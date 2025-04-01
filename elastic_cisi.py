import os
import re
import nltk
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from nltk.corpus import stopwords
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from nltk.tokenize import word_tokenize
import string

nltk.download('punkt')
nltk.download('stopwords')

stop_words = set(stopwords.words('english'))

# Flask App Setup
app = Flask(__name__)
CORS(app)

# Elastic Cloud Configuration
INDEX_NAME = "cisi_data"

# Connect to Elastic Cloud
es = Elasticsearch(
    hosts=["https://my-elasticsearch-project-ec56ca.es.us-east-1.aws.elastic.cloud:443"],
    api_key="ZHVhVVdKVUJmWEg5ajJ6UC1oYzk6M2pGdk5zVVVtWmxoMjAwdHlHZzc2dw=="
)

def preprocess_query(text):
    tokens = word_tokenize(text.lower())
    tokens = [t for t in tokens if t not in stop_words and t not in string.punctuation]
    return ' '.join(tokens)



# Load the dataset (Modify the path to your dataset location)
DOCUMENTS_FILE = "CISI.ALL"
QUERIES_FILE = "CISI.QRY"
RELEVANCE_FILE = "CISI.REL"

def read_cisi_file(filename):
    """Reads a CISI dataset file and returns structured data with titles, authors, text, and citations."""
    data = {}
    citations = {}
    with open(filename, "r", encoding="utf-8") as file:
        content = file.read()

    entries = re.split(r'\.I \d+', content)[1:]
    for i, entry in enumerate(entries):
        entry = entry.strip()
        doc_id = i + 1

        text_match = re.search(r'\.W\s+(.*?)(?:\.X|$)', entry, re.DOTALL)
        title_match = re.search(r'\.T\s+(.*?)(?:\.A|$)', entry, re.DOTALL)
        author_match = re.search(r'\.A\s+(.*?)(?:\.W|$)', entry, re.DOTALL)
        citation_match = re.search(r'\.X\s+(.*)', entry, re.DOTALL)

        text = text_match.group(1).strip() if text_match else ""
        title = title_match.group(1).strip() if title_match else ""
        author = author_match.group(1).strip() if author_match else ""

        data[doc_id] = {
            "doc_id": doc_id,
            "text": text,
            "title": title,
            "author": author
        }

        citations[doc_id] = []
        if citation_match:
            cited_lines = citation_match.group(1).strip().split("\n")
            for line in cited_lines:
                parts = line.split()
                if parts:
                    cited_doc_id = int(parts[0])
                    citations[doc_id].append(cited_doc_id)

    return data, citations

def index_documents_to_elasticsearch(documents):
    """Indexes CISI documents into Elasticsearch using bulk API."""
    actions = [
        {
            "_index": INDEX_NAME,
            "_id": doc["doc_id"],
            "_source": {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "author": doc["author"],
                "text": doc["text"]
            }
        }
        for doc in documents.values()
    ]

    success, _ = bulk(es, actions)
    print(f"Indexed {success} documents into Elasticsearch.")

# Load CISI documents and cross-references
documents, citations = read_cisi_file(DOCUMENTS_FILE)

index_documents_to_elasticsearch(documents)

# Function to Search Elasticsearch
def search_cisi(query, top_n=5):
    """Performs a multi-field search with fuzzy matching, autocomplete, and highlights."""
    response = es.search(index=INDEX_NAME, body={
        "query": {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^2", "text", "author"],
                            "fuzziness": "AUTO",           # fuzzy matching
                            "type": "best_fields"
                        }
                    },
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^2", "text"],
                            "type": "phrase_prefix"         # autocomplete-like behavior
                        }
                    }
                ]
            }
        },
        "highlight": {
            "fields": {
                "title": {},
                "text": {},
                "author": {}
            },
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"]
        },
        "size": top_n
    })

    results = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        highlights = hit.get("highlight", {})
        results.append({
            "doc_id": source["doc_id"],
            "score": hit["_score"],
            "title": source["title"],
            "author": source["author"],
            "text": source["text"],
            "highlights": {
                "title": highlights.get("title", []),
                "author": highlights.get("author", []),
                "text": highlights.get("text", [])
            }
        })

    return results

def evaluate_cisi(query, top_n=5):
    query = preprocess_query(query)
    response = es.search(index=INDEX_NAME, body={
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title^5", "text^2", "author"],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        },
        "size": top_n
    })  

    results = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        results.append({
            "doc_id": source["doc_id"],
            "score": hit["_score"],
            "title": source["title"],
            "author": source["author"],
            "text": source["text"]
        })

    return results

# Flask API Endpoint for Searching CISI Data
@app.route("/search", methods=["GET"])
def search_api():
    query = request.args.get("q", "")
    top_n = request.args.get("size", default=5, type=int)

    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    results = search_cisi(query, top_n=top_n) 
    return jsonify({"query": query, "results": results})

@app.route("/evaluate", methods=["GET"])
def search_simple_api():
    query = request.args.get("q", "")
    top_n = request.args.get("size", default=5, type=int)
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    results = evaluate_cisi(query, top_n=top_n)
    return jsonify({"query": query, "results": results})

# === Run Flask App ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

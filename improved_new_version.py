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
from sklearn.metrics import precision_score, recall_score, average_precision_score
import math


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

# Fine-Tuning BM25
def create_index_with_bm25(index_name, k1 = 1.2, b = 0.3):
    
    # Remove previous indexing
    if es.indices.exists(index = index_name):
        es.indices.delete(index = index_name)

    settings = {
        "settings": {
            "similarity": {
                "my_bm25": {
                    "type": "BM25",
                    "k1": k1,
                    "b": b
                }
            }
        },
        "mappings": {
            "properties": {
                "title": {"type": "text", "similarity": "my_bm25"},
                "text": {"type": "text", "similarity": "my_bm25"},
                "author": {"type": "text", "similarity": "my_bm25"}
            }
        }
    }

    es.indices.create(index = index_name, body = settings)
    print(f"Created index '{index_name}' with BM25(k1 = {k1}, b = {b})")


# Customize BM25 setting and perform indexing
create_index_with_bm25(INDEX_NAME, k1 = 1.2, b = 0.3) # Balanced precision and recall, better ranking
index_documents_to_elasticsearch(documents)

# Function to Search Elasticsearch
def search_cisi(query, top_k=5):
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
        "size": top_k
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

def evaluate_cisi(query, top_k=10):
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
        "size": top_k
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

def read_queries(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Extract query texts
    entries = re.findall(r'\.I\s+(\d+)\s*\.W\s+(.*?)(?=(?:\.I\s+\d+)|\Z)', content, re.DOTALL)
    
    queries = {}
    for qid_str, text in entries:
        # Must be (int) to match with ground truth format
        qid = int(qid_str.strip())
        queries[qid] = text.strip()
    return queries


def read_relevance(file_path):
    relevance = {}
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            # Extract records from relevance file
            parts = line.strip().split()
            # Two first columns are what we need
            if len(parts) >= 2:
                try:
                    qid = int(parts[0])
                    doc_id = int(parts[1])
                    # Add new records to the relevance dictionary
                    if qid not in relevance:
                        relevance[qid] = set()
                    relevance[qid].add(doc_id)
                # If data was buggy (no info for a record), raise error
                except ValueError:
                    print(f"Line {i} has invalid format: {line.strip()}")
            # Query or relevant document ID or both are missing
            else:
                print(f"Line {i} has not enough parts: {line.strip()}")
    return relevance


# DCG calculator
def dcg(relevances):
    return sum([
        (relevant_docs / math.log2(qid + 2))  # index + 2 because log2(1) = 0
        for qid, relevant_docs in enumerate(relevances)
    ])

# NDCG calculator
def ndcg(relevances, ideal_relevances):
    return dcg(relevances) / dcg(ideal_relevances) if dcg(ideal_relevances) != 0 else 0


# Conduct evaluation on all queries
def evaluate_all_queries(queries, relevance, top_k = 10):
    results = []
    for qid, query_text in queries.items():
        # Take one query at a time
        query = preprocess_query(query_text)
        # Search for query
        res = es.search(index = INDEX_NAME, size = top_k, body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "text", "author"],
                    "fuzziness": "AUTO"
                }
            }
        })
        # Take the hits (search result)
        retrieved_ids = [int(hit["_id"]) for hit in res["hits"]["hits"]]
        # And relevant document IDs for the query
        relevant_ids = relevance.get(qid, set())

        # Create ground truth list
        y_true = [1 if doc_id in relevant_ids else 0 for doc_id in retrieved_ids]
        # Create prediction list (to compare matches with ground truth)
        y_pred = [1] * len(retrieved_ids)
        # Score results based on their rank (Used for MAP)
        y_scores = [hit["_score"] for hit in res["hits"]["hits"]]

        # Sorted relevant documents (to calculate NDCG, we need the ideal ranking)
        sorted_relevant_docs = sorted(y_true, reverse = True)

        precision = precision_score(y_true, y_pred, zero_division = 0)
        recall = recall_score(y_true, y_pred, zero_division = 0)
        map_score = average_precision_score(y_true, y_scores) if relevant_ids else 0.0
        ndcg_score = ndcg(y_true, sorted_relevant_docs)

        results.append({
            "query_id": qid,
            f"precision@{top_k}": precision,
            f"recall@{top_k}": recall,
            "map": round(map_score, 4),
            f"ndcg@{top_k}": round(ndcg_score, 4)
        })

    return results


# Flask API Endpoint for Searching CISI Data
@app.route("/search", methods=["GET"])
def search_api():
    query = request.args.get("q", "")
    top_k = request.args.get("size", default=5, type=int)

    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    results = search_cisi(query, top_k=top_k) 
    return jsonify({"query": query, "results": results})

@app.route("/evaluate", methods=["GET"])
def search_simple_api():
    query = request.args.get("q", "")
    top_k = request.args.get("size", default=5, type=int)
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    results = evaluate_cisi(query, top_k=top_k)
    return jsonify({"query": query, "results": results})

@app.route("/evaluate_all", methods = ["GET"])
def evaluate_all_api():
    top_k = request.args.get("size", default = 10, type = int)

    queries = read_queries(QUERIES_FILE)
    relevance = read_relevance(RELEVANCE_FILE)
    evaluation = evaluate_all_queries(queries, relevance, top_k=top_k)

    avg_precision = np.mean([r[f"precision@{top_k}"] for r in evaluation])
    avg_recall = np.mean([r[f"recall@{top_k}"] for r in evaluation])
    avg_map = np.mean([r["map"] for r in evaluation])
    avg_ndcg = np.mean([r[f"ndcg@{top_k}"] for r in evaluation])

    return jsonify({
        "Top k: ": top_k,
        f"Average Precision @{top_k}": round(avg_precision, 4),
        f"Average Recall @{top_k}": round(avg_recall, 4),
        "Mean Average Precision": round(avg_map, 4),
        f"Average NDCG @{top_k}": round(avg_ndcg, 4),
        "Per Query Scores: ": evaluation
    })


# === Run Flask App ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
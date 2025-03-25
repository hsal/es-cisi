import os
import pandas as pd
import numpy as np
import re
import nltk
from flask import Flask, request, jsonify
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Ensure necessary NLTK resources are available
nltk.download('stopwords')
nltk.download('punkt')

# Flask App Setup
app = Flask(__name__)

# Elastic Cloud Configuration
INDEX_NAME = "cisi_data"

# Connect to Elastic Cloud
es = Elasticsearch("https://my-elasticsearch-project-ec56ca.es.us-east-1.aws.elastic.cloud:443",
    api_key="ZHVhVVdKVUJmWEg5ajJ6UC1oYzk6M2pGdk5zVVVtWmxoMjAwdHlHZzc2dw=="
)

# Load the dataset (Modify the path to your dataset location)
DOCUMENTS_FILE = "CISI.ALL"
QUERIES_FILE = "CISI.QRY"
RELEVANCE_FILE = "CISI.REL"


# Function to read CISI dataset files and extract cross-references
def read_cisi_file(filename):
    """Reads a CISI dataset file and returns a dictionary mapping IDs to text and citations."""
    data = {}
    citations = {}
    with open(filename, "r", encoding="utf-8") as file:
        content = file.read()
    
    entries = re.split(r'\.I \d+', content)[1:]
    for i, entry in enumerate(entries):
        entry = entry.strip()
        doc_id = i + 1  # Assign an index-based ID
        
        text_match = re.search(r'\.W\s+(.*?)(?:\.X|$)', entry, re.DOTALL)
        citation_match = re.search(r'\.X\s+(.*)', entry, re.DOTALL)
        
        text = text_match.group(1).strip() if text_match else ""
        data[doc_id] = text
        
        # Process citations
        citations[doc_id] = []
        if citation_match:
            cited_docs = citation_match.group(1).strip().split("\n")
            for line in cited_docs:
                parts = line.split()
                if parts:
                    cited_docs = int(parts[0])
                    citations[doc_id].append(cited_docs)
    
    return data, citations

# Load CISI documents and cross-references
documents, citations = read_cisi_file(DOCUMENTS_FILE)

# Function to Search Elasticsearch
def search_cisi(query, top_n=5):
    """Searches CISI dataset in Elasticsearch Cloud."""
    response = es.search(index=INDEX_NAME, body={
        "query": {
            "match": {
                "text": query
            }
        },
        "size": top_n
    })
    
    results = [{"doc_id": hit["_source"]["doc_id"], "score": hit["_score"], "text": hit["_source"]["text"]} for hit in response["hits"]["hits"]]
    return results

# Flask API Endpoint for Searching CISI Data
@app.route("/search", methods=["GET"])
def search_api():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400
    
    results = search_cisi(query)
    return jsonify({"query": query, "results": results})

# Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

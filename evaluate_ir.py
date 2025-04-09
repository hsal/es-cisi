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
        res = es.search(index = INDEX_NAME, body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "text", "author"],
                    "fuzziness": "AUTO"
                }
            },
            "size": top_k            
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


def evaluate_ir():
    top_k = 10

    queries = read_queries(QUERIES_FILE)
    relevance = read_relevance(RELEVANCE_FILE)
    evaluation = evaluate_all_queries(queries, relevance, top_k=top_k)

    avg_precision = np.mean([r[f"precision@{top_k}"] for r in evaluation])
    avg_recall = np.mean([r[f"recall@{top_k}"] for r in evaluation])
    avg_map = np.mean([r["map"] for r in evaluation])
    avg_ndcg = np.mean([r[f"ndcg@{top_k}"] for r in evaluation])

    
    print(f"Top k: {top_k}")
    print(f"Average Precision @{top_k}: {avg_precision:.4f}")
    print(f"Average Recall @{top_k}: {avg_recall:.4f}")
    print(f"Average NDCG @{top_k}: {avg_ndcg:.4f}")
    print(f"Mean Average Precision: {avg_map:.4f}")

evaluate_ir()
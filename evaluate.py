import re
import requests
import numpy as np

# === Load Queries from CISI.QRY ===
def load_queries(qry_file):
    queries = {}
    with open(qry_file, "r", encoding="utf-8") as f:
        content = f.read()
    entries = re.split(r'\.I\s+(\d+)', content)[1:]
    for i in range(0, len(entries), 2):
        qid = int(entries[i])
        text_match = re.search(r'\.W\s+(.*)', entries[i+1], re.DOTALL)
        if text_match:
            queries[qid] = text_match.group(1).strip()
    return queries

# === Load Relevance Judgments from CISI.REL ===
def load_relevance_judgments(rel_file):
    relevance = {}
    with open(rel_file, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3:
                try:
                    qid = int(parts[0])
                    doc_id = int(parts[1])
                    relevance.setdefault(qid, set()).add(doc_id)
                except ValueError:
                    print(f"Skipping malformed line: {line.strip()}")
    return relevance

def recall_at_k(retrieved, relevant, k):
    retrieved_k = retrieved[:k]
    return len([doc for doc in retrieved_k if doc in relevant]) / len(relevant) if relevant else 0.0

def f1_at_k(precision, recall):
    return 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

def average_precision(retrieved, relevant, k):
    hits = 0
    sum_precisions = 0
    for i in range(min(k, len(retrieved))):
        if retrieved[i] in relevant:
            hits += 1
            sum_precisions += hits / (i + 1)
    return sum_precisions / len(relevant) if relevant else 0.0

def reciprocal_rank(retrieved, relevant):
    for i, doc in enumerate(retrieved):
        if doc in relevant:
            return 1 / (i + 1)
    return 0.0

def precision_at_k(retrieved, relevant, k):
    retrieved_k = retrieved[:k]
    return len([doc for doc in retrieved_k if doc in relevant]) / k

# === Evaluate using API ===
def evaluate_api(base_url, queries, relevance):
    precisions = []
    recalls = []
    f1_scores = []
    map_scores = []
    mrr_scores = []
    precisions = []
    total = len(queries)

    print(f"Starting evaluation on {total} queries...\n")

    for idx, qid in enumerate(queries.keys(), 1):
        query = queries[qid]
        endpoint = base_url + "/evaluate"
        mode = "Text"
        print(f"▶ Query {idx}/{total} | QID: {qid} | Mode: {mode}")
        print(f"   Query: {query[:80]}...")

        try:
            response = requests.get(endpoint, params={"q": query, "size": 100}, timeout=10)
            response.raise_for_status()
            data = response.json()
            retrieved_ids = [res["doc_id"] for res in data["results"]]
            relevant_ids = relevance.get(qid, set())
                        
            k = len(relevant_ids)
            if k == 0:
                print(f"   ⏩ Skipping QID {qid} (no relevance judgments)\n")
                continue

            precision = precision_at_k(retrieved_ids, relevant_ids, k)
            precisions.append(precision)
            
            recall = recall_at_k(retrieved_ids, relevant_ids, k)
            recalls.append(recall)
            
            f1 = f1_at_k(precision, recall)
            f1_scores.append(f1)
            
            ap = average_precision(retrieved_ids, relevant_ids, k)
            map_scores.append(ap)
            
            rr = reciprocal_rank(retrieved_ids, relevant_ids)
            mrr_scores.append(rr)

            print(f"   Retrieved IDs : {retrieved_ids}")
            print(f"   Relevant IDs  : {sorted(relevant_ids)}")
            print(f"   Precision@{k} : {precision:.4f}")
            print(f"   Recall@{k}    : {recall:.4f}")
            print(f"   F1@{k}        : {f1:.4f}")
            print(f"   AvgPrec@{k}   : {ap:.4f}")
            print(f"   ReciprocalRank: {rr:.4f}\n")
            

        except Exception as e:
            print(f"   ❌ Error retrieving results: {e}\n")
            precisions.append(0.0)
            
    mean_precision = np.mean(precisions)
    mean_recall = np.mean(recalls)
    mean_f1 = np.mean(f1_scores)
    mean_map = np.mean(map_scores)
    mean_mrr = np.mean(mrr_scores)

    print("Evaluation Complete")
    print(f"Mean Precision@{k}: {mean_precision:.4f}")
    print(f"Mean Recall@{k}   : {mean_recall:.4f}")
    print(f"Mean F1@{k}       : {mean_f1:.4f}")
    print(f"MAP@{k}           : {mean_map:.4f}")
    print(f"MRR               : {mean_mrr:.4f}")
    

# === Run Evaluation ===
if __name__ == "__main__":
    BASE_URL = "https://www.qmulsearch.com/"  # Base API URL
    QRY_FILE = "CISI.QRY"
    REL_FILE = "CISI.REL"

    queries = load_queries(QRY_FILE)
    relevance = load_relevance_judgments(REL_FILE)

    
    evaluate_api(BASE_URL, queries, relevance)

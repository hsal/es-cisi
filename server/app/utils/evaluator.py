import numpy as np
from sklearn.metrics import precision_score, recall_score, average_precision_score
from app.utils.preprocess import preprocess_query
from app.config import Config
from app.utils.metrics import ndcg
from app.extensions.es import es


def evaluate_all_queries(queries, relevance, top_k=10):
    results = []
    for qid, text in queries.items():
        query = preprocess_query(text)
        response = es.search(
            index=Config.INDEX_NAME,
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "text", "author"],
                        "fuzziness": "AUTO",
                    }
                },
                "size": top_k,
            },
        )

        hits = response["hits"]["hits"]
        retrieved_ids = [int(hit["_id"]) for hit in hits]
        relevant_ids = relevance.get(qid, set())
        y_true = [1 if doc_id in relevant_ids else 0 for doc_id in retrieved_ids]
        y_pred = [1] * len(retrieved_ids)
        y_scores = [hit["_score"] for hit in hits]
        sorted_relevant_docs = sorted(y_true, reverse=True)

        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        map_score = average_precision_score(y_true, y_scores) if relevant_ids else 0.0
        ndcg_score = ndcg(y_true, sorted_relevant_docs)

        results.append(
            {
                "query_id": qid,
                f"precision@{top_k}": precision,
                f"recall@{top_k}": recall,
                "map": round(map_score, 4),
                f"ndcg@{top_k}": round(ndcg_score, 4),
            }
        )

    return results


def summarize_metrics(results, top_k):
    avg_precision = np.mean([r[f"precision@{top_k}"] for r in results])
    avg_recall = np.mean([r[f"recall@{top_k}"] for r in results])
    avg_map = np.mean([r["map"] for r in results])
    avg_ndcg = np.mean([r[f"ndcg@{top_k}"] for r in results])
    return avg_precision, avg_recall, avg_map, avg_ndcg

from app.utils.loader import read_queries, read_relevance
from app.utils.evaluator import evaluate_all_queries, summarize_metrics

QUERIES_FILE = "data/CISI.QRY"
RELEVANCE_FILE = "data/CISI.REL"


TOP_K = 10


def evaluate_ir():
    queries = read_queries(QUERIES_FILE)
    relevance = read_relevance(RELEVANCE_FILE)
    results = evaluate_all_queries(queries, relevance, top_k=TOP_K)
    avg_p, avg_r, avg_map, avg_ndcg = summarize_metrics(results, TOP_K)

    print(f"Top k: {TOP_K}")
    print(f"Average Precision @{TOP_K}: {avg_p:.4f}")
    print(f"Average Recall @{TOP_K}: {avg_r:.4f}")
    print(f"Average NDCG @{TOP_K}: {avg_ndcg:.4f}")
    print(f"Mean Average Precision: {avg_map:.4f}")


if __name__ == "__main__":
    evaluate_ir()

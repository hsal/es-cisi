import math


def dcg(relevances):
    return sum(rel / math.log2(idx + 2) for idx, rel in enumerate(relevances))


def ndcg(relevances, ideal_relevances):
    return dcg(relevances) / dcg(ideal_relevances) if dcg(ideal_relevances) else 0

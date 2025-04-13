from app.config import Config
from app.extensions.es import es
from app.utils.preprocess import preprocess_query


def search_cisi(query, top_n=5):
    query = preprocess_query(query)
    response = es.search(
        index=Config.INDEX_NAME,
        body={
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "text", "author"],
                                "fuzziness": "AUTO",
                                "type": "best_fields",
                            }
                        },
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "text"],
                                "type": "phrase_prefix",
                            }
                        },
                    ]
                }
            },
            "highlight": {
                "fields": {"title": {}, "text": {}, "author": {}},
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
            },
            "size": top_n,
        },
    )

    results = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        highlights = hit.get("highlight", {})
        results.append(
            {
                "doc_id": source["doc_id"],
                "score": hit["_score"],
                "title": source["title"],
                "author": source["author"],
                "text": source["text"],
                "highlights": {
                    "title": highlights.get("title", []),
                    "author": highlights.get("author", []),
                    "text": highlights.get("text", []),
                },
            }
        )

    return results


def autocomplete(query, top_n=5):
    response = es.search(
        index=Config.INDEX_NAME,
        body={
            "size": top_n,
            "query": {
                "bool": {
                    "should": [
                        {"match_phrase_prefix": {"title": {"query": query}}},
                        {"match_phrase_prefix": {"text": {"query": query}}},
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "title": {"fragment_size": 50, "number_of_fragments": 1},
                    "text": {"fragment_size": 80, "number_of_fragments": 1},
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
            },
        },
    )

    suggestions = []
    for hit in response["hits"]["hits"]:
        highlight = hit.get("highlight", {})
        snippet = highlight.get("title", highlight.get("text", [""]))[0]
        suggestions.append(
            {
                "doc_id": hit["_source"]["doc_id"],
                "title": hit["_source"]["title"],
                "snippet": snippet,
            }
        )

    return suggestions

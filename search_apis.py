import nltk
from flask import Flask, request, jsonify
from flask_cors import CORS
from nltk.corpus import stopwords
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from nltk.tokenize import word_tokenize
import string

nltk.data.path.append("./nltk_data")

nltk.download('punkt')
nltk.download('stopwords')

stop_words = set(stopwords.words('english'))

# Flask App Setup
app = Flask(__name__)
CORS(app)

# Elastic Cloud Configuration
INDEX_NAME = "cisi_data_p"

# Connect to Elastic Cloud
es = Elasticsearch(
    hosts=["https://my-elasticsearch-project-ec56ca.es.us-east-1.aws.elastic.cloud:443"],
    api_key="ZHVhVVdKVUJmWEg5ajJ6UC1oYzk6M2pGdk5zVVVtWmxoMjAwdHlHZzc2dw=="
)

def preprocess_query(text):
    tokens = word_tokenize(text.lower())
    tokens = [t for t in tokens if t not in stop_words and t not in string.punctuation]
    return ' '.join(tokens)

# Function to Search Elasticsearch
def search_cisi(query, top_n=5):    
    query = preprocess_query(query)
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

# Flask API Endpoint for Searching CISI Data
@app.route("/search", methods=["GET"])
def search_api():
    query = request.args.get("q", "")
    top_n = request.args.get("size", default=5, type=int)

    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    results = search_cisi(query, top_n=top_n) 
    return jsonify({"query": query, "results": results})

@app.route("/autocomplete", methods=["GET"])
def autocomplete_combined_text_title():
    prefix = request.args.get("q", "")
    top_n = request.args.get("size", default=5, type=int)

    if not prefix:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    response = es.search(index=INDEX_NAME, body={
        "size": top_n,
        "query": {
            "bool": {
                "should": [
                    {"match_phrase_prefix": {"title": {"query": prefix}}},
                    {"match_phrase_prefix": {"text": {"query": prefix}}}
                ]
            }
        },
        "highlight": {
            "fields": {
                "title": {
                    "fragment_size": 50,
                    "number_of_fragments": 1
                },
                "text": {
                    "fragment_size": 80,
                    "number_of_fragments": 1
                }
            },
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"]
        }
    })

    suggestions = []
    for hit in response["hits"]["hits"]:
        highlight = hit.get("highlight", {})
        snippet = highlight.get("title", highlight.get("text", [""]))[0]

        suggestions.append({
            "doc_id": hit["_source"]["doc_id"],
            "title": hit["_source"]["title"],
            "snippet": snippet
        })

    return jsonify({
        "query": prefix,
        "suggestions": suggestions
    })
    
# === Run Flask App ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

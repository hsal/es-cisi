from flask import Blueprint, request, jsonify
from app.services.search import search_cisi, autocomplete

search_bp = Blueprint("search", __name__)


@search_bp.route("/", methods=["GET"])
def search_api():
    query = request.args.get("q", "")
    top_n = request.args.get("size", default=5, type=int)
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    results = search_cisi(query, top_n=top_n)
    return jsonify({"query": query, "results": results})


@search_bp.route("/autocomplete", methods=["GET"])
def autocomplete_api():
    query = request.args.get("q", "")
    top_n = request.args.get("size", default=5, type=int)
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    results = autocomplete(query, top_n=top_n)
    return jsonify({"query": query, "suggestions": results})

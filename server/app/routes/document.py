from flask import Blueprint, jsonify
from app.services.document import get_document

document_bp = Blueprint("document", __name__)


@document_bp.route("/<doc_id>", methods=["GET"])
def get_doc(doc_id):
    try:
        doc = get_document(doc_id)
        if doc:
            return jsonify(doc), 200
        return jsonify({"error": "Document not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

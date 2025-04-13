from flask import Flask
from flask_cors import CORS
from app.routes.search import search_bp
from app.routes.document import document_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(search_bp, url_prefix="/api/search")
    app.register_blueprint(document_bp, url_prefix="/api/document")

    return app

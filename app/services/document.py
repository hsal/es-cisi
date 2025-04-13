from app.extensions.es import es
from app.config import Config


def get_document(doc_id):
    try:
        response = es.get(index=Config.INDEX_NAME, id=doc_id)
        if response["found"]:
            return response["_source"]
        return None
    except Exception as e:
        raise e

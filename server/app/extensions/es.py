from elasticsearch import Elasticsearch
from app.config import Config

es = Elasticsearch(
    hosts=[Config.ES_HOST],
    api_key=Config.ES_API_KEY,
)

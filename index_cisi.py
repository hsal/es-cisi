import re
from nltk.corpus import stopwords
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from nltk.tokenize import word_tokenize
import string

stop_words = set(stopwords.words("english"))

# Elastic Cloud Configuration
INDEX_NAME = "cisi_data_p"

# Connect to Elastic Cloud
es = Elasticsearch(
    hosts=[
        "https://my-elasticsearch-project-ec56ca.es.us-east-1.aws.elastic.cloud:443"
    ],
    api_key="ZHVhVVdKVUJmWEg5ajJ6UC1oYzk6M2pGdk5zVVVtWmxoMjAwdHlHZzc2dw==",
)


def preprocess(text):
    tokens = word_tokenize(text.lower())
    tokens = [t for t in tokens if t not in stop_words and t not in string.punctuation]
    return " ".join(tokens)


# Load the dataset (Modify the path to your dataset location)
DOCUMENTS_FILE = "CISI.ALL"


def read_cisi_file(filename):
    """Reads a CISI dataset file and returns structured data with titles, authors, text, and citations."""
    data = {}
    citations = {}
    with open(filename, "r", encoding="utf-8") as file:
        content = file.read()

    entries = re.split(r"\.I \d+", content)[1:]
    for i, entry in enumerate(entries):
        entry = entry.strip()
        doc_id = i + 1

        text_match = re.search(r"\.W\s+(.*?)(?:\.X|$)", entry, re.DOTALL)
        title_match = re.search(r"\.T\s+(.*?)(?:\.A|$)", entry, re.DOTALL)
        author_match = re.search(r"\.A\s+(.*?)(?:\.W|$)", entry, re.DOTALL)
        citation_match = re.search(r"\.X\s+(.*)", entry, re.DOTALL)

        text = text_match.group(1).strip() if text_match else ""
        title = title_match.group(1).strip() if title_match else ""
        author = author_match.group(1).strip() if author_match else ""

        data[doc_id] = {
            "doc_id": doc_id,
            "text": text,
            "preprocessed_text": preprocess(text),
            "title": title,
            "author": author,
        }

        citations[doc_id] = []
        if citation_match:
            cited_lines = citation_match.group(1).strip().split("\n")
            for line in cited_lines:
                parts = line.split()
                if parts:
                    cited_doc_id = int(parts[0])
                    citations[doc_id].append(cited_doc_id)

    return data, citations


def index_documents_to_elasticsearch(documents):
    """Indexes CISI documents into Elasticsearch using bulk API."""
    actions = [
        {
            "_index": INDEX_NAME,
            "_id": doc["doc_id"],
            "_source": {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "author": doc["author"],
                "text": doc["text"],
                "preprocessed_text": doc["preprocessed_text"],
            },
        }
        for doc in documents.values()
    ]

    success, _ = bulk(es, actions)
    print(f"Indexed {success} documents into Elasticsearch.")


# Load CISI documents and cross-references
documents, citations = read_cisi_file(DOCUMENTS_FILE)

index_documents_to_elasticsearch(documents)

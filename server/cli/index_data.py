import re
from elasticsearch.helpers import bulk
from app.extensions.es import es
from app.config import Config
from app.utils.preprocess import preprocess_query


# Load the dataset (Modify the path to your dataset location)
DOCUMENTS_FILE = "data/CISI.ALL"


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
            "preprocessed_text": preprocess_query(text),
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
            "_index": Config.INDEX_NAME,
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

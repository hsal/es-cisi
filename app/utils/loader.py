import re


def read_queries(file_path):
    with open(file_path, "r") as f:
        content = f.read()
    entries = re.findall(
        r"\.I\s+(\d+)\s*\.W\s+(.*?)(?=(?:\.I\s+\d+)|\Z)", content, re.DOTALL
    )
    return {int(qid): text.strip() for qid, text in entries}


def read_relevance(file_path):
    relevance = {}
    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    qid = int(parts[0])
                    doc_id = int(parts[1])
                    relevance.setdefault(qid, set()).add(doc_id)
                except ValueError:
                    continue
    return relevance

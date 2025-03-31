import os
import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ensure necessary NLTK resources are available
nltk.download('stopwords')
nltk.download('punkt')

# Load the dataset (Modify the path to your dataset location)
DOCUMENTS_FILE = "CISI.ALL"
QUERIES_FILE = "CISI.QRY"
RELEVANCE_FILE = "CISI.REL"

# Function to read CISI dataset files
def read_cisi_file(filename):
    """Reads a CISI dataset file and returns a dictionary mapping IDs to text."""
    data = {}
    with open(filename, "r", encoding="utf-8") as file:
        content = file.read()
    
    # CISI documents have an identifier like .I 123
    entries = re.split(r'\.I \d+', content)[1:]
    for i, entry in enumerate(entries):
        entry = entry.strip()
        data[i + 1] = entry  # Assign an index-based ID
    return data

# Load CISI documents and queries
documents = read_cisi_file(DOCUMENTS_FILE)
queries = read_cisi_file(QUERIES_FILE)

# Convert to DataFrames
doc_df = pd.DataFrame(list(documents.items()), columns=["DocID", "Text"])
query_df = pd.DataFrame(list(queries.items()), columns=["QueryID", "Text"])

# Text Preprocessing
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)  # Remove special characters
    words = nltk.word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    words = [w for w in words if w not in stop_words]
    stemmer = PorterStemmer()
    words = [stemmer.stem(w) for w in words]
    return " ".join(words)

# Apply preprocessing
doc_df["ProcessedText"] = doc_df["Text"].apply(preprocess_text)
query_df["ProcessedText"] = query_df["Text"].apply(preprocess_text)

# TF-IDF Vectorization
vectorizer = TfidfVectorizer()
doc_matrix = vectorizer.fit_transform(doc_df["ProcessedText"])
query_matrix = vectorizer.transform(query_df["ProcessedText"])

# Compute Cosine Similarity between queries and documents
cosine_sim = cosine_similarity(query_matrix, doc_matrix)

# Retrieve Top Documents for Each Query
num_results = 5
retrieval_results = {}
for i, query_id in enumerate(query_df["QueryID"]):
    sorted_indices = np.argsort(-cosine_sim[i])  # Sort by descending similarity
    top_docs = [(doc_df.iloc[idx]["DocID"], cosine_sim[i][idx]) for idx in sorted_indices[:num_results]]
    retrieval_results[query_id] = top_docs

# Display Sample Results with Query Text
for query_id, results in list(retrieval_results.items())[:3]:  # Show first 3 queries
    query_text = query_df.loc[query_df["QueryID"] == query_id, "Text"].values[0]
    print(f"Query {query_id}: {query_text}")
    for doc_id, score in results:
        print(f"   Document {doc_id} - Similarity Score: {score:.4f}")
    print("\n")

import nltk
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.data.path.append("./nltk_data")
nltk.download("punkt")
nltk.download("stopwords")

stop_words = set(stopwords.words("english"))


def preprocess_query(text):
    tokens = word_tokenize(text.lower())
    tokens = [t for t in tokens if t not in stop_words and t not in string.punctuation]
    return " ".join(tokens)

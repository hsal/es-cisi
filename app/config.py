import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ES_HOST = os.getenv("ES_HOST")
    ES_API_KEY = os.getenv("ES_API_KEY")
    INDEX_NAME = "cisi_data_p"

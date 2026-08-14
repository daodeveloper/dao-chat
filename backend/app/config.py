import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FAISS_INDEX_PATH = os.path.join(BASE_DIR, "data", "faiss_index")
    DOCUMENTS_PATH = os.path.join(BASE_DIR, "data")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
    SIGNUP_URL = os.getenv("SIGNUP_URL", "https://id.daoproptech.com")
    WATI_SHARED_SECRET = os.getenv("WATI_SHARED_SECRET", "")
    WEB_SEARCH_ENABLED = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

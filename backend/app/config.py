import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FAISS_INDEX_PATH = os.path.join(BASE_DIR, "data", "faiss_index")
    DOCUMENTS_PATH = os.path.join(BASE_DIR, "data")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
    SIGNUP_URL = os.getenv("SIGNUP_URL", "https://id.daoproptech.com")
    WATI_SHARED_SECRET = os.getenv("WATI_SHARED_SECRET", "")
    WEB_SEARCH_ENABLED = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google")               # google | openai
    EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", "openai")  # openai | google
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    USE_DB = os.getenv("USE_DB", "false").lower() == "true"   # false = run without any database

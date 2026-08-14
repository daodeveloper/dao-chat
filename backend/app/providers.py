"""LLM and embeddings factory. Switch providers with env vars (see config.py).
Default: Gemini for chat (free tier), OpenAI for embeddings (keeps the existing index).
Set EMBEDDINGS_PROVIDER=google to go fully free (then rebuild the index)."""
from .config import Config


def get_embeddings():
    if getattr(Config, "EMBEDDINGS_PROVIDER", "openai").lower() == "google":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings()


def get_chat_llm(streaming: bool = False):
    provider = getattr(Config, "LLM_PROVIDER", "google").lower()
    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=getattr(Config, "GEMINI_MODEL", "gemini-2.0-flash"),
            temperature=0,
            max_output_tokens=8192,
        )
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        temperature=0,
        model_name=getattr(Config, "MODEL_NAME", "gpt-4o-mini"),
        streaming=streaming,
        max_tokens=16000,
        request_timeout=60,
    )

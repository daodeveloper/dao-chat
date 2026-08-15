"""LLM and embeddings for the bot. Gemini only.

Model names come from config (Config.GEMINI_MODEL / Config.EMBEDDINGS_MODEL) so they
can be swapped with an env var when Google retires a model, without touching code.
"""
from .config import Config


def get_embeddings():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    return GoogleGenerativeAIEmbeddings(
        model=getattr(Config, "EMBEDDINGS_MODEL", "models/gemini-embedding-001")
    )


def get_chat_llm(streaming: bool = False):
    # streaming is handled by calling .astream(); no constructor flag needed for Gemini.
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=getattr(Config, "GEMINI_MODEL", "gemini-3.5-flash"),
        temperature=0,
        max_output_tokens=8192,
    )

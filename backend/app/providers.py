"""LLM and embeddings for the bot.

Chat  = Gemini (Google API), model name from config so it can be swapped by env.
Embeddings = LOCAL via fastembed, called directly (the LangChain FastEmbed wrapper has a
version-mismatch bug where its internal model stays None). No API, no quota, no cost.
"""
from typing import List
from langchain_core.embeddings import Embeddings
from .config import Config

_EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def _to_list(vec) -> List[float]:
    # fastembed yields numpy arrays; make them plain float lists for FAISS/JSON.
    if hasattr(vec, "tolist"):
        return vec.tolist()
    return [float(x) for x in vec]


class LocalFastEmbed(Embeddings):
    """Minimal LangChain Embeddings backed directly by fastembed."""

    def __init__(self, model_name: str = _EMBED_MODEL):
        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [_to_list(v) for v in self._model.embed(list(texts))]

    def embed_query(self, text: str) -> List[float]:
        return _to_list(next(iter(self._model.embed([text]))))


def get_embeddings():
    # Local, in-container embeddings. No API calls, no quota, no cost.
    return LocalFastEmbed()


def get_chat_llm(streaming: bool = False):
    # streaming is handled via .astream(); no constructor flag needed for Gemini.
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=getattr(Config, "GEMINI_MODEL", "gemini-2.5-flash"),
        temperature=0,
        max_output_tokens=8192,
    )

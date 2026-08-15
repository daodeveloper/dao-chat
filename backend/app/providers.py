"""LLM and embeddings for the bot.

Chat = Gemini (Google API). Embeddings = LOCAL (fastembed), so building and querying the
knowledge index costs nothing and has no rate limit. Only the chat model uses Gemini quota.
The chat model name comes from config so it can be swapped by env when Google retires one.
"""
from .config import Config


def get_embeddings():
    # Local, in-container embeddings. No API calls, no quota, no cost.
    from langchain_community.embeddings import FastEmbedEmbeddings
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")


def get_chat_llm(streaming: bool = False):
    # streaming is handled via .astream(); no constructor flag needed for Gemini.
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=getattr(Config, "GEMINI_MODEL", "gemini-3.5-flash"),
        temperature=0,
        max_output_tokens=8192,
    )

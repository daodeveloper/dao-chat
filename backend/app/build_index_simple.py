"""Minimal FAISS index builder: markdown only, uses the configured embeddings provider.
Kept dependency-light on purpose (no Unstructured/PDF), so it runs cleanly at container boot.
Run: python -m app.build_index_simple
"""
import logging
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from .config import Config
from .providers import get_embeddings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def build():
    data_dir = Path(Config.DOCUMENTS_PATH)
    index_dir = Config.FAISS_INDEX_PATH
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150, separators=["\n\n", "\n", ". ", " ", ""]
    )
    md_files = sorted(data_dir.glob("*.md"))
    docs = []
    for md in md_files:
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning("skip %s: %s", md.name, e)
            continue
        for chunk in splitter.split_text(text):
            if chunk.strip():
                docs.append(Document(page_content=chunk, metadata={"source": md.name, "project": md.stem}))

    if not docs:
        logger.error("No markdown found to index in %s", data_dir)
        return

    logger.info("Embedding %d chunks from %d markdown files...", len(docs), len(md_files))
    db = FAISS.from_documents(docs, get_embeddings())
    db.save_local(index_dir)
    logger.info("FAISS index written to %s", index_dir)


if __name__ == "__main__":
    build()

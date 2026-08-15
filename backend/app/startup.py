import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def rebuild_index_if_needed():
    """Build the FAISS index if it is missing or older than the knowledge files."""
    try:
        from .config import Config
        index_path = Path(Config.FAISS_INDEX_PATH)
        data_path = Path(Config.DOCUMENTS_PATH)

        index_files = list(index_path.glob("*.faiss")) if index_path.exists() else []
        doc_files = list(data_path.glob("*.md"))
        if not doc_files:
            logger.warning("No markdown files found to index")
            return

        latest_doc = max((f.stat().st_mtime for f in doc_files), default=0)
        index_mtime = max((f.stat().st_mtime for f in index_files), default=0)

        if not index_files or latest_doc > index_mtime:
            logger.info("Building FAISS index...")
            from .build_index_simple import build
            build()
            logger.info("FAISS index built")
        else:
            logger.info("FAISS index is up to date")
    except Exception as e:
        logger.error(f"Index build skipped: {e}", exc_info=True)

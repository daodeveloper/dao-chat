import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def rebuild_index_if_needed():
    """Rebuild index if documents are newer than index or index doesn't exist"""
    try:
        from .config import Config
        index_path = Path(Config.FAISS_INDEX_PATH)
        data_path = Path(Config.DOCUMENTS_PATH)
        
        # Check if index exists
        index_files = list(index_path.glob("*.faiss")) if index_path.exists() else []
        
        if not index_files:
            logger.info("No FAISS index found, rebuilding...")
            _rebuild_index()
            return
        
        # Get the most recent index file modification time
        index_mtime = max((f.stat().st_mtime for f in index_files), default=0)
        
        # Get all document files
        doc_files = list(data_path.glob("*.md")) + list(data_path.glob("*.pdf"))
        
        if not doc_files:
            logger.warning("No document files found in /app/data")
            return
        
        # Get the most recent document modification time
        latest_doc_mtime = max((f.stat().st_mtime for f in doc_files), default=0)
        
        # Rebuild if any document is newer than the index
        if latest_doc_mtime > index_mtime:
            logger.info("Documents updated, rebuilding index...")
            _rebuild_index()
        else:
            logger.info("Index is up to date, no rebuild needed")
            
    except Exception as e:
        logger.error(f"Error checking/rebuilding index: {e}", exc_info=True)
        # Don't fail startup if index rebuild fails
        logger.warning("Continuing startup despite index rebuild error")

def _rebuild_index():
    """Internal function to rebuild the index"""
    try:
        from .create_index import main
        main(force_rebuild=True)
        logger.info("Index rebuilt successfully")
    except Exception as e:
        logger.error(f"Failed to rebuild index: {e}", exc_info=True)
        raise


"""
Lightweight web search so the bot can pull the latest info.
Uses Tavily if TAVILY_API_KEY is set, otherwise DuckDuckGo. Never raises; returns "" on failure.
"""
import logging
from .config import Config

logger = logging.getLogger(__name__)


def _search_tavily(query, max_results):
    if not getattr(Config, "TAVILY_API_KEY", ""):
        return None
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=Config.TAVILY_API_KEY)
        res = client.search(query=query, max_results=max_results)
        items = res.get("results", []) if isinstance(res, dict) else []
        return [{"title": i.get("title", ""), "url": i.get("url", ""), "snippet": i.get("content", "")} for i in items]
    except Exception as e:
        logger.warning(f"Tavily search failed: {e}")
        return None


def _search_ddg(query, max_results):
    DDGS = None
    try:
        from ddgs import DDGS
    except Exception:
        try:
            from duckduckgo_search import DDGS
        except Exception:
            logger.warning("No DuckDuckGo package installed (pip install ddgs)")
            return None
    try:
        out = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                out.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", "") or r.get("url", ""),
                    "snippet": r.get("body", "") or r.get("snippet", ""),
                })
        return out
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {e}")
        return None


def search_web(query: str, max_results: int = 4) -> str:
    """Return a short formatted block of web results, or '' if search is unavailable."""
    if not query or not query.strip():
        return ""
    results = _search_tavily(query, max_results) or _search_ddg(query, max_results)
    if not results:
        return ""
    lines = []
    for r in results[:max_results]:
        title = (r.get("title") or "").strip()
        snippet = (r.get("snippet") or "").strip()
        url = (r.get("url") or "").strip()
        if not (title or snippet):
            continue
        lines.append(f"- {title}: {snippet} ({url})")
    return "\n".join(lines)

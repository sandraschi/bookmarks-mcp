from typing import Any, Dict
from .manager import create_bookmark, read_bookmark, update_bookmark, delete_bookmark
from .organizer import organize_bookmarks
from .sync import sync_browsers
from ..ai.analyzer import analyze_text
from ..ai.tagger import tag_text
from ..ai.summarizer import summarize_text


async def bookmarks(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch for the `bookmarks` portmanteau tool.

    Parameters:
        operation: Operation name: create, read, update, delete, organize, sync, analyze, tag, summarize
        payload: Operation-specific parameters

    Returns:
        dict: Operation-specific result

    Usage:
        Use this function as the single entry point for the MCP tool.

    Examples:
        await bookmarks("create", {"url": "https://example.com", "title": "Example"})

    Notes:
        This function routes to per-domain async implementations.

    See Also:
        manager.py, organizer.py, sync.py, analyzer.py, tagger.py, summarizer.py
    """
    op = operation.lower().strip()
    if op == "create":
        return await create_bookmark(payload)
    if op == "read":
        return await read_bookmark(payload)
    if op == "update":
        return await update_bookmark(payload)
    if op == "delete":
        return await delete_bookmark(payload)
    if op == "organize":
        return await organize_bookmarks(payload)
    if op == "sync":
        return await sync_browsers(payload)
    if op == "analyze":
        return await analyze_text(payload)
    if op == "tag":
        return await tag_text(payload)
    if op == "summarize":
        return await summarize_text(payload)
    return {"error": f"Unsupported operation: {operation}"}

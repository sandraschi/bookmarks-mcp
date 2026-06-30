"""Safari bookmark tools (macOS plist)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from browser_bookmarks_tools.services.browser.safari_plist import (
    delete_safari_bookmark,
    read_safari_bookmarks,
    write_safari_bookmark,
)
from browser_bookmarks_tools.services.browser.safari_registry import is_safari_browser, safari_supported_on_platform

SUPPORTED_OPERATIONS = (
    "list_bookmarks",
    "add_bookmark",
    "delete_bookmark",
    "get_bookmark",
    "search",
    "search_bookmarks",
    "find_duplicates",
    "export_bookmarks",
    "find_old_bookmarks",
    "get_bookmark_stats",
    "find_broken_links",
)


def supported_safari_operations() -> list[str]:
    return list(SUPPORTED_OPERATIONS)


def _normalize(result: dict[str, Any], *, operation: str | None = None) -> dict[str, Any]:
    out = dict(result)
    status = out.get("status")
    if status == "success":
        out["success"] = True
    elif status in ("error", "planned"):
        out["success"] = status != "error"
    out["browser"] = "safari"
    out["browser_family"] = "safari"
    out["profile_name"] = "default"
    if operation:
        out["operation"] = operation
    return out


async def list_safari_bookmarks(bookmarks_path: str | None = None) -> dict[str, Any]:
    path = Path(bookmarks_path) if bookmarks_path else None
    return _normalize(read_safari_bookmarks(path), operation="list_bookmarks")


async def add_safari_bookmark(
    title: str,
    url: str,
    folder: str | None = None,
    bookmarks_path: str | None = None,
    allow_duplicates: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    path = Path(bookmarks_path) if bookmarks_path else None
    result = write_safari_bookmark(
        path,
        title=title,
        url=url,
        folder=folder,
        allow_duplicates=allow_duplicates,
        dry_run=dry_run,
    )
    return _normalize(result, operation="add_bookmark")


async def delete_safari_bookmark_op(
    *,
    url: str | None = None,
    dry_run: bool = False,
    bookmarks_path: str | None = None,
) -> dict[str, Any]:
    path = Path(bookmarks_path) if bookmarks_path else None
    result = delete_safari_bookmark(path, url=url, dry_run=dry_run)
    return _normalize(result, operation="delete_bookmark")


async def search_safari_bookmarks(
    search_query: str, bookmarks_path: str | None = None, limit: int = 100
) -> dict[str, Any]:
    listed = await list_safari_bookmarks(bookmarks_path)
    if not listed.get("success"):
        listed["operation"] = "search_bookmarks"
        return listed

    query = search_query.lower()
    matches = [
        item
        for item in listed.get("bookmarks", [])
        if query in str(item.get("title", "")).lower() or query in str(item.get("url", "")).lower()
    ]
    return {
        "success": True,
        "browser": "safari",
        "browser_family": "safari",
        "operation": "search_bookmarks",
        "query": search_query,
        "results": matches[:limit],
        "total_matches": len(matches),
    }


async def get_safari_bookmark(
    *,
    bookmark_id: str | None = None,
    url: str | None = None,
    bookmarks_path: str | None = None,
) -> dict[str, Any]:
    listed = await list_safari_bookmarks(bookmarks_path)
    if not listed.get("success"):
        listed["operation"] = "get_bookmark"
        return listed

    for bookmark in listed.get("bookmarks", []):
        if (bookmark_id and str(bookmark.get("id")) == str(bookmark_id)) or (url and bookmark.get("url") == url):
            return {
                "success": True,
                "browser": "safari",
                "browser_family": "safari",
                "operation": "get_bookmark",
                "bookmark": bookmark,
            }

    return {
        "success": False,
        "browser": "safari",
        "operation": "get_bookmark",
        "error": f"Bookmark not found: {bookmark_id or url}",
    }


__all__ = [
    "SUPPORTED_OPERATIONS",
    "add_safari_bookmark",
    "delete_safari_bookmark_op",
    "get_safari_bookmark",
    "is_safari_browser",
    "list_safari_bookmarks",
    "safari_supported_on_platform",
    "search_safari_bookmarks",
    "supported_safari_operations",
]

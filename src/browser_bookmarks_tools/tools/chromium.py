"""Unified Chromium-family bookmark CRUD (registry-driven)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from browser_bookmarks_tools.services.browser.chromium_manager import ChromiumManager
from browser_bookmarks_tools.services.browser.chromium_registry import (
    get_chromium_spec,
    is_chromium_browser,
    list_chromium_browser_ids,
    list_chromium_browsers,
    resolve_bookmarks_file,
)
from browser_bookmarks_tools.tools.chromium_common import (
    delete_chromium_bookmark as _delete_chromium_bookmark_file,
)
from browser_bookmarks_tools.tools.chromium_common import (
    edit_chromium_bookmark as _edit_chromium_bookmark_file,
)
from browser_bookmarks_tools.tools.chromium_common import (
    read_chromium_bookmarks,
    write_chromium_bookmark,
)

SUPPORTED_OPERATIONS = (
    "list_bookmarks",
    "add_bookmark",
    "edit_bookmark",
    "delete_bookmark",
    "get_bookmark",
    "search",
    "search_bookmarks",
)


def supported_chromium_operations() -> list[str]:
    return list(SUPPORTED_OPERATIONS)


def resolve_bookmarks_path(
    browser: str,
    profile_name: str | None = None,
    bookmarks_path: str | None = None,
) -> Path | None:
    if bookmarks_path:
        path = Path(bookmarks_path)
        return path if path.exists() else None

    spec = get_chromium_spec(browser)
    profile = profile_name or spec.default_profile
    return resolve_bookmarks_file(browser, profile)


def _normalize_result(
    result: dict[str, Any],
    *,
    browser: str,
    profile_name: str | None,
    operation: str | None = None,
) -> dict[str, Any]:
    out = dict(result)
    status = out.get("status")
    if status == "success":
        out["success"] = True
    elif status in ("error", "planned"):
        out["success"] = status != "error"
    out["browser"] = browser
    out["browser_family"] = "chromium"
    out["profile_name"] = profile_name or get_chromium_spec(browser).default_profile
    if operation:
        out["operation"] = operation
    return out


async def list_chromium_bookmarks(
    browser: str,
    profile_name: str | None = None,
    bookmarks_path: str | None = None,
) -> dict[str, Any]:
    path = resolve_bookmarks_path(browser, profile_name, bookmarks_path)
    if path is None:
        spec = get_chromium_spec(browser)
        return {
            "success": False,
            "status": "error",
            "browser": browser,
            "browser_family": "chromium",
            "profile_name": profile_name or spec.default_profile,
            "error": f"Bookmarks file not found for {spec.display_name}",
            "error_code": "CHROMIUM_FILE_NOT_FOUND",
            "recovery_options": [
                f"Install {spec.display_name} or verify profile_name.",
                "Pass bookmarks_path to override the file location.",
            ],
        }

    result = read_chromium_bookmarks(path)
    normalized = _normalize_result(result, browser=browser, profile_name=profile_name, operation="list_bookmarks")
    bookmarks = normalized.get("bookmarks", [])
    if isinstance(bookmarks, list):
        for item in bookmarks:
            if isinstance(item, dict) and "id" not in item:
                item["id"] = item.get("url")
    return normalized


async def add_chromium_bookmark(
    browser: str,
    title: str,
    url: str,
    folder: str | None = None,
    profile_name: str | None = None,
    bookmarks_path: str | None = None,
) -> dict[str, Any]:
    path = resolve_bookmarks_path(browser, profile_name, bookmarks_path)
    result = write_chromium_bookmark(path, title, url, folder)
    return _normalize_result(result, browser=browser, profile_name=profile_name, operation="add_bookmark")


async def edit_chromium_bookmark(
    browser: str,
    *,
    id: str | None = None,
    url: str | None = None,
    new_title: str | None = None,
    new_folder: str | None = None,
    allow_duplicates: bool = False,
    create_folders: bool = True,
    dry_run: bool = False,
    profile_name: str | None = None,
    bookmarks_path: str | None = None,
) -> dict[str, Any]:
    path = resolve_bookmarks_path(browser, profile_name, bookmarks_path)
    result = _edit_chromium_bookmark_file(
        path,
        id=id,
        url=url,
        new_title=new_title,
        new_folder=new_folder,
        allow_duplicates=allow_duplicates,
        create_folders=create_folders,
        dry_run=dry_run,
    )
    return _normalize_result(result, browser=browser, profile_name=profile_name, operation="edit_bookmark")


async def delete_chromium_bookmark(
    browser: str,
    *,
    id: str | None = None,
    url: str | None = None,
    dry_run: bool = False,
    profile_name: str | None = None,
    bookmarks_path: str | None = None,
) -> dict[str, Any]:
    path = resolve_bookmarks_path(browser, profile_name, bookmarks_path)
    result = _delete_chromium_bookmark_file(path, id=id, url=url, dry_run=dry_run)
    return _normalize_result(result, browser=browser, profile_name=profile_name, operation="delete_bookmark")


async def search_chromium_bookmarks(
    browser: str,
    search_query: str,
    profile_name: str | None = None,
    bookmarks_path: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    listed = await list_chromium_bookmarks(browser, profile_name, bookmarks_path)
    if not listed.get("success"):
        listed["operation"] = "search_bookmarks"
        return listed

    bookmarks = listed.get("bookmarks", [])
    query_lower = search_query.lower()
    matches = [
        bookmark
        for bookmark in bookmarks
        if query_lower in str(bookmark.get("title", "")).lower()
        or query_lower in str(bookmark.get("url", "")).lower()
    ]
    return {
        "success": True,
        "status": "success",
        "browser": browser,
        "browser_family": "chromium",
        "profile_name": listed.get("profile_name"),
        "operation": "search_bookmarks",
        "query": search_query,
        "results": matches[:limit],
        "total_matches": len(matches),
        "total_count": len(matches),
        "returned_count": min(len(matches), limit),
    }


async def get_chromium_bookmark(
    browser: str,
    *,
    bookmark_id: str | None = None,
    url: str | None = None,
    profile_name: str | None = None,
    bookmarks_path: str | None = None,
) -> dict[str, Any]:
    listed = await list_chromium_bookmarks(browser, profile_name, bookmarks_path)
    if not listed.get("success"):
        listed["operation"] = "get_bookmark"
        return listed

    for bookmark in listed.get("bookmarks", []):
        if (bookmark_id and str(bookmark.get("id")) == str(bookmark_id)) or (url and bookmark.get("url") == url):
            return {
                "success": True,
                "browser": browser,
                "browser_family": "chromium",
                "profile_name": listed.get("profile_name"),
                "operation": "get_bookmark",
                "bookmark": bookmark,
            }

    return {
        "success": False,
        "browser": browser,
        "browser_family": "chromium",
        "profile_name": listed.get("profile_name"),
        "operation": "get_bookmark",
        "error": f"Bookmark not found: {bookmark_id or url}",
        "recovery_options": ["Use search_bookmarks to locate valid bookmark ids."],
    }


async def get_chromium_profiles(browser: str) -> dict[str, Any]:
    manager = ChromiumManager(browser)
    try:
        profiles = await manager.get_profiles()
    except RuntimeError as exc:
        return {
            "success": False,
            "browser": browser,
            "error": str(exc),
            "recovery_options": [f"Install {get_chromium_spec(browser).display_name}."],
        }

    return {
        "success": True,
        "browser": browser,
        "browser_family": "chromium",
        "profiles": profiles,
        "count": len(profiles),
        "user_data_dir": str(manager.user_data_dir) if manager.user_data_dir else None,
    }


__all__ = [
    "SUPPORTED_OPERATIONS",
    "add_chromium_bookmark",
    "delete_chromium_bookmark",
    "edit_chromium_bookmark",
    "get_chromium_bookmark",
    "get_chromium_profiles",
    "is_chromium_browser",
    "list_chromium_bookmarks",
    "list_chromium_browser_ids",
    "list_chromium_browsers",
    "resolve_bookmarks_path",
    "search_chromium_bookmarks",
    "supported_chromium_operations",
]

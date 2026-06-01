"""Safari Bookmarks.plist read/write helpers."""

from __future__ import annotations

import plistlib
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from browser_bookmarks_tools.services.browser.safari_registry import (
    resolve_safari_bookmarks_plist,
    safari_supported_on_platform,
)


def _walk_safari_node(node: dict[str, Any], folder_path: str, out: list[dict[str, Any]]) -> None:
    bookmark_type = node.get("WebBookmarkType")
    if bookmark_type == "WebBookmarkTypeLeaf":
        uri = node.get("URIDictionary") or {}
        url = uri.get("URLString") or ""
        if not url:
            return
        title = uri.get("title") or uri.get("URLString") or url
        out.append(
            {
                "id": url,
                "title": title,
                "url": url,
                "folder_path": folder_path,
            }
        )
        return

    if bookmark_type == "WebBookmarkTypeList":
        title = node.get("Title") or "Folder"
        next_path = f"{folder_path}/{title}" if folder_path else title
        for child in node.get("Children") or []:
            if isinstance(child, dict):
                _walk_safari_node(child, next_path, out)


def parse_safari_bookmarks(data: dict[str, Any]) -> list[dict[str, Any]]:
    bookmarks: list[dict[str, Any]] = []
    for child in data.get("Children") or []:
        if isinstance(child, dict):
            _walk_safari_node(child, "", bookmarks)
    return bookmarks


def read_safari_bookmarks(path: Path | None = None) -> dict[str, Any]:
    if path is None and not safari_supported_on_platform():
        return {
            "status": "error",
            "error_code": "SAFARI_PLATFORM_UNSUPPORTED",
            "error": "Safari bookmark access requires macOS",
            "recovery_options": ["Run bookmarks-mcp on macOS with Full Disk Access for Safari."],
        }

    plist_path = path or resolve_safari_bookmarks_plist()
    if plist_path is None or not plist_path.exists():
        return {
            "status": "error",
            "error_code": "SAFARI_FILE_NOT_FOUND",
            "error": f"Safari Bookmarks.plist not found: {plist_path}",
            "recovery_options": ["Install Safari and create at least one bookmark."],
        }

    try:
        with plist_path.open("rb") as handle:
            data = plistlib.load(handle)
        if not isinstance(data, dict):
            return {"status": "error", "error": "Invalid Safari plist root type"}
        bookmarks = parse_safari_bookmarks(data)
        return {
            "status": "success",
            "count": len(bookmarks),
            "bookmarks": bookmarks,
            "bookmarks_path": str(plist_path),
        }
    except Exception as exc:
        return {
            "status": "error",
            "error_code": "SAFARI_READ_FAILED",
            "error": f"{type(exc).__name__}: {exc}",
            "recovery_options": ["Grant Full Disk Access to the host app.", "Close Safari before writes."],
        }


def _find_folder_list(root: dict[str, Any], folder_name: str | None) -> dict[str, Any]:
    if not folder_name:
        for child in root.get("Children") or []:
            if isinstance(child, dict) and child.get("WebBookmarkType") == "WebBookmarkTypeList":
                return child
        root.setdefault("Children", [])
        created = {
            "WebBookmarkType": "WebBookmarkTypeList",
            "Title": "Imported",
            "Children": [],
        }
        root["Children"].append(created)
        return created

    stack: list[dict[str, Any]] = [root]
    while stack:
        node = stack.pop()
        for child in node.get("Children") or []:
            if not isinstance(child, dict):
                continue
            if child.get("WebBookmarkType") == "WebBookmarkTypeList" and child.get("Title") == folder_name:
                return child
            if child.get("WebBookmarkType") == "WebBookmarkTypeList":
                stack.append(child)

    root.setdefault("Children", [])
    created = {
        "WebBookmarkType": "WebBookmarkTypeList",
        "Title": folder_name,
        "Children": [],
    }
    root["Children"].append(created)
    return created


def write_safari_bookmark(
    path: Path | None,
    title: str,
    url: str,
    folder: str | None = None,
    allow_duplicates: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    read_result = read_safari_bookmarks(path)
    if read_result.get("status") != "success":
        return read_result

    plist_path = Path(read_result["bookmarks_path"])
    existing = read_result.get("bookmarks") or []
    if not allow_duplicates and any(item.get("url") == url for item in existing):
        return {"status": "success", "message": "Duplicate skipped", "duplicate": True}

    with plist_path.open("rb") as handle:
        data = plistlib.load(handle)
    if not isinstance(data, dict):
        return {"status": "error", "error": "Invalid Safari plist root type"}

    target_folder = _find_folder_list(data, folder)
    target_folder.setdefault("Children", [])
    target_folder["Children"].append(
        {
            "WebBookmarkType": "WebBookmarkTypeLeaf",
            "URIDictionary": {
                "title": title or url,
                "URLString": url,
            },
            "WebBookmarkUUID": str(uuid4()).upper(),
        }
    )

    if dry_run:
        return {"status": "planned", "action": "add", "url": url, "folder": folder}

    backup = plist_path.with_suffix(f".backup-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.plist")
    shutil.copy2(plist_path, backup)
    with plist_path.open("wb") as handle:
        plistlib.dump(data, handle, fmt=plistlib.FMT_BINARY)

    return {
        "status": "success",
        "bookmark": {"title": title or url, "url": url, "folder": folder},
        "backup_path": str(backup),
    }


def delete_safari_bookmark(
    path: Path | None,
    *,
    url: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    if not url:
        return {"status": "error", "error": "url is required for Safari delete"}

    read_result = read_safari_bookmarks(path)
    if read_result.get("status") != "success":
        return read_result

    plist_path = Path(read_result["bookmarks_path"])
    with plist_path.open("rb") as handle:
        data = plistlib.load(handle)
    if not isinstance(data, dict):
        return {"status": "error", "error": "Invalid Safari plist root type"}

    removed = False

    def _prune(node: dict[str, Any]) -> None:
        nonlocal removed
        children = node.get("Children")
        if not isinstance(children, list):
            return
        kept: list[Any] = []
        for child in children:
            if not isinstance(child, dict):
                kept.append(child)
                continue
            if child.get("WebBookmarkType") == "WebBookmarkTypeLeaf":
                uri = child.get("URIDictionary") or {}
                if uri.get("URLString") == url:
                    removed = True
                    continue
            _prune(child)
            kept.append(child)
        node["Children"] = kept

    _prune(data)
    if not removed:
        return {"status": "error", "error": "Bookmark not found"}

    if dry_run:
        return {"status": "planned", "action": "delete", "url": url}

    backup = plist_path.with_suffix(f".backup-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.plist")
    shutil.copy2(plist_path, backup)
    with plist_path.open("wb") as handle:
        plistlib.dump(data, handle, fmt=plistlib.FMT_BINARY)

    return {"status": "success", "deleted": True, "backup_path": str(backup)}

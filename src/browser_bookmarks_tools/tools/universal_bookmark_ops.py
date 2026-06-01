"""Browser-agnostic bookmark analysis and export operations."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

import aiohttp


def find_duplicates_from_bookmarks(
    bookmarks: list[dict[str, Any]],
    *,
    similarity_threshold: float = 0.85,
) -> dict[str, Any]:
    del similarity_threshold
    by_url: dict[str, list[dict[str, Any]]] = {}
    for bookmark in bookmarks:
        url = bookmark.get("url")
        if not url:
            continue
        by_url.setdefault(url, []).append(bookmark)

    duplicates = [
        {"url": url, "count": len(items), "bookmarks": items}
        for url, items in by_url.items()
        if len(items) > 1
    ]
    return {
        "success": True,
        "operation": "find_duplicates",
        "total_duplicates": len(duplicates),
        "duplicates": duplicates,
    }


def find_old_bookmarks_from_list(bookmarks: list[dict[str, Any]], age_days: int) -> dict[str, Any]:
    cutoff = datetime.now(tz=UTC).timestamp() - (age_days * 86400)
    old: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []

    for bookmark in bookmarks:
        ts = bookmark.get("added_timestamp")
        if ts is None:
            unknown.append(bookmark)
            continue
        if ts < cutoff:
            old.append(bookmark)

    return {
        "success": True,
        "operation": "find_old_bookmarks",
        "age_days": age_days,
        "count": len(old),
        "bookmarks": old,
        "unknown_age_count": len(unknown),
    }


def get_bookmark_stats_from_list(bookmarks: list[dict[str, Any]]) -> dict[str, Any]:
    folder_counts = Counter()
    for bookmark in bookmarks:
        folder = bookmark.get("folder_path") or "(root)"
        folder_counts[folder] += 1

    dated = [b for b in bookmarks if b.get("added_timestamp") is not None]
    oldest = min(dated, key=lambda b: b["added_timestamp"]) if dated else None
    newest = max(dated, key=lambda b: b["added_timestamp"]) if dated else None

    return {
        "success": True,
        "operation": "get_bookmark_stats",
        "stats": {
            "total_bookmarks": len(bookmarks),
            "folders": len(folder_counts),
            "top_folders": folder_counts.most_common(10),
            "dated_bookmarks": len(dated),
            "oldest": oldest,
            "newest": newest,
        },
    }


def export_bookmarks_to_file(
    bookmarks: list[dict[str, Any]],
    export_format: str,
    export_path: str | None = None,
) -> dict[str, Any]:
    fmt = export_format.lower()
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    default_name = f"bookmarks_{timestamp}.{ 'html' if fmt == 'netscape' else fmt }"
    output_path = Path(export_path or default_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        {
            "title": bookmark.get("title") or bookmark.get("url"),
            "url": bookmark.get("url"),
            "folder_path": bookmark.get("folder_path") or "",
        }
        for bookmark in bookmarks
        if bookmark.get("url")
    ]

    if fmt == "json":
        output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    elif fmt == "csv":
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["title", "url", "folder_path"])
            writer.writeheader()
            writer.writerows(rows)
    elif fmt in {"html", "netscape"}:
        lines = [
            "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
            "<TITLE>Bookmarks</TITLE>",
            "<H1>Bookmarks</H1>",
            "<DL><p>",
        ]
        for row in rows:
            lines.append(f'    <DT><A HREF="{escape(row["url"])}">{escape(row["title"])}</A>')
        lines.extend(["</DL><p>", ""])
        output_path.write_text("\n".join(lines), encoding="utf-8")
    else:
        return {
            "success": False,
            "operation": "export_bookmarks",
            "error": f"Unsupported export format: {export_format}",
            "supported_formats": ["json", "csv", "html", "netscape"],
        }

    return {
        "success": True,
        "operation": "export_bookmarks",
        "export_format": fmt,
        "export_path": str(output_path),
        "record_count": len(rows),
    }


async def find_broken_links_from_list(
    bookmarks: list[dict[str, Any]],
    *,
    limit: int = 100,
    check_links: bool = True,
) -> dict[str, Any]:
    if not check_links:
        return {
            "success": True,
            "operation": "find_broken_links",
            "checked": 0,
            "broken_links": [],
            "note": "Set check_links=True to perform HTTP checks",
        }

    candidates = [b for b in bookmarks if b.get("url")][:limit]
    broken: list[dict[str, Any]] = []
    redirected: list[dict[str, Any]] = []

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for bookmark in candidates:
            url = bookmark["url"]
            try:
                async with session.head(url, allow_redirects=True) as response:
                    item = {
                        "title": bookmark.get("title"),
                        "url": url,
                        "status": response.status,
                        "final_url": str(response.url),
                    }
                    if response.status >= 400:
                        broken.append(item)
                    elif str(response.url) != url:
                        redirected.append(item)
            except Exception as exc:
                broken.append(
                    {
                        "title": bookmark.get("title"),
                        "url": url,
                        "error": str(exc),
                        "is_broken": True,
                    }
                )

    return {
        "success": True,
        "operation": "find_broken_links",
        "checked": len(candidates),
        "broken_links": broken,
        "redirected_links": redirected,
        "broken_count": len(broken),
    }


UNIVERSAL_ADVANCED_OPERATIONS = (
    "find_duplicates",
    "export_bookmarks",
    "find_old_bookmarks",
    "get_bookmark_stats",
    "find_broken_links",
)


async def execute_universal_operation(
    operation: str,
    browser: str,
    profile_name: str | None,
    *,
    bookmarks_path: str | None = None,
    limit: int = 10_000,
    export_format: str = "json",
    export_path: str | None = None,
    similarity_threshold: float = 0.85,
    age_days: int = 365,
    check_links: bool = False,
) -> dict[str, Any]:
    from browser_bookmarks_tools.tools.bookmark_loader import load_browser_bookmarks

    loaded = await load_browser_bookmarks(
        browser,
        profile_name,
        limit=limit,
        bookmarks_path=bookmarks_path,
    )
    if not loaded.get("success"):
        loaded["operation"] = operation
        return loaded

    bookmarks = loaded.get("bookmarks") or []

    if operation == "find_duplicates":
        result = find_duplicates_from_bookmarks(bookmarks, similarity_threshold=similarity_threshold)
    elif operation == "export_bookmarks":
        result = export_bookmarks_to_file(bookmarks, export_format, export_path)
    elif operation == "find_old_bookmarks":
        result = find_old_bookmarks_from_list(bookmarks, age_days)
    elif operation == "get_bookmark_stats":
        result = get_bookmark_stats_from_list(bookmarks)
    elif operation == "find_broken_links":
        result = await find_broken_links_from_list(bookmarks, limit=min(limit, 200), check_links=check_links)
    else:
        return {
            "success": False,
            "operation": operation,
            "error": f"Unsupported universal operation: {operation}",
        }

    result["browser"] = loaded.get("browser", browser)
    result["browser_family"] = loaded.get("browser_family")
    result["profile_name"] = loaded.get("profile_name")
    return result

"""Parse bookmark exports (Netscape HTML, Chromium JSON, Firefox JSON) without a live browser."""

from __future__ import annotations

import json
from html import unescape
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


def detect_import_format(path: Path, content: str | None = None) -> str:
    text = content if content is not None else path.read_text(encoding="utf-8", errors="replace")
    stripped = text.lstrip()
    if stripped.startswith("{"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return "json"
        if isinstance(payload, dict) and "roots" in payload:
            return "chrome_json"
        if isinstance(payload, dict) and ("bookmarks" in payload or "children" in payload):
            return "firefox_json"
        if isinstance(payload, list):
            return "json_list"
        return "json"
    if "NETSCAPE-Bookmark-file-1" in text[:500] or "<DL" in text.upper():
        return "netscape_html"
    return "netscape_html"


def parse_bookmark_file(path: str | Path, import_format: str = "auto") -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {"success": False, "error": f"Import file not found: {file_path}"}

    raw = file_path.read_text(encoding="utf-8", errors="replace")
    fmt = import_format.lower()
    if fmt in ("auto", ""):
        fmt = detect_import_format(file_path, raw)

    if fmt in ("html", "netscape", "netscape_html"):
        bookmarks = parse_netscape_html(raw)
    elif fmt in ("chrome", "chrome_json", "chromium"):
        bookmarks = parse_chrome_json(raw)
    elif fmt in ("firefox", "firefox_json", "gecko"):
        bookmarks = parse_firefox_json(raw)
    elif fmt in ("json", "json_list"):
        bookmarks = parse_generic_json(raw)
    else:
        return {
            "success": False,
            "error": f"Unsupported import_format: {import_format}",
            "supported_formats": ["auto", "netscape_html", "chrome_json", "firefox_json", "json"],
        }

    return {
        "success": True,
        "import_format": fmt,
        "import_path": str(file_path),
        "count": len(bookmarks),
        "bookmarks": bookmarks,
    }


def parse_netscape_html(content: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(content, "html.parser")
    bookmarks: list[dict[str, Any]] = []

    for anchor in soup.find_all("a"):
        href = anchor.get("href")
        if not href or href.startswith("javascript:"):
            continue

        folder_parts: list[str] = []
        for h3 in anchor.find_all_previous(["h3", "H3"]):
            dt_parent = h3.find_parent("dt")
            dl_parent = h3.find_parent("dl")
            if dt_parent is None or dl_parent is None:
                continue
            if anchor.find_parent("dl") is None:
                continue
            if dl_parent in anchor.find_parents("dl"):
                title = unescape(h3.get_text(strip=True) or "Folder")
                if title and (not folder_parts or folder_parts[0] != title):
                    folder_parts.insert(0, title)

        title = unescape(anchor.get_text(strip=True) or href)
        tags_attr = anchor.get("tags") or anchor.get("TAGS")
        tags = [t.strip() for t in tags_attr.split(",")] if tags_attr else []
        bookmarks.append(
            {
                "title": title,
                "url": href.strip(),
                "folder_path": "/".join(folder_parts),
                "tags": tags,
            }
        )

    return bookmarks


def parse_chrome_json(content: str) -> list[dict[str, Any]]:
    payload = json.loads(content)
    roots = payload.get("roots") if isinstance(payload, dict) else None
    if not isinstance(roots, dict):
        return parse_generic_json(content)

    bookmarks: list[dict[str, Any]] = []

    def walk(node: dict[str, Any], folder_path: str) -> None:
        node_type = node.get("type")
        if node_type == "url":
            url = node.get("url") or ""
            if url:
                bookmarks.append(
                    {
                        "title": node.get("name") or url,
                        "url": url,
                        "folder_path": folder_path,
                        "tags": node.get("tags") or [],
                    }
                )
            return
        if node_type == "folder":
            name = node.get("name") or "Folder"
            next_path = f"{folder_path}/{name}" if folder_path else name
            for child in node.get("children") or []:
                if isinstance(child, dict):
                    walk(child, next_path)

    for root_node in roots.values():
        if isinstance(root_node, dict):
            walk(root_node, "")

    return bookmarks


def parse_firefox_json(content: str) -> list[dict[str, Any]]:
    payload = json.loads(content)
    if isinstance(payload, list):
        return _normalize_import_rows(payload)

    if isinstance(payload, dict):
        if "bookmarks" in payload and isinstance(payload["bookmarks"], list):
            return _normalize_import_rows(payload["bookmarks"])
        if "children" in payload and isinstance(payload["children"], list):
            return _walk_firefox_tree(payload["children"], "")

    return []


def _walk_firefox_tree(children: list[Any], folder_path: str) -> list[dict[str, Any]]:
    bookmarks: list[dict[str, Any]] = []
    for child in children:
        if not isinstance(child, dict):
            continue
        if child.get("uri") or child.get("url"):
            url = child.get("uri") or child.get("url")
            bookmarks.append(
                {
                    "title": child.get("title") or url,
                    "url": url,
                    "folder_path": folder_path,
                    "description": child.get("description"),
                    "tags": child.get("tags") or [],
                }
            )
            continue
        folder_name = child.get("title") or child.get("name") or "Folder"
        next_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
        nested = child.get("children") or []
        if isinstance(nested, list):
            bookmarks.extend(_walk_firefox_tree(nested, next_path))
    return bookmarks


def parse_generic_json(content: str) -> list[dict[str, Any]]:
    payload = json.loads(content)
    if isinstance(payload, list):
        return _normalize_import_rows(payload)
    if isinstance(payload, dict) and isinstance(payload.get("bookmarks"), list):
        return _normalize_import_rows(payload["bookmarks"])
    return []


def _normalize_import_rows(rows: list[Any]) -> list[dict[str, Any]]:
    bookmarks: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = row.get("url") or row.get("uri") or row.get("URLString")
        if not url:
            continue
        bookmarks.append(
            {
                "title": row.get("title") or row.get("name") or url,
                "url": url,
                "folder_path": row.get("folder_path") or row.get("folder") or "",
                "description": row.get("description"),
                "tags": row.get("tags") or [],
                "user_comment": row.get("user_comment") or row.get("comment"),
                "starred": row.get("starred") or row.get("rating") or 0,
            }
        )
    return bookmarks


def metadata_rows_from_bookmarks(
    bookmarks: list[dict[str, Any]],
    *,
    browser: str | None = None,
    profile_name: str | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bookmark in bookmarks:
        url = bookmark.get("url")
        if not url:
            continue
        rows.append(
            {
                "url": url,
                "browser": browser or "",
                "profile_name": profile_name or "",
                "title": bookmark.get("title"),
                "description": bookmark.get("description"),
                "user_comment": bookmark.get("user_comment"),
                "tags": bookmark.get("tags") or [],
                "starred": int(bookmark.get("starred") or 0),
            }
        )
    return rows

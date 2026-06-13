"""Merge sidecar metadata into native bookmark records."""

from __future__ import annotations

from typing import Any

from browser_bookmarks_tools.services.metadata.sidecar_db import SidecarMetadataStore


def enrich_bookmark(
    bookmark: dict[str, Any],
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    if not metadata:
        return bookmark
    out = dict(bookmark)
    sidecar = {
        "description": metadata.get("description"),
        "user_comment": metadata.get("user_comment"),
        "tags": metadata.get("tags") or [],
        "starred": metadata.get("starred") or 0,
        "read_count": metadata.get("read_count") or 0,
        "last_read_at": metadata.get("last_read_at"),
        "updated_at": metadata.get("updated_at"),
    }
    out["metadata"] = sidecar
    if sidecar["description"] and not out.get("description"):
        out["description"] = sidecar["description"]
    if sidecar["tags"] and not out.get("tags"):
        out["tags"] = sidecar["tags"]
    return out


def enrich_bookmarks(
    bookmarks: list[dict[str, Any]],
    *,
    browser: str | None = None,
    profile_name: str | None = None,
    store: SidecarMetadataStore | None = None,
) -> list[dict[str, Any]]:
    if not bookmarks:
        return bookmarks
    db = store or SidecarMetadataStore()
    urls = [str(item.get("url")) for item in bookmarks if item.get("url")]
    meta_map = db.get_many(urls, browser=browser, profile_name=profile_name)
    return [enrich_bookmark(item, meta_map.get(str(item.get("url")))) for item in bookmarks]

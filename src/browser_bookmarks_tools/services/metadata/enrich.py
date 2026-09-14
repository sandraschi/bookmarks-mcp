"""Merge sidecar metadata and collection membership into native bookmark records."""

from __future__ import annotations

from typing import Any

from browser_bookmarks_tools.services.metadata.collection_store import CollectionStore
from browser_bookmarks_tools.services.metadata.sidecar_db import SidecarMetadataStore


def enrich_bookmark(
    bookmark: dict[str, Any],
    metadata: dict[str, Any] | None,
    member_collections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    out = dict(bookmark)
    out["collections"] = member_collections or []
    if not metadata:
        return out
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
    out["starred"] = sidecar["starred"]
    out["user_comment"] = sidecar["user_comment"]
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
    collection_store: CollectionStore | None = None,
) -> list[dict[str, Any]]:
    if not bookmarks:
        return bookmarks
    db = store or SidecarMetadataStore()
    collections_db = collection_store or CollectionStore()
    urls = [str(item.get("url")) for item in bookmarks if item.get("url")]
    meta_map = db.get_many(urls, browser=browser, profile_name=profile_name)
    collections_map = collections_db.get_collections_for_urls(urls, browser=browser, profile_name=profile_name)
    return [
        enrich_bookmark(
            item,
            meta_map.get(str(item.get("url"))),
            collections_map.get(str(item.get("url"))),
        )
        for item in bookmarks
    ]

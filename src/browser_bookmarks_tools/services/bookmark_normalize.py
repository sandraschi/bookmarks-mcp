"""Normalize bookmark records from any browser family to a common shape."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def chromium_timestamp_to_datetime(raw: Any) -> datetime | None:
    try:
        micros = int(str(raw))
    except (TypeError, ValueError):
        return None
    if micros <= 0:
        return None
    # Chromium stores microseconds since 1601-01-01 UTC
    seconds = (micros / 1_000_000) - 11_644_473_600
    return datetime.fromtimestamp(seconds, tz=UTC)


def firefox_timestamp_to_datetime(raw: Any) -> datetime | None:
    try:
        micros = int(str(raw))
    except (TypeError, ValueError):
        return None
    if micros <= 0:
        return None
    # Firefox places uses microseconds since Unix epoch
    return datetime.fromtimestamp(micros / 1_000_000, tz=UTC)


def normalize_bookmark(raw: dict[str, Any], *, browser_family: str) -> dict[str, Any]:
    title = raw.get("title") or raw.get("name") or raw.get("Title") or ""
    url = raw.get("url") or raw.get("URLString") or ""
    folder_path = raw.get("folder_path") or raw.get("parent") or raw.get("folder") or ""
    bookmark_id = raw.get("id") or url

    added = None
    if browser_family == "chromium":
        added = chromium_timestamp_to_datetime(raw.get("added_date") or raw.get("date_added"))
    elif browser_family == "gecko":
        added = firefox_timestamp_to_datetime(raw.get("dateAdded") or raw.get("date_added"))
    elif browser_family == "safari":
        added = None

    return {
        "id": str(bookmark_id) if bookmark_id is not None else "",
        "title": str(title),
        "url": str(url),
        "folder_path": str(folder_path) if folder_path else "",
        "added_at": added.isoformat() if added else None,
        "added_timestamp": added.timestamp() if added else None,
        "raw": raw,
    }


def normalize_bookmarks(items: list[dict[str, Any]], *, browser_family: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        bookmark = normalize_bookmark(item, browser_family=browser_family)
        if bookmark.get("url"):
            normalized.append(bookmark)
    return normalized

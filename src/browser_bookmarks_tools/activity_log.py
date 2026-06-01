"""In-memory activity feed for web dashboard and audit trail."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from threading import Lock
from typing import Any

_MAX_ENTRIES = 200
_lock = Lock()
_entries: deque[dict[str, Any]] = deque(maxlen=_MAX_ENTRIES)


def log_activity(kind: str, detail: str, *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    entry = {
        "id": f"{datetime.now(UTC).timestamp():.6f}",
        "timestamp": datetime.now(UTC).isoformat(),
        "kind": kind,
        "detail": detail,
        "meta": meta or {},
    }
    with _lock:
        _entries.appendleft(entry)
    return entry


def get_activity(limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(limit, _MAX_ENTRIES))
    with _lock:
        return list(_entries)[:limit]


def clear_activity() -> None:
    with _lock:
        _entries.clear()

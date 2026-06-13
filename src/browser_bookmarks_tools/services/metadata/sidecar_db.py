"""SQLite sidecar for bookmark enrichment metadata.

Native browser stores (Chromium JSON, Safari plist) lack description, user notes,
star ratings, read stats, and portable tags. Firefox places.sqlite has description
and tags but they do not travel with exports to other browsers.

This sidecar keys rows by (url, browser, profile_name) with empty strings for
global scope. Set browser='' and profile_name='' for URL-global metadata.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def default_sidecar_path() -> Path:
    data_dir = os.getenv("BOOKMARKS_MCP_DATA_DIR")
    if data_dir:
        root = Path(data_dir)
    else:
        root = Path.home() / ".bookmarks-mcp"
    root.mkdir(parents=True, exist_ok=True)
    return root / "metadata.db"


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _scope(browser: str | None, profile_name: str | None) -> tuple[str, str]:
    return (browser or "").lower(), profile_name or ""


class SidecarMetadataStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or default_sidecar_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS bookmark_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    browser TEXT NOT NULL DEFAULT '',
                    profile_name TEXT NOT NULL DEFAULT '',
                    title TEXT,
                    description TEXT,
                    user_comment TEXT,
                    tags TEXT NOT NULL DEFAULT '[]',
                    starred INTEGER NOT NULL DEFAULT 0,
                    read_count INTEGER NOT NULL DEFAULT 0,
                    last_read_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(url, browser, profile_name)
                );
                CREATE INDEX IF NOT EXISTS idx_metadata_url ON bookmark_metadata(url);
                CREATE INDEX IF NOT EXISTS idx_metadata_scope ON bookmark_metadata(browser, profile_name);
                CREATE INDEX IF NOT EXISTS idx_metadata_starred ON bookmark_metadata(starred);
                """
            )

    def get(
        self,
        url: str,
        *,
        browser: str | None = None,
        profile_name: str | None = None,
        fallback_global: bool = True,
    ) -> dict[str, Any] | None:
        browser_key, profile_key = _scope(browser, profile_name)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM bookmark_metadata
                WHERE url = ? AND browser = ? AND profile_name = ?
                """,
                (url, browser_key, profile_key),
            ).fetchone()
            if row is None and fallback_global and (browser_key or profile_key):
                row = conn.execute(
                    "SELECT * FROM bookmark_metadata WHERE url = ? AND browser = '' AND profile_name = ''",
                    (url,),
                ).fetchone()
            return self._row_to_dict(row) if row else None

    def get_many(
        self,
        urls: list[str],
        *,
        browser: str | None = None,
        profile_name: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        if not urls:
            return {}
        browser_key, profile_key = _scope(browser, profile_name)
        placeholders = ",".join("?" for _ in urls)
        out: dict[str, dict[str, Any]] = {}
        with self._connect() as conn:
            scoped = conn.execute(
                f"""
                SELECT * FROM bookmark_metadata
                WHERE url IN ({placeholders}) AND browser = ? AND profile_name = ?
                """,
                [*urls, browser_key, profile_key],
            ).fetchall()
            for row in scoped:
                item = self._row_to_dict(row)
                out[item["url"]] = item

            missing = [url for url in urls if url not in out]
            if missing and (browser_key or profile_key):
                global_rows = conn.execute(
                    f"""
                    SELECT * FROM bookmark_metadata
                    WHERE url IN ({','.join('?' for _ in missing)})
                      AND browser = '' AND profile_name = ''
                    """,
                    missing,
                ).fetchall()
                for row in global_rows:
                    item = self._row_to_dict(row)
                    out.setdefault(item["url"], item)
        return out

    def upsert(
        self,
        url: str,
        *,
        browser: str | None = None,
        profile_name: str | None = None,
        title: str | None = None,
        description: str | None = None,
        user_comment: str | None = None,
        tags: list[str] | None = None,
        starred: int | None = None,
        read_count: int | None = None,
        last_read_at: str | None = None,
    ) -> dict[str, Any]:
        browser_key, profile_key = _scope(browser, profile_name)
        existing = self.get(url, browser=browser_key, profile_name=profile_key, fallback_global=False)
        now = _now_iso()
        created = existing["created_at"] if existing else now

        merged_tags = tags
        if merged_tags is None and existing:
            merged_tags = existing.get("tags") or []
        merged_tags = merged_tags or []

        merged_starred = starred if starred is not None else (existing or {}).get("starred", 0)
        merged_read_count = read_count if read_count is not None else (existing or {}).get("read_count", 0)
        merged_last_read = last_read_at if last_read_at is not None else (existing or {}).get("last_read_at")

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO bookmark_metadata (
                    url, browser, profile_name, title, description, user_comment,
                    tags, starred, read_count, last_read_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url, browser, profile_name) DO UPDATE SET
                    title = COALESCE(excluded.title, bookmark_metadata.title),
                    description = COALESCE(excluded.description, bookmark_metadata.description),
                    user_comment = COALESCE(excluded.user_comment, bookmark_metadata.user_comment),
                    tags = excluded.tags,
                    starred = excluded.starred,
                    read_count = excluded.read_count,
                    last_read_at = COALESCE(excluded.last_read_at, bookmark_metadata.last_read_at),
                    updated_at = excluded.updated_at
                """,
                (
                    url,
                    browser_key,
                    profile_key,
                    title if title is not None else (existing or {}).get("title"),
                    description if description is not None else (existing or {}).get("description"),
                    user_comment if user_comment is not None else (existing or {}).get("user_comment"),
                    json.dumps(sorted(set(str(t) for t in merged_tags if t))),
                    int(merged_starred or 0),
                    int(merged_read_count or 0),
                    merged_last_read,
                    created,
                    now,
                ),
            )
        saved = self.get(url, browser=browser_key, profile_name=profile_key, fallback_global=False)
        return {"success": True, "metadata": saved}

    def record_read(
        self,
        url: str,
        *,
        browser: str | None = None,
        profile_name: str | None = None,
    ) -> dict[str, Any]:
        existing = self.get(url, browser=browser, profile_name=profile_name, fallback_global=False)
        read_count = int((existing or {}).get("read_count") or 0) + 1
        return self.upsert(
            url,
            browser=browser,
            profile_name=profile_name,
            read_count=read_count,
            last_read_at=_now_iso(),
        )

    def delete(
        self,
        url: str,
        *,
        browser: str | None = None,
        profile_name: str | None = None,
    ) -> dict[str, Any]:
        browser_key, profile_key = _scope(browser, profile_name)
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM bookmark_metadata WHERE url = ? AND browser = ? AND profile_name = ?",
                (url, browser_key, profile_key),
            )
        return {"success": True, "deleted": cur.rowcount > 0, "url": url}

    def list_metadata(
        self,
        *,
        browser: str | None = None,
        profile_name: str | None = None,
        tag: str | None = None,
        starred_only: bool = False,
        search_query: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        browser_key, profile_key = _scope(browser, profile_name)
        clauses = ["1=1"]
        params: list[Any] = []

        if browser is not None:
            clauses.append("browser = ?")
            params.append(browser_key)
        if profile_name is not None:
            clauses.append("profile_name = ?")
            params.append(profile_key)
        if starred_only:
            clauses.append("starred > 0")
        if search_query:
            like = f"%{search_query}%"
            clauses.append("(url LIKE ? OR title LIKE ? OR description LIKE ? OR user_comment LIKE ? OR tags LIKE ?)")
            params.extend([like, like, like, like, like])
        if tag:
            clauses.append("tags LIKE ?")
            params.append(f'%"{tag}"%')

        where = " AND ".join(clauses)
        with self._connect() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM bookmark_metadata WHERE {where}",
                params,
            ).fetchone()[0]
            rows = conn.execute(
                f"""
                SELECT * FROM bookmark_metadata
                WHERE {where}
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            ).fetchall()

        items = [self._row_to_dict(row) for row in rows]
        return {
            "success": True,
            "items": items,
            "total_count": total,
            "returned_count": len(items),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(items) < total,
                "total_count": total,
            },
        }

    def import_rows(self, rows: list[dict[str, Any]], *, merge: bool = True) -> dict[str, Any]:
        imported = 0
        for row in rows:
            url = row.get("url")
            if not url:
                continue
            if merge:
                self.upsert(
                    url,
                    browser=row.get("browser"),
                    profile_name=row.get("profile_name"),
                    title=row.get("title"),
                    description=row.get("description"),
                    user_comment=row.get("user_comment"),
                    tags=row.get("tags"),
                    starred=row.get("starred"),
                )
            else:
                self.upsert(
                    url,
                    browser=row.get("browser"),
                    profile_name=row.get("profile_name"),
                    title=row.get("title"),
                    description=row.get("description"),
                    user_comment=row.get("user_comment"),
                    tags=row.get("tags") or [],
                    starred=row.get("starred") or 0,
                    read_count=row.get("read_count") or 0,
                    last_read_at=row.get("last_read_at"),
                )
            imported += 1
        return {"success": True, "imported": imported}

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        tags_raw = row["tags"] or "[]"
        try:
            tags = json.loads(tags_raw)
        except json.JSONDecodeError:
            tags = []
        return {
            "url": row["url"],
            "browser": row["browser"],
            "profile_name": row["profile_name"],
            "title": row["title"],
            "description": row["description"],
            "user_comment": row["user_comment"],
            "tags": tags if isinstance(tags, list) else [],
            "starred": row["starred"],
            "read_count": row["read_count"],
            "last_read_at": row["last_read_at"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

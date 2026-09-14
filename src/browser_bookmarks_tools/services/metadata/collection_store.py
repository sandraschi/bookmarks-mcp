"""SQLite store for named bookmark collections (e.g. "ai", "music", "politics").

Collections are first-class, CRUD-able entities - unlike the sidecar's old loose
`tags` JSON-array field, a collection has a stable id, can be renamed without
touching every member row, and deleting one only removes membership rows, never
the bookmarks themselves. Lives in the same SQLite file as
`SidecarMetadataStore` (see sidecar_db.py) but as sibling tables, since writes
here (create/rename/membership toggle) are a different, much lower-frequency
pattern than that store's per-bookmark upserts.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from browser_bookmarks_tools.services.metadata.sidecar_db import default_sidecar_path


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _scope(browser: str | None, profile_name: str | None) -> tuple[str, str]:
    return (browser or "").lower(), profile_name or ""


class CollectionStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or default_sidecar_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS collections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    color TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS bookmark_collections (
                    url TEXT NOT NULL,
                    browser TEXT NOT NULL DEFAULT '',
                    profile_name TEXT NOT NULL DEFAULT '',
                    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
                    added_at TEXT NOT NULL,
                    PRIMARY KEY (url, browser, profile_name, collection_id)
                );
                CREATE INDEX IF NOT EXISTS idx_bc_collection ON bookmark_collections(collection_id);
                CREATE INDEX IF NOT EXISTS idx_bc_scope ON bookmark_collections(url, browser, profile_name);
                """
            )

    # -- collection CRUD -----------------------------------------------------

    def create_collection(
        self,
        name: str,
        *,
        description: str | None = None,
        color: str | None = None,
    ) -> dict[str, Any]:
        name = name.strip()
        if not name:
            return {"success": False, "error": "name is required"}
        now = _now_iso()
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO collections (name, description, color, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, description, color, now, now),
                )
                collection_id = cur.lastrowid
        except sqlite3.IntegrityError:
            return {"success": False, "error": f"Collection '{name}' already exists"}
        return {"success": True, "collection": self.get_collection(collection_id)}

    def update_collection(
        self,
        collection_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        color: str | None = None,
    ) -> dict[str, Any]:
        existing = self.get_collection(collection_id)
        if existing is None:
            return {"success": False, "error": f"Collection {collection_id} not found"}
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE collections
                    SET name = COALESCE(?, name),
                        description = COALESCE(?, description),
                        color = COALESCE(?, color),
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (name.strip() if name else None, description, color, _now_iso(), collection_id),
                )
        except sqlite3.IntegrityError:
            return {"success": False, "error": f"Collection '{name}' already exists"}
        return {"success": True, "collection": self.get_collection(collection_id)}

    def delete_collection(self, collection_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        return {"success": True, "deleted": cur.rowcount > 0, "collection_id": collection_id}

    def get_collection(self, collection_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT c.*, COUNT(bc.url) AS member_count
                FROM collections c
                LEFT JOIN bookmark_collections bc ON bc.collection_id = c.id
                WHERE c.id = ?
                GROUP BY c.id
                """,
                (collection_id,),
            ).fetchone()
            return self._row_to_dict(row) if row else None

    def list_collections(self) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT c.*, COUNT(bc.url) AS member_count
                FROM collections c
                LEFT JOIN bookmark_collections bc ON bc.collection_id = c.id
                GROUP BY c.id
                ORDER BY c.name COLLATE NOCASE
                """
            ).fetchall()
        return {"success": True, "collections": [self._row_to_dict(row) for row in rows]}

    def get_or_create_collection(self, name: str) -> dict[str, Any]:
        name = name.strip()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM collections WHERE name = ?", (name,)).fetchone()
        if row:
            return {"success": True, "collection": self.get_collection(row["id"])}
        return self.create_collection(name)

    # -- membership -----------------------------------------------------------

    def add_to_collection(
        self,
        url: str,
        collection_id: int,
        *,
        browser: str | None = None,
        profile_name: str | None = None,
    ) -> dict[str, Any]:
        browser_key, profile_key = _scope(browser, profile_name)
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO bookmark_collections
                        (url, browser, profile_name, collection_id, added_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (url, browser_key, profile_key, collection_id, _now_iso()),
                )
        except sqlite3.IntegrityError as exc:
            return {"success": False, "error": str(exc)}
        return {"success": True, "url": url, "collection_id": collection_id}

    def bulk_add_to_collection(
        self,
        urls: list[str],
        collection_id: int,
        *,
        browser: str | None = None,
        profile_name: str | None = None,
    ) -> dict[str, Any]:
        browser_key, profile_key = _scope(browser, profile_name)
        now = _now_iso()
        rows = [(url, browser_key, profile_key, collection_id, now) for url in urls]
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO bookmark_collections
                    (url, browser, profile_name, collection_id, added_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )
        return {"success": True, "collection_id": collection_id, "count": len(rows)}

    def remove_from_collection(
        self,
        url: str,
        collection_id: int,
        *,
        browser: str | None = None,
        profile_name: str | None = None,
    ) -> dict[str, Any]:
        browser_key, profile_key = _scope(browser, profile_name)
        with self._connect() as conn:
            cur = conn.execute(
                """
                DELETE FROM bookmark_collections
                WHERE url = ? AND browser = ? AND profile_name = ? AND collection_id = ?
                """,
                (url, browser_key, profile_key, collection_id),
            )
        return {"success": True, "removed": cur.rowcount > 0, "url": url, "collection_id": collection_id}

    def get_collections_for_urls(
        self,
        urls: list[str],
        *,
        browser: str | None = None,
        profile_name: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Map each URL to the list of {id, name, color} collections it belongs to."""
        if not urls:
            return {}
        browser_key, profile_key = _scope(browser, profile_name)
        placeholders = ",".join("?" for _ in urls)
        out: dict[str, list[dict[str, Any]]] = {url: [] for url in urls}
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT bc.url, c.id, c.name, c.color
                FROM bookmark_collections bc
                JOIN collections c ON c.id = bc.collection_id
                WHERE bc.url IN ({placeholders}) AND bc.browser = ? AND bc.profile_name = ?
                """,  # noqa: S608
                [*urls, browser_key, profile_key],
            ).fetchall()
        for row in rows:
            out.setdefault(row["url"], []).append({"id": row["id"], "name": row["name"], "color": row["color"]})
        return out

    def list_urls_in_collection(
        self,
        collection_id: int,
        *,
        browser: str | None = None,
        profile_name: str | None = None,
    ) -> list[str]:
        browser_key, profile_key = _scope(browser, profile_name)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT url FROM bookmark_collections
                WHERE collection_id = ? AND browser = ? AND profile_name = ?
                """,
                (collection_id, browser_key, profile_key),
            ).fetchall()
        return [row["url"] for row in rows]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "color": row["color"],
            "member_count": row["member_count"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

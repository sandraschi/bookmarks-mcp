"""SQLite store for link-audit results (liveness snapshots, not a history log).

Sibling to SidecarMetadataStore/CollectionStore - same file
(default_sidecar_path()), same (url, browser, profile_name) scoping - but its
own table, since writes here are a bulk-overwrite-per-scan rather than the
low-frequency single-row edits those stores handle. Uses aiosqlite rather than
sync sqlite3: a scan can write thousands of rows while 30 concurrent HTTP
checks are in flight, and blocking the event loop for each one would stall
the scan itself.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite

from browser_bookmarks_tools.services.metadata.sidecar_db import default_sidecar_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS link_audit_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    browser TEXT NOT NULL DEFAULT '',
    profile_name TEXT NOT NULL DEFAULT '',
    title TEXT,
    folder_path TEXT,
    status TEXT NOT NULL,
    http_status INTEGER,
    final_url TEXT,
    checked_via TEXT NOT NULL DEFAULT 'direct',
    tier2_summary TEXT,
    suggested_tags TEXT,
    suggested_category TEXT,
    error_detail TEXT,
    job_id TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    UNIQUE(url, browser, profile_name)
);
CREATE INDEX IF NOT EXISTS idx_audit_scope ON link_audit_results(browser, profile_name);
CREATE INDEX IF NOT EXISTS idx_audit_status ON link_audit_results(status);
CREATE INDEX IF NOT EXISTS idx_audit_job ON link_audit_results(job_id);
"""


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _scope(browser: str | None, profile_name: str | None) -> tuple[str, str]:
    return (browser or "").lower(), profile_name or ""


class LinkAuditStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or default_sidecar_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def _init_schema(self, conn: aiosqlite.Connection) -> None:
        await conn.executescript(SCHEMA)

    async def bulk_upsert_results(self, job_id: str, rows: list[dict[str, Any]]) -> int:
        """Upsert a batch of check results. Each row: url, browser, profile_name, status,
        plus optional title/folder_path/http_status/final_url/checked_via/error_detail."""
        if not rows:
            return 0
        now = _now_iso()
        payload = [
            (
                row["url"],
                (row.get("browser") or "").lower(),
                row.get("profile_name") or "",
                row.get("title"),
                row.get("folder_path"),
                row["status"],
                row.get("http_status"),
                row.get("final_url"),
                row.get("checked_via", "direct"),
                row.get("error_detail"),
                job_id,
                now,
            )
            for row in rows
        ]
        async with aiosqlite.connect(self.db_path) as conn:
            await self._init_schema(conn)
            await conn.executemany(
                """
                INSERT INTO link_audit_results (
                    url, browser, profile_name, title, folder_path, status,
                    http_status, final_url, checked_via, error_detail, job_id, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url, browser, profile_name) DO UPDATE SET
                    title = excluded.title,
                    folder_path = excluded.folder_path,
                    status = excluded.status,
                    http_status = excluded.http_status,
                    final_url = excluded.final_url,
                    checked_via = excluded.checked_via,
                    error_detail = excluded.error_detail,
                    job_id = excluded.job_id,
                    checked_at = excluded.checked_at
                """,
                payload,
            )
            await conn.commit()
        return len(payload)

    async def get_results_for_urls(
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
        async with aiosqlite.connect(self.db_path) as conn:
            await self._init_schema(conn)
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                f"""
                SELECT * FROM link_audit_results
                WHERE url IN ({placeholders}) AND browser = ? AND profile_name = ?
                """,  # noqa: S608
                [*urls, browser_key, profile_key],
            ) as cursor:
                async for row in cursor:
                    out[row["url"]] = self._row_to_dict(row)
        return out

    async def list_results(
        self,
        *,
        browser: str | None = None,
        profile_name: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        browser_key, profile_key = _scope(browser, profile_name)
        clauses = ["browser = ?", "profile_name = ?"]
        params: list[Any] = [browser_key, profile_key]
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = " AND ".join(clauses)
        async with aiosqlite.connect(self.db_path) as conn:
            await self._init_schema(conn)
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                f"SELECT COUNT(*) as c FROM link_audit_results WHERE {where}",  # noqa: S608
                params,
            ) as cur:
                total = (await cur.fetchone())["c"]
            async with conn.execute(
                f"""
                SELECT * FROM link_audit_results WHERE {where}
                ORDER BY checked_at DESC LIMIT ? OFFSET ?
                """,  # noqa: S608
                [*params, limit, offset],
            ) as cur:
                rows = [self._row_to_dict(r) async for r in cur]
        return {
            "success": True,
            "results": rows,
            "total_count": total,
            "returned_count": len(rows),
            "pagination": {"limit": limit, "offset": offset, "has_more": offset + len(rows) < total},
        }

    @staticmethod
    def _row_to_dict(row: aiosqlite.Row) -> dict[str, Any]:
        return {
            "url": row["url"],
            "browser": row["browser"],
            "profile_name": row["profile_name"],
            "title": row["title"],
            "folder_path": row["folder_path"],
            "status": row["status"],
            "http_status": row["http_status"],
            "final_url": row["final_url"],
            "checked_via": row["checked_via"],
            "tier2_summary": row["tier2_summary"],
            "suggested_tags": row["suggested_tags"],
            "suggested_category": row["suggested_category"],
            "error_detail": row["error_detail"],
            "job_id": row["job_id"],
            "checked_at": row["checked_at"],
        }

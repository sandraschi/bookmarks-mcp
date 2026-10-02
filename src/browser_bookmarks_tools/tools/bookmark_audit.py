"""Concurrent link-audit portmanteau tool - the "check for dead links" action.

Scans a browser's bookmarks (or a specific URL subset) concurrently via
services/audit/link_checker.py, persists results to LinkAuditStore, and
reports live progress through services/audit/job_registry.py. Runs as a
background asyncio task started from `run_audit` and polled via
`get_audit_status` - this process runs FastMCP and FastAPI on one event
loop (see mcp_server.py), so a task created here keeps running after the
tool call returns.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Literal

from browser_bookmarks_tools.config.mcp_config import mcp
from browser_bookmarks_tools.services.audit import job_registry
from browser_bookmarks_tools.services.audit.audit_store import LinkAuditStore
from browser_bookmarks_tools.services.audit.link_checker import check_links_chunk
from browser_bookmarks_tools.tools.help_tools import HelpSystem

logger = logging.getLogger(__name__)

BookmarkAuditOperation = Literal[
    "run_audit",
    "get_audit_status",
    "list_audit_results",
    "get_results_for_urls",
    "cancel_audit",
]

CHUNK_SIZE = 50


async def _run_audit_job(
    job_id: str,
    *,
    browser: str,
    profile_name: str | None,
    candidates: list[dict[str, Any]],
    concurrency: int,
    per_host_limit: int,
) -> None:
    store = LinkAuditStore()
    try:
        for i in range(0, len(candidates), CHUNK_SIZE):
            if job_registry.is_cancelled(job_id):
                job_registry.finish_job(job_id, status="cancelled")
                return

            chunk = candidates[i : i + CHUNK_SIZE]
            urls = [b["url"] for b in chunk]
            results = await check_links_chunk(urls, concurrency=concurrency, per_host_limit=per_host_limit)

            rows: list[dict[str, Any]] = []
            counts_delta: dict[str, int] = {}
            for bookmark, result in zip(chunk, results, strict=True):
                status = result["status"]
                counts_delta[status] = counts_delta.get(status, 0) + 1
                rows.append(
                    {
                        "url": bookmark["url"],
                        "browser": browser,
                        "profile_name": profile_name or "",
                        "title": bookmark.get("title"),
                        "folder_path": bookmark.get("folder_path"),
                        "status": status,
                        "http_status": result["http_status"],
                        "final_url": result["final_url"],
                        "error_detail": result["error_detail"],
                    }
                )
            await store.bulk_upsert_results(job_id, rows)
            job_registry.update_progress(job_id, checked_delta=len(chunk), status_counts_delta=counts_delta)

        job_registry.finish_job(job_id, status="done")
    except Exception as exc:
        logger.error("Audit job %s failed: %s", job_id, exc, exc_info=True)
        job_registry.finish_job(job_id, status="error", error=str(exc))


async def _run_audit(
    browser: str | None,
    profile_name: str | None,
    urls: list[str] | None,
    folder_path: str | None,
    limit: int,
    concurrency: int,
    per_host_limit: int,
) -> dict[str, Any]:
    if not browser:
        return {"success": False, "error": "browser is required"}

    if urls:
        candidates = [{"url": u} for u in urls]
    else:
        from browser_bookmarks_tools.tools.bookmark_loader import load_browser_bookmarks

        loaded = await load_browser_bookmarks(browser, profile_name, limit=limit)
        if not loaded.get("success"):
            return {"success": False, "error": loaded.get("error") or "Failed to load bookmarks"}
        candidates = [b for b in (loaded.get("bookmarks") or []) if b.get("url")]
        if folder_path:
            needle = folder_path.lower()
            candidates = [b for b in candidates if needle in str(b.get("folder_path") or "").lower()]

    if not candidates:
        return {"success": False, "error": "No bookmarks matched the given scope"}

    job_id = job_registry.create_job(browser=browser, profile_name=profile_name, total=len(candidates))
    asyncio.create_task(  # noqa: RUF006 - fire-and-forget background job, tracked via job_registry
        _run_audit_job(
            job_id,
            browser=browser,
            profile_name=profile_name,
            candidates=candidates,
            concurrency=concurrency,
            per_host_limit=per_host_limit,
        )
    )
    return {"success": True, "job_id": job_id, "status": "running", "total": len(candidates)}


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False})
@HelpSystem.register_tool
async def bookmark_audit(
    operation: BookmarkAuditOperation,
    browser: str | None = None,
    profile_name: str | None = None,
    job_id: str | None = None,
    urls: list[str] | None = None,
    folder_path: str | None = None,
    status: str | None = None,
    limit: int = 5000,
    offset: int = 0,
    concurrency: int = 30,
    per_host_limit: int = 4,
) -> dict[str, Any]:
    """Concurrent dead-link audit for a browser's bookmarks, or a specific URL subset.

    Checks run with bounded concurrency (aiohttp connection pool, not one
    request at a time) and persist to the sidecar SQLite DB
    (~/.bookmarks-mcp/metadata.db), so results survive across scans and
    across the frontend's normal pagination.

    OPERATIONS:
    - run_audit(browser, profile_name?, urls?, folder_path?, limit?, concurrency?, per_host_limit?)
      Scope is either an explicit `urls` list (e.g. "recheck these N selected
      bookmarks") or the browser's full bookmark set, optionally filtered by
      `folder_path` substring. Starts a background job, returns immediately
      with job_id.
    - get_audit_status(job_id) - poll while running: status/checked/total/counts_by_status.
    - list_audit_results(browser, profile_name?, status?, limit?, offset?) - paginated, filterable by status.
    - get_results_for_urls(urls, browser, profile_name?) - status for a specific set of URLs
      (e.g. the bookmarks currently loaded on a page).
    - cancel_audit(job_id) - stop dispatching new chunks; in-flight requests finish.
    """
    limit = max(1, min(limit, 50_000))
    offset = max(0, offset)
    concurrency = max(1, min(concurrency, 100))
    per_host_limit = max(1, min(per_host_limit, concurrency))

    if operation == "run_audit":
        result = await _run_audit(browser, profile_name, urls, folder_path, limit, concurrency, per_host_limit)
        result["operation"] = operation
        return result

    if operation == "get_audit_status":
        if not job_id:
            return {"success": False, "operation": operation, "error": "job_id is required"}
        job = job_registry.get_job(job_id)
        if not job:
            return {"success": False, "operation": operation, "error": f"Unknown job_id: {job_id}"}
        return {"success": True, "operation": operation, "job": job}

    if operation == "list_audit_results":
        if not browser:
            return {"success": False, "operation": operation, "error": "browser is required"}
        result = await LinkAuditStore().list_results(
            browser=browser, profile_name=profile_name, status=status, limit=limit, offset=offset
        )
        result["operation"] = operation
        return result

    if operation == "get_results_for_urls":
        if not urls or not browser:
            return {"success": False, "operation": operation, "error": "urls and browser are required"}
        mapping = await LinkAuditStore().get_results_for_urls(urls, browser=browser, profile_name=profile_name)
        return {"success": True, "operation": operation, "results_by_url": mapping}

    if operation == "cancel_audit":
        if not job_id:
            return {"success": False, "operation": operation, "error": "job_id is required"}
        cancelled = job_registry.request_cancel(job_id)
        return {"success": True, "operation": operation, "cancelled": cancelled}

    return {
        "success": False,
        "operation": operation,
        "error": f"Unsupported operation: {operation}",
    }

"""Single-URL liveness classification, shared by the audit job runner.

Same HEAD-then-GET-fallback approach as
tools/universal_bookmark_ops.py::_check_one_link (milestone 1's concurrency
fix), but always returns a full classification (including the "ok" case)
since the audit pipeline persists one row per checked URL, not just the
broken/redirected ones.
"""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

BLOCKED_STATUSES = {401, 403, 429, 999}


async def check_link_status(session: aiohttp.ClientSession, url: str) -> dict[str, Any]:
    try:
        async with session.head(url, allow_redirects=True) as response:
            status = response.status
            final_url = str(response.url)
        if status in (403, 405, 999):
            async with session.get(url, allow_redirects=True) as response:
                status = response.status
                final_url = str(response.url)
    except TimeoutError:
        return {"status": "timeout", "http_status": None, "final_url": None, "error_detail": "timed out"}
    except aiohttp.ClientConnectorError as exc:
        return {"status": "dns_error", "http_status": None, "final_url": None, "error_detail": str(exc)}
    except Exception as exc:
        return {"status": "dead", "http_status": None, "final_url": None, "error_detail": str(exc)}

    if status in BLOCKED_STATUSES:
        return {"status": "blocked", "http_status": status, "final_url": final_url, "error_detail": None}
    if status >= 400:
        return {"status": "dead", "http_status": status, "final_url": final_url, "error_detail": None}
    if final_url != url:
        return {"status": "redirected", "http_status": status, "final_url": final_url, "error_detail": None}
    return {"status": "ok", "http_status": status, "final_url": final_url, "error_detail": None}


async def check_links_chunk(
    urls: list[str],
    *,
    concurrency: int = 30,
    per_host_limit: int = 4,
) -> list[dict[str, Any]]:
    """Check a chunk of URLs concurrently. Order of results matches `urls`."""
    connector = aiohttp.TCPConnector(limit=concurrency, limit_per_host=per_host_limit)
    timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=8)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        return await asyncio.gather(*(check_link_status(session, url) for url in urls))

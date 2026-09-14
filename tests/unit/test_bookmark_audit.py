import asyncio
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from browser_bookmarks_tools.tools.bookmark_audit import bookmark_audit


@pytest.fixture(autouse=True)
def _isolated_sidecar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BOOKMARKS_MCP_DATA_DIR", str(tmp_path))


async def _wait_for_job_done(job_id: str, timeout: float = 10.0) -> dict:
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        result = await bookmark_audit(operation="get_audit_status", job_id=job_id)
        job = result["job"]
        if job["status"] != "running":
            return job
        await asyncio.sleep(0.05)
    raise AssertionError(f"job {job_id} did not finish within {timeout}s")


async def test_run_audit_scoped_to_explicit_urls_end_to_end():
    app = web.Application()

    async def ok(_request):
        return web.Response(status=200)

    async def missing(_request):
        return web.Response(status=404)

    app.router.add_get("/ok", ok)
    app.router.add_get("/missing", missing)

    server = TestServer(app)
    await server.start_server()
    try:
        base = str(server.make_url("/")).rstrip("/")
        urls = [f"{base}/ok", f"{base}/missing"]

        started = await bookmark_audit(
            operation="run_audit",
            browser="chrome",
            profile_name="Default",
            urls=urls,
        )
        assert started["success"] is True
        job_id = started["job_id"]
        assert started["total"] == 2

        job = await _wait_for_job_done(job_id)
        assert job["status"] == "done"
        assert job["checked"] == 2
        assert job["counts_by_status"].get("ok") == 1
        assert job["counts_by_status"].get("dead") == 1

        results = await bookmark_audit(
            operation="get_results_for_urls", urls=urls, browser="chrome", profile_name="Default"
        )
        assert results["results_by_url"][f"{base}/ok"]["status"] == "ok"
        assert results["results_by_url"][f"{base}/missing"]["status"] == "dead"

        listed = await bookmark_audit(
            operation="list_audit_results", browser="chrome", profile_name="Default", status="dead"
        )
        assert listed["total_count"] == 1
        assert listed["results"][0]["url"] == f"{base}/missing"
    finally:
        await server.close()


async def test_run_audit_requires_browser():
    result = await bookmark_audit(operation="run_audit", urls=["https://a.example.com"])
    assert result["success"] is False


async def test_get_audit_status_unknown_job():
    result = await bookmark_audit(operation="get_audit_status", job_id="does-not-exist")
    assert result["success"] is False


async def test_cancel_audit_stops_further_progress():
    app = web.Application()

    async def slow_ok(_request):
        await asyncio.sleep(0.2)
        return web.Response(status=200)

    app.router.add_get("/slow", slow_ok)
    server = TestServer(app)
    await server.start_server()
    try:
        base = str(server.make_url("/")).rstrip("/")
        # More than one chunk's worth so cancellation has a chance to land between chunks.
        urls = [f"{base}/slow?i={i}" for i in range(120)]

        started = await bookmark_audit(operation="run_audit", browser="chrome", urls=urls, concurrency=5)
        job_id = started["job_id"]

        await asyncio.sleep(0.1)
        cancelled = await bookmark_audit(operation="cancel_audit", job_id=job_id)
        assert cancelled["cancelled"] is True

        job = await _wait_for_job_done(job_id, timeout=15.0)
        assert job["status"] == "cancelled"
        assert job["checked"] < len(urls)
    finally:
        await server.close()

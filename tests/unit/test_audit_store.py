from pathlib import Path

import pytest

from browser_bookmarks_tools.services.audit.audit_store import LinkAuditStore


@pytest.fixture
def store(tmp_path: Path) -> LinkAuditStore:
    return LinkAuditStore(db_path=tmp_path / "metadata.db")


async def test_bulk_upsert_and_get_results_for_urls(store: LinkAuditStore):
    rows = [
        {
            "url": "https://a.example.com",
            "browser": "chrome",
            "profile_name": "Default",
            "status": "ok",
            "http_status": 200,
        },
        {
            "url": "https://b.example.com",
            "browser": "chrome",
            "profile_name": "Default",
            "status": "dead",
            "http_status": 404,
        },
    ]
    count = await store.bulk_upsert_results("job1", rows)
    assert count == 2

    results = await store.get_results_for_urls(
        ["https://a.example.com", "https://b.example.com"], browser="chrome", profile_name="Default"
    )
    assert results["https://a.example.com"]["status"] == "ok"
    assert results["https://b.example.com"]["status"] == "dead"
    assert results["https://b.example.com"]["http_status"] == 404


async def test_upsert_overwrites_on_recheck(store: LinkAuditStore):
    await store.bulk_upsert_results(
        "job1",
        [{"url": "https://a.example.com", "browser": "chrome", "profile_name": "Default", "status": "dead"}],
    )
    await store.bulk_upsert_results(
        "job2",
        [{"url": "https://a.example.com", "browser": "chrome", "profile_name": "Default", "status": "ok"}],
    )
    results = await store.get_results_for_urls(["https://a.example.com"], browser="chrome", profile_name="Default")
    assert results["https://a.example.com"]["status"] == "ok"
    assert results["https://a.example.com"]["job_id"] == "job2"


async def test_list_results_filters_by_status_and_scope(store: LinkAuditStore):
    await store.bulk_upsert_results(
        "job1",
        [
            {"url": "https://a.example.com", "browser": "chrome", "profile_name": "Default", "status": "dead"},
            {"url": "https://b.example.com", "browser": "chrome", "profile_name": "Default", "status": "ok"},
            {"url": "https://c.example.com", "browser": "edge", "profile_name": "Default", "status": "dead"},
        ],
    )
    dead_chrome = await store.list_results(browser="chrome", profile_name="Default", status="dead")
    assert dead_chrome["total_count"] == 1
    assert dead_chrome["results"][0]["url"] == "https://a.example.com"

    all_chrome = await store.list_results(browser="chrome", profile_name="Default")
    assert all_chrome["total_count"] == 2


async def test_get_results_for_urls_empty_list_returns_empty(store: LinkAuditStore):
    assert await store.get_results_for_urls([]) == {}

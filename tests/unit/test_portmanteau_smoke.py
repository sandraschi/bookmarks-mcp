import asyncio
import pytest

from browser_bookmarks_tools.bookmarks.portmanteau import bookmarks


@pytest.mark.asyncio
async def test_smoke_create():
    result = await bookmarks("create", {"url": "https://example.com", "title": "Example"})
    assert result["status"] == "created"


@pytest.mark.asyncio
async def test_smoke_analyze():
    result = await bookmarks("analyze", {"text": "hello world"})
    assert result["status"] == "ok"

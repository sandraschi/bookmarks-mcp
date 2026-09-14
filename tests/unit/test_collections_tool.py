import os
from pathlib import Path

import pytest

os.environ.setdefault("BOOKMARKS_WEB_AUTH", "0")


@pytest.fixture(autouse=True)
def _isolated_sidecar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BOOKMARKS_MCP_DATA_DIR", str(tmp_path))


async def test_collections_tool_crud_and_membership():
    from browser_bookmarks_tools.tools.collections import collections

    created = await collections(operation="create_collection", name="ai", description="AI stuff")
    assert created["success"] is True
    collection_id = created["collection"]["id"]

    listed = await collections(operation="list_collections")
    assert listed["success"] is True
    assert any(c["id"] == collection_id for c in listed["collections"])

    added = await collections(
        operation="bulk_add_to_collection",
        urls=["https://a.example.com", "https://b.example.com"],
        collection_id=collection_id,
        browser="chrome",
        profile_name="Default",
    )
    assert added["success"] is True
    assert added["count"] == 2

    membership = await collections(
        operation="get_collections_for_urls",
        urls=["https://a.example.com"],
        browser="chrome",
        profile_name="Default",
    )
    assert membership["success"] is True
    assert membership["collections_by_url"]["https://a.example.com"][0]["name"] == "ai"

    removed = await collections(
        operation="remove_from_collection",
        url="https://a.example.com",
        collection_id=collection_id,
        browser="chrome",
        profile_name="Default",
    )
    assert removed["success"] is True

    renamed = await collections(operation="update_collection", collection_id=collection_id, name="ai-tools")
    assert renamed["success"] is True
    assert renamed["collection"]["name"] == "ai-tools"

    deleted = await collections(operation="delete_collection", collection_id=collection_id)
    assert deleted["success"] is True
    assert deleted["deleted"] is True


async def test_collections_tool_requires_name():
    from browser_bookmarks_tools.tools.collections import collections

    result = await collections(operation="create_collection")
    assert result["success"] is False


async def test_collections_tool_unknown_operation():
    from browser_bookmarks_tools.tools.collections import collections

    result = await collections(operation="not_a_real_op")  # type: ignore[arg-type]
    assert result["success"] is False
    assert "Unsupported operation" in result["error"]

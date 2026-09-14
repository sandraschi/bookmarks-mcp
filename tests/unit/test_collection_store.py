from pathlib import Path

import pytest

from browser_bookmarks_tools.services.metadata.collection_store import CollectionStore


@pytest.fixture
def store(tmp_path: Path) -> CollectionStore:
    return CollectionStore(db_path=tmp_path / "metadata.db")


def test_create_and_list_collections(store: CollectionStore):
    created = store.create_collection("ai", description="AI links", color="#22c55e")
    assert created["success"] is True
    assert created["collection"]["name"] == "ai"
    assert created["collection"]["member_count"] == 0

    dup = store.create_collection("ai")
    assert dup["success"] is False

    listed = store.list_collections()
    assert listed["success"] is True
    assert [c["name"] for c in listed["collections"]] == ["ai"]


def test_rename_does_not_touch_members(store: CollectionStore):
    coll = store.create_collection("politics")["collection"]
    store.add_to_collection("https://a.example.com", coll["id"], browser="chrome", profile_name="Default")
    store.add_to_collection("https://b.example.com", coll["id"], browser="chrome", profile_name="Default")

    renamed = store.update_collection(coll["id"], name="current-events")
    assert renamed["success"] is True
    assert renamed["collection"]["name"] == "current-events"
    assert renamed["collection"]["member_count"] == 2


def test_delete_collection_removes_membership_not_bookmarks(store: CollectionStore):
    coll = store.create_collection("music")["collection"]
    store.add_to_collection("https://a.example.com", coll["id"], browser="chrome", profile_name="Default")

    deleted = store.delete_collection(coll["id"])
    assert deleted["success"] is True
    assert deleted["deleted"] is True

    mapping = store.get_collections_for_urls(["https://a.example.com"], browser="chrome", profile_name="Default")
    assert mapping["https://a.example.com"] == []


def test_bulk_add_and_get_collections_for_urls(store: CollectionStore):
    coll = store.create_collection("ai")["collection"]
    urls = ["https://a.example.com", "https://b.example.com"]
    result = store.bulk_add_to_collection(urls, coll["id"], browser="chrome", profile_name="Default")
    assert result["success"] is True
    assert result["count"] == 2

    mapping = store.get_collections_for_urls(urls, browser="chrome", profile_name="Default")
    assert {c["name"] for c in mapping["https://a.example.com"]} == {"ai"}
    assert {c["name"] for c in mapping["https://b.example.com"]} == {"ai"}


def test_remove_from_collection(store: CollectionStore):
    coll = store.create_collection("ai")["collection"]
    store.add_to_collection("https://a.example.com", coll["id"], browser="chrome", profile_name="Default")

    removed = store.remove_from_collection(
        "https://a.example.com", coll["id"], browser="chrome", profile_name="Default"
    )
    assert removed["success"] is True
    assert removed["removed"] is True

    mapping = store.get_collections_for_urls(["https://a.example.com"], browser="chrome", profile_name="Default")
    assert mapping["https://a.example.com"] == []


def test_scoping_is_per_browser_profile(store: CollectionStore):
    coll = store.create_collection("ai")["collection"]
    store.add_to_collection("https://a.example.com", coll["id"], browser="chrome", profile_name="Default")

    chrome_map = store.get_collections_for_urls(["https://a.example.com"], browser="chrome", profile_name="Default")
    edge_map = store.get_collections_for_urls(["https://a.example.com"], browser="edge", profile_name="Default")

    assert len(chrome_map["https://a.example.com"]) == 1
    assert edge_map["https://a.example.com"] == []

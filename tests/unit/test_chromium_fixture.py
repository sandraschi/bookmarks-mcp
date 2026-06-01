import json
from pathlib import Path

from browser_bookmarks_tools.web import _chromium_node_to_tree

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "chromium_bookmarks.json"


def test_chromium_fixture_has_urls():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    bar = data["roots"]["bookmark_bar"]
    urls = [c for c in bar["children"] if c.get("type") == "url"]
    assert len(urls) == 1
    assert urls[0]["url"] == "https://example.com/docs"


def test_chromium_node_to_tree_maps_fixture():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    bar = data["roots"]["bookmark_bar"]
    mapped = _chromium_node_to_tree(bar, "bookmark_bar")
    assert mapped is not None
    assert mapped["type"] == "folder"
    assert len(mapped["children"]) >= 2
    bookmark = next(c for c in mapped["children"] if c["type"] == "bookmark")
    assert bookmark["url"] == "https://example.com/docs"

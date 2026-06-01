import plistlib
from pathlib import Path

import pytest

from browser_bookmarks_tools.services.browser.safari_plist import (
    delete_safari_bookmark,
    parse_safari_bookmarks,
    read_safari_bookmarks,
    write_safari_bookmark,
)


def _sample_plist() -> dict:
    return {
        "WebBookmarkType": "WebBookmarkTypeList",
        "Title": "BookmarksBar",
        "Children": [
            {
                "WebBookmarkType": "WebBookmarkTypeLeaf",
                "URIDictionary": {"title": "Example", "URLString": "https://example.com"},
            },
            {
                "WebBookmarkType": "WebBookmarkTypeList",
                "Title": "Dev",
                "Children": [
                    {
                        "WebBookmarkType": "WebBookmarkTypeLeaf",
                        "URIDictionary": {"title": "Docs", "URLString": "https://docs.example.com"},
                    }
                ],
            },
        ],
    }


@pytest.fixture
def safari_plist_path(tmp_path: Path) -> Path:
    path = tmp_path / "Bookmarks.plist"
    with path.open("wb") as handle:
        plistlib.dump(_sample_plist(), handle, fmt=plistlib.FMT_BINARY)
    return path


def test_parse_safari_bookmarks(safari_plist_path: Path):
    with safari_plist_path.open("rb") as handle:
        data = plistlib.load(handle)
    bookmarks = parse_safari_bookmarks(data)
    assert len(bookmarks) == 2
    urls = {item["url"] for item in bookmarks}
    assert "https://example.com" in urls
    assert "https://docs.example.com" in urls
    dev = next(item for item in bookmarks if item["url"] == "https://docs.example.com")
    assert dev["folder_path"] == "Dev"


def test_read_safari_bookmarks_with_explicit_path(safari_plist_path: Path):
    result = read_safari_bookmarks(safari_plist_path)
    assert result["status"] == "success"
    assert result["count"] == 2


def test_write_and_delete_safari_bookmark(safari_plist_path: Path):
    add_result = write_safari_bookmark(
        safari_plist_path,
        title="New",
        url="https://new.example.com",
        folder="Dev",
    )
    assert add_result["status"] == "success"

    read_result = read_safari_bookmarks(safari_plist_path)
    assert read_result["count"] == 3

    delete_result = delete_safari_bookmark(safari_plist_path, url="https://new.example.com")
    assert delete_result["status"] == "success"

    read_after = read_safari_bookmarks(safari_plist_path)
    assert read_after["count"] == 2

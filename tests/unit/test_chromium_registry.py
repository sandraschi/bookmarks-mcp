import json
from pathlib import Path

import pytest

from browser_bookmarks_tools.services.browser.chromium_manager import ChromiumManager
from browser_bookmarks_tools.services.browser.chromium_registry import (
    get_chromium_spec,
    is_chromium_browser,
    list_chromium_browser_ids,
)
from browser_bookmarks_tools.tools.chromium import (
    add_chromium_bookmark,
    delete_chromium_bookmark,
    list_chromium_bookmarks,
    search_chromium_bookmarks,
)

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "chromium_bookmarks.json"


def test_registry_includes_core_browsers():
    ids = list_chromium_browser_ids()
    assert "chrome" in ids
    assert "edge" in ids
    assert "brave" in ids
    assert "opera" in ids
    assert "vivaldi" in ids
    assert "comet" in ids
    assert "dia" in ids


def test_is_chromium_browser():
    assert is_chromium_browser("chrome")
    assert is_chromium_browser("opera_gx")
    assert not is_chromium_browser("firefox")
    assert not is_chromium_browser("safari")


def test_get_chromium_spec_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown Chromium browser"):
        get_chromium_spec("internet_explorer")


@pytest.mark.asyncio
async def test_list_chromium_bookmarks_via_override_path():
    result = await list_chromium_bookmarks("chrome", bookmarks_path=str(FIXTURE))
    assert result["success"] is True
    assert result["count"] == 2
    assert result["browser"] == "chrome"
    assert result["profile_name"] == "Default"


@pytest.mark.asyncio
async def test_search_chromium_bookmarks_fixture(tmp_path: Path):
    target = tmp_path / "Bookmarks"
    target.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    result = await search_chromium_bookmarks(
        "chrome",
        "nested",
        bookmarks_path=str(target),
    )
    assert result["success"] is True
    assert result["total_matches"] == 1
    assert result["results"][0]["url"] == "https://example.com/nested"


@pytest.mark.asyncio
async def test_chromium_crud_roundtrip(tmp_path: Path):
    target = tmp_path / "Bookmarks"
    target.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    added = await add_chromium_bookmark(
        "chrome",
        title="Phase 1 Test",
        url="https://example.com/phase1",
        bookmarks_path=str(target),
    )
    assert added["success"] is True

    listed = await list_chromium_bookmarks("chrome", bookmarks_path=str(target))
    urls = {item["url"] for item in listed["bookmarks"]}
    assert "https://example.com/phase1" in urls

    deleted = await delete_chromium_bookmark(
        "chrome",
        url="https://example.com/phase1",
        bookmarks_path=str(target),
    )
    assert deleted["success"] is True

    listed_after = await list_chromium_bookmarks("chrome", bookmarks_path=str(target))
    urls_after = {item["url"] for item in listed_after["bookmarks"]}
    assert "https://example.com/phase1" not in urls_after


@pytest.mark.asyncio
async def test_chromium_manager_parses_fixture(tmp_path: Path):
    user_data = tmp_path / "User Data" / "Default"
    user_data.mkdir(parents=True)
    bookmarks = user_data / "Bookmarks"
    bookmarks.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    manager = ChromiumManager("chrome")
    manager.user_data_dir = tmp_path / "User Data"

    parsed = await manager.parse_bookmarks("Default")
    assert len(parsed) == 2
    assert parsed[0]["url"]


@pytest.mark.asyncio
async def test_chromium_manager_profile_discovery(tmp_path: Path):
    user_data = tmp_path / "User Data"
    for profile in ("Default", "Profile 1"):
        profile_dir = user_data / profile
        profile_dir.mkdir(parents=True)
        (profile_dir / "Bookmarks").write_text(
            json.dumps({"checksum": "x", "roots": {}, "version": 1}),
            encoding="utf-8",
        )

    manager = ChromiumManager("chrome")
    manager.user_data_dir = user_data
    profiles = await manager.get_profiles()
    assert profiles == ["Default", "Profile 1"]

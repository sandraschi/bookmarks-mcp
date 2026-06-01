import pytest

from browser_bookmarks_tools.tools.sync_tree import sync_bookmarks_with_folders


@pytest.mark.asyncio
async def test_sync_dry_run_preserves_folder_metadata(monkeypatch: pytest.MonkeyPatch):
    async def fake_load(browser: str, profile_name: str | None = None, **kwargs):
        return {
            "success": True,
            "browser": browser,
            "bookmarks": [
                {"title": "Docs", "url": "https://docs.example.com", "folder_path": "Work/Dev"},
                {"title": "Home", "url": "https://example.com", "folder_path": ""},
            ],
        }

    monkeypatch.setattr(
        "browser_bookmarks_tools.tools.sync_tree.load_browser_bookmarks",
        fake_load,
    )

    result = await sync_bookmarks_with_folders(
        source_browser="firefox",
        target_browser="chrome",
        dry_run=True,
        preserve_folders=True,
    )

    assert result["status"] == "planned"
    assert result["count"] == 2
    assert result["folder_support_on_target"] is True
    assert result["sample"][0]["folder_path"] == "Work/Dev"


@pytest.mark.asyncio
async def test_sync_dry_run_gecko_target_no_folder_support(monkeypatch: pytest.MonkeyPatch):
    async def fake_load(browser: str, profile_name: str | None = None, **kwargs):
        return {
            "success": True,
            "browser": browser,
            "bookmarks": [
                {"title": "Docs", "url": "https://docs.example.com", "folder_path": "Work/Dev"},
            ],
        }

    monkeypatch.setattr(
        "browser_bookmarks_tools.tools.sync_tree.load_browser_bookmarks",
        fake_load,
    )

    result = await sync_bookmarks_with_folders(
        source_browser="chrome",
        target_browser="firefox",
        dry_run=True,
        preserve_folders=True,
    )

    assert result["status"] == "planned"
    assert result["folder_support_on_target"] is False

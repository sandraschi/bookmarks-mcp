import pytest

from browser_bookmarks_tools.services.backup_service import batch_backup_profiles, batch_restore_profiles
from browser_bookmarks_tools.tools.prefab_apps import _rows_for_bookmarks


def test_rows_for_bookmarks_includes_metadata():
    rows = _rows_for_bookmarks(
        [
            {
                "title": "Docs",
                "url": "https://docs.example.com",
                "folder_path": "Work",
                "metadata": {"tags": ["ref"], "starred": 3},
            }
        ]
    )
    assert rows[0]["tags"] == "ref"
    assert rows[0]["starred"] == 3


@pytest.mark.asyncio
async def test_batch_backup_dry_run():
    result = await batch_backup_profiles(dry_run=True)
    assert result["success"] is True
    assert result["status"] == "planned"
    assert result["count"] >= 1


@pytest.mark.asyncio
async def test_batch_restore_dry_run():
    plan = [{"browser": "chrome", "profile_name": "Default", "backup_file": "/tmp/x.zip"}]
    result = await batch_restore_profiles(plan, dry_run=True)
    assert result["success"] is True
    assert result["count"] == 1

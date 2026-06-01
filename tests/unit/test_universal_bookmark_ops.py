import json
from datetime import UTC, datetime
from pathlib import Path

from browser_bookmarks_tools.tools.universal_bookmark_ops import (
    export_bookmarks_to_file,
    find_duplicates_from_bookmarks,
    find_old_bookmarks_from_list,
    get_bookmark_stats_from_list,
)


def _sample_bookmarks() -> list[dict]:
    now = datetime.now(tz=UTC).timestamp()
    old = now - (400 * 86400)
    return [
        {"title": "A", "url": "https://a.example.com", "folder_path": "Work", "added_timestamp": old},
        {"title": "A dup", "url": "https://a.example.com", "folder_path": "Work", "added_timestamp": now},
        {"title": "B", "url": "https://b.example.com", "folder_path": "Personal", "added_timestamp": now},
        {"title": "Unknown", "url": "https://unknown.example.com", "folder_path": ""},
    ]


def test_find_duplicates_from_bookmarks():
    result = find_duplicates_from_bookmarks(_sample_bookmarks())
    assert result["success"] is True
    assert result["total_duplicates"] == 1
    assert result["duplicates"][0]["url"] == "https://a.example.com"


def test_find_old_bookmarks_from_list():
    result = find_old_bookmarks_from_list(_sample_bookmarks(), age_days=365)
    assert result["success"] is True
    assert result["count"] == 1
    assert result["unknown_age_count"] == 1


def test_get_bookmark_stats_from_list():
    result = get_bookmark_stats_from_list(_sample_bookmarks())
    assert result["success"] is True
    assert result["stats"]["total_bookmarks"] == 4
    assert result["stats"]["folders"] == 3


def test_export_bookmarks_to_file_json(tmp_path: Path):
    output = tmp_path / "export.json"
    result = export_bookmarks_to_file(_sample_bookmarks(), "json", str(output))
    assert result["success"] is True
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload) == 4
    assert payload[0]["url"] == "https://a.example.com"

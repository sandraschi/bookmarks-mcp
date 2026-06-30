from pathlib import Path

from browser_bookmarks_tools.services.bookmark_import import parse_bookmark_file, parse_netscape_html
from browser_bookmarks_tools.services.metadata.sidecar_db import SidecarMetadataStore

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_parse_netscape_html_fixture():
    content = (FIXTURES / "netscape_sample.html").read_text(encoding="utf-8")
    bookmarks = parse_netscape_html(content)
    assert len(bookmarks) == 2
    docs = next(item for item in bookmarks if item["url"] == "https://docs.example.com")
    assert docs["folder_path"] == "Work"
    assert "docs" in docs["tags"]


def test_parse_bookmark_file_auto(tmp_path):
    path = tmp_path / "bookmarks.html"
    path.write_text((FIXTURES / "netscape_sample.html").read_text(encoding="utf-8"), encoding="utf-8")
    result = parse_bookmark_file(path, "auto")
    assert result["success"] is True
    assert result["count"] == 2


def test_sidecar_metadata_crud(tmp_path):
    db_path = tmp_path / "metadata.db"
    store = SidecarMetadataStore(db_path)

    saved = store.upsert(
        "https://example.com",
        browser="chrome",
        profile_name="Default",
        description="A useful site",
        user_comment="Read weekly",
        tags=["reference"],
        starred=4,
    )
    assert saved["success"] is True

    fetched = store.get("https://example.com", browser="chrome", profile_name="Default")
    assert fetched is not None
    assert fetched["description"] == "A useful site"
    assert fetched["starred"] == 4
    assert "reference" in fetched["tags"]

    read = store.record_read("https://example.com", browser="chrome", profile_name="Default")
    assert read["metadata"]["read_count"] == 1
    assert read["metadata"]["last_read_at"]

    listed = store.list_metadata(browser="chrome", tag="reference")
    assert listed["total_count"] == 1

    deleted = store.delete("https://example.com", browser="chrome", profile_name="Default")
    assert deleted["deleted"] is True

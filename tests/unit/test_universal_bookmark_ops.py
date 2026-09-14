import json
from datetime import UTC, datetime
from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import TestServer

from browser_bookmarks_tools.tools.universal_bookmark_ops import (
    export_bookmarks_to_file,
    find_broken_links_from_list,
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


async def test_find_broken_links_from_list_concurrent_and_head_fallback():
    app = web.Application()

    async def ok(_request):
        return web.Response(status=200, text="ok")

    async def missing(_request):
        return web.Response(status=404)

    async def redirect(_request):
        raise web.HTTPFound("/ok")

    async def head_blocked(request):
        if request.method == "HEAD":
            return web.Response(status=403)
        return web.Response(status=200, text="ok via get")

    app.router.add_get("/ok", ok)
    app.router.add_get("/missing", missing)
    app.router.add_get("/redirect", redirect)
    app.router.add_route("*", "/head-blocked", head_blocked)

    server = TestServer(app)
    await server.start_server()
    try:
        base = str(server.make_url("/")).rstrip("/")
        bookmarks = [
            {"title": "OK", "url": f"{base}/ok"},
            {"title": "Missing", "url": f"{base}/missing"},
            {"title": "Redirect", "url": f"{base}/redirect"},
            {"title": "HEAD blocked", "url": f"{base}/head-blocked"},
        ]

        result = await find_broken_links_from_list(bookmarks, check_links=True)

        assert result["success"] is True
        assert result["checked"] == 4
        broken_urls = {item["url"] for item in result["broken_links"]}
        redirected_urls = {item["url"] for item in result["redirected_links"]}
        assert f"{base}/missing" in broken_urls
        assert f"{base}/redirect" in redirected_urls
        # HEAD returns 403 here but GET succeeds - the fallback must kick in,
        # so this URL should be neither broken nor redirected.
        assert f"{base}/head-blocked" not in broken_urls
        assert f"{base}/head-blocked" not in redirected_urls
        assert f"{base}/ok" not in broken_urls
    finally:
        await server.close()

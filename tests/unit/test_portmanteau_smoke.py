import pytest

from browser_bookmarks_tools.mcp_server import BookmarksMCPServer


@pytest.mark.asyncio
async def test_multi_portmanteau_tools_registered():
    server = BookmarksMCPServer()
    from fastmcp.utilities.inspect import inspect_fastmcp

    info = await inspect_fastmcp(server.mcp)
    names = {t.name for t in info.tools or []}
    expected = {
        "browser_bookmarks",
        "firefox_profiles",
        "firefox_backup",
        "firefox_curated",
        "firefox_tagging",
        "firefox_utils",
        "sync_bookmarks",
        "chrome_profiles",
        "ai_bookmark_portmanteau",
    }
    missing = expected - names
    assert not missing, f"Missing tools: {missing}; got {sorted(names)}"

from aiohttp import web
from aiohttp.test_utils import TestServer

from browser_bookmarks_tools.services.audit.link_checker import check_link_status, check_links_chunk


async def test_check_link_status_classifies_ok_dead_redirect_blocked():
    app = web.Application()

    async def ok(_request):
        return web.Response(status=200, text="ok")

    async def missing(_request):
        return web.Response(status=404)

    async def redirect(_request):
        raise web.HTTPFound("/ok")

    async def blocked(_request):
        return web.Response(status=403)

    app.router.add_get("/ok", ok)
    app.router.add_get("/missing", missing)
    app.router.add_get("/redirect", redirect)
    app.router.add_route("*", "/blocked", blocked)

    server = TestServer(app)
    await server.start_server()
    try:
        base = str(server.make_url("/")).rstrip("/")
        import aiohttp

        async with aiohttp.ClientSession() as session:
            ok_result = await check_link_status(session, f"{base}/ok")
            dead_result = await check_link_status(session, f"{base}/missing")
            redirect_result = await check_link_status(session, f"{base}/redirect")
            blocked_result = await check_link_status(session, f"{base}/blocked")

        assert ok_result["status"] == "ok"
        assert dead_result["status"] == "dead"
        assert dead_result["http_status"] == 404
        assert redirect_result["status"] == "redirected"
        # blocked/* has no GET handler that succeeds (route is "*" -> 403 for any method),
        # so HEAD 403 retried as GET still comes back 403 -> classified blocked.
        assert blocked_result["status"] == "blocked"
    finally:
        await server.close()


async def test_check_link_status_dns_error_on_bad_host():
    import aiohttp

    async with aiohttp.ClientSession() as session:
        result = await check_link_status(session, "http://this-host-does-not-exist.invalid/")
    assert result["status"] == "dns_error"
    assert result["error_detail"]


async def test_check_links_chunk_preserves_order():
    app = web.Application()

    async def ok(_request):
        return web.Response(status=200)

    async def missing(_request):
        return web.Response(status=404)

    app.router.add_get("/a", ok)
    app.router.add_get("/b", missing)

    server = TestServer(app)
    await server.start_server()
    try:
        base = str(server.make_url("/")).rstrip("/")
        urls = [f"{base}/a", f"{base}/b", f"{base}/a"]
        results = await check_links_chunk(urls, concurrency=5, per_host_limit=5)
        assert [r["status"] for r in results] == ["ok", "dead", "ok"]
    finally:
        await server.close()

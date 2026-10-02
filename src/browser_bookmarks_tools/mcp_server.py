"""FastMCP server - multi-portmanteau bookmark tools."""

import logging
import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from browser_bookmarks_tools.config.mcp_config import get_mcp
from browser_bookmarks_tools.transport import run_server
from browser_bookmarks_tools.web import setup_webapp

logger = logging.getLogger(__name__)


def _register_tools() -> None:
    """Import tool modules so @mcp.tool decorators run."""

    from browser_bookmarks_tools.tools import (  # noqa: F401
        backup_restore,
        bookmark_audit,
        bookmark_metadata,
        browser_bookmarks,
        chrome_profiles,
        collections,
        firefox_backup,
        firefox_curated,
        firefox_profiles,
        firefox_tagging,
        firefox_utils,
        prefab_apps,
        server_tools,
        sync_tools,
    )
    from browser_bookmarks_tools.tools.firefox import ai_portmanteau  # noqa: F401


class BookmarksMCPServer:
    def __init__(self) -> None:

        self.mcp = get_mcp()

        _register_tools()


def _build_web_app():

    mcp = get_mcp()

    _register_tools()

    app = FastAPI(title="bookmarks-mcp")

    _bookmarks_tauri = os.environ.get("BOOKMARKS_TAURI", "").lower() in ("1", "true", "yes")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:10803",
            "http://localhost:10803",
            "http://goliath:10803",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "tauri://localhost",
        ],
        allow_origin_regex=r"https?://tauri\.localhost(:\d+)?" if _bookmarks_tauri else None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():

        return {"status": "ok", "server": "bookmarks-mcp"}

    @app.get("/api/capabilities")
    async def capabilities():
        """Standard fleet shape for webapp discovery."""
        try:
            from importlib.metadata import version

            _pkg_version = version("bookmarks-mcp")
        except Exception:
            _pkg_version = "unknown"
        tool_names = sorted(t.name for t in await mcp.list_tools())
        return {
            "service": "bookmarks-mcp",
            "version": _pkg_version,
            "status": "ok",
            "tool_count": len(tool_names),
            "tools": tool_names,
            "endpoints": [
                "/health",
                "/api/capabilities",
                "/api/v1/diagnostics",
                "/mcp",
            ],
            "transports": ["http", "stdio"],
        }

    @app.get("/api/v1/diagnostics")
    async def diagnostics():
        try:
            import psutil

            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
        except ImportError:
            cpu = mem = disk = None
        try:
            _tool_total = len(await mcp.list_tools())
        except Exception:
            _tool_total = 0
        return {
            "success": True,
            "backend": {"port": 10803, "status": "running"},
            "system": {"cpu_percent": cpu, "memory_percent": mem, "disk_percent": disk},
            "tools": {"total": _tool_total},
            "cua_status": {"tesseract_available": False, "window_found": False},
        }

    setup_webapp(app, mcp_app=mcp)

    return app


web_app = _build_web_app()


def main() -> None:

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    BookmarksMCPServer()

    if os.getenv("MCP_TRANSPORT") == "http" or "--http" in sys.argv:
        port = int(os.getenv("MCP_PORT", "10803"))

        host = os.getenv("MCP_HOST", "127.0.0.1")

        logger.info("Starting bookmarks-mcp HTTP bridge on %s:%s", host, port)

        uvicorn.run(web_app, host=host, port=port)

    else:
        run_server(get_mcp(), server_name="bookmarks-mcp")


if __name__ == "__main__":
    main()

"""FastMCP server — multi-portmanteau bookmark tools."""

import logging
import os
import sys

import uvicorn
from browser_bookmarks_tools.config.mcp_config import get_mcp
from browser_bookmarks_tools.transport import run_server
from browser_bookmarks_tools.web import setup_webapp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


def _register_tools() -> None:
    """Import tool modules so @mcp.tool decorators run."""

    from browser_bookmarks_tools.tools import (  # noqa: F401
        backup_restore,
        bookmark_metadata,
        browser_bookmarks,
        chrome_profiles,
        firefox_backup,
        firefox_curated,
        firefox_profiles,
        firefox_tagging,
        firefox_utils,
        prefab_apps,
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

"""Central FastMCP configuration for bookmarks-mcp."""

import logging
import os

from fastmcp import FastMCP
from fastmcp.server import create_proxy

logger = logging.getLogger(__name__)

mcp = FastMCP(name="bookmarks-mcp", version="0.2.0")

_bridge_urls = os.getenv("MCP_BRIDGE_URLS", "")
if _bridge_urls:
    for url in _bridge_urls.split(","):
        url = url.strip()
        if url:
            try:
                mcp.add_provider(create_proxy(url))
            except Exception:
                logger.debug("Skipping bridge URL: %s", url)


def get_mcp() -> FastMCP:
    return mcp

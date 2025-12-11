"""Main entry point for the Browser Bookmarks MCP server with stdio support."""

import sys

from .mcp_server import mcp

if __name__ == "__main__":
    mcp.run()

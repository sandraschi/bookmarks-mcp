from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from .bookmarks.portmanteau import bookmarks
from .transport import run_server
import os
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .auth import authenticate
from .web import setup_webapp

mcp = FastMCP("bookmarks-mcp", version="0.1.0")


@mcp.tool()
async def bookmarks_tool(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Unified bookmarks tool for CRUD, organization, sync, and AI helpers."""
    return await bookmarks(operation=operation, payload=payload)


# FastAPI Bridge
web_app = FastAPI(title="Bookmark Master Web Bridge", dependencies=[Depends(authenticate)])

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@web_app.get("/api/status")
async def get_status():
    return {"status": "online", "server": "bookmarks-mcp", "version": "0.1.0"}


# Setup static file serving
setup_webapp(web_app, mcp_app=mcp)


def main():
    """Main entry point with unified transport handling."""
    if os.getenv("MCP_TRANSPORT") == "http" or "--http" in os.sys.argv:
        port = int(os.getenv("MCP_PORT", "10800"))
        print(f"Starting Bookmark Master Web Bridge on port {port}...")
        uvicorn.run(web_app, host="0.0.0.0", port=port)
    else:
        run_server(mcp, server_name="bookmarks-mcp")


if __name__ == "__main__":
    main()

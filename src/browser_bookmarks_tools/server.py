"""
ASGI entry point for uvicorn (web_sota backend).

Use: uvicorn browser_bookmarks_tools.server:app --host 127.0.0.1 --port ...
"""

from browser_bookmarks_tools.mcp_server import web_app as app

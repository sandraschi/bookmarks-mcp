from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from .bookmarks.portmanteau import bookmarks

mcp = FastMCP()

@mcp.tool()
async def bookmarks_tool(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Unified bookmarks tool for CRUD, organization, sync, and AI helpers.

    Parameters:
        operation: One of create, read, update, delete, organize, sync, analyze, tag, summarize
        payload: Operation-specific parameters (e.g., url, title, folder, browser)

    Returns:
        dict: Result object with operation-specific fields

    Usage:
        - Create: operation='create', payload={'url': '...', 'title': '...', 'tags': []}
        - Organize: operation='organize', payload={'rule': 'group-by-domain'}
        - Sync: operation='sync', payload={'source': 'firefox', 'target': 'chrome'}
        - Analyze: operation='analyze', payload={'text': '...'}

    Examples:
        See docs and tests for examples.

    Notes:
        - All operations are async.
        - Firefox is the primary target.

    See Also:
        - browser_bookmarks_tools.bookmarks.manager
        - browser_bookmarks_tools.bookmarks.organizer
        - browser_bookmarks_tools.bookmarks.sync
    """
    return await bookmarks(operation=operation, payload=payload)

if __name__ == "__main__":
    mcp.run()

"""Server administration tools for bookmarks-mcp."""

import os
import signal

from browser_bookmarks_tools.config.mcp_config import mcp
from browser_bookmarks_tools.tools.help_tools import HelpSystem

_DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}


@mcp.tool(annotations=_DESTRUCTIVE)
@HelpSystem.register_tool
async def bookmarks_shutdown(confirmed: bool = False) -> str:
    """Shut down the bookmarks-mcp server process.

    ## Return Format
    Confirmation prompt or termination notice string

    ## Examples
    ```python
    await call_tool("bookmarks_shutdown", {"confirmed": True})
    ```
    """
    if not confirmed:
        return "Refusing: pass confirmed=true to terminate the bookmarks-mcp server process."
    os.kill(os.getpid(), signal.SIGTERM)
    return "bookmarks-mcp server terminating."

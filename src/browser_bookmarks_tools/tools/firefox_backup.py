# Firefox backup and authentication portmanteau tool.
# Consolidates Firefox backup and auth operations into a single interface.

import logging
from typing import Any

from browser_bookmarks_tools.config.mcp_config import mcp
from browser_bookmarks_tools.services.backup_service import (
    backup_browser_profile,
    restore_browser_profile,
)
from browser_bookmarks_tools.tools.help_tools import HelpSystem

logger = logging.getLogger(__name__)


@mcp.tool()
@HelpSystem.register_tool(category="firefox")
async def firefox_backup(
    operation: str,
    profile_name: str | None = None,
    browser_id: str = "firefox",
    backup_path: str | None = None,
    include_bookmarks: bool = True,
    include_settings: bool = True,
    include_passwords: bool = False,
    restore_path: str | None = None,
    overwrite: bool = False,
    create_session: bool = False,
) -> dict[str, Any]:
    """Firefox/Gecko backup and authentication portmanteau tool.

    Operations: backup_firefox_data, restore_firefox_data, create_session.
    profile_name: profile name (default: 'default')
    browser_id: gecko browser id (default: firefox)
    backup_path: directory for backup ZIP output
    restore_path: path to backup ZIP for restore
    """
    del include_bookmarks, include_settings, include_passwords, create_session

    if operation == "backup_firefox_data":
        if not backup_path:
            return {"success": False, "error": "backup_path is required"}
        return await backup_browser_profile(browser_id, profile_name, backup_path)

    if operation == "restore_firefox_data":
        if not restore_path:
            return {"success": False, "error": "restore_path is required"}
        return await restore_browser_profile(
            browser_id,
            restore_path,
            profile_name,
            overwrite=overwrite,
        )

    if operation == "create_session":
        return {
            "success": False,
            "error": "create_session is not implemented",
            "note": "Use gecko browser directly for bookmark operations.",
        }

    return {
        "success": False,
        "error": f"Unknown operation: {operation}",
        "available_operations": [
            "backup_firefox_data",
            "restore_firefox_data",
            "create_session",
        ],
    }

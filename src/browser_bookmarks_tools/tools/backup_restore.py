"""Batch and single-profile backup/restore across browser families."""

from __future__ import annotations

from typing import Any, Literal

from browser_bookmarks_tools.config.mcp_config import mcp
from browser_bookmarks_tools.services.backup_service import (
    backup_browser_profile,
    batch_backup_profiles,
    batch_restore_profiles,
    default_backup_root,
    list_backup_targets,
    restore_browser_profile,
)
from browser_bookmarks_tools.tools.help_tools import HelpSystem

BackupRestoreOperation = Literal[
    "list_targets",
    "backup_profile",
    "restore_profile",
    "batch_backup",
    "batch_restore",
]


@mcp.tool()
@HelpSystem.register_tool
async def backup_restore(
    operation: BackupRestoreOperation,
    browser: str | None = None,
    profile_name: str | None = None,
    backup_destination: str | None = None,
    backup_file: str | None = None,
    browsers: list[str] | None = None,
    restore_plan: list[dict[str, Any]] | None = None,
    overwrite: bool = False,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Backup and restore browser bookmark profiles (single or batch).

    Supports gecko, chromium, and safari families.
    batch_backup backs up all available targets (optionally filtered by browsers list).
    batch_restore accepts a list of {browser, profile_name, backup_file} entries.
    Default backup root: ~/.bookmarks-mcp/backups
    """
    if operation == "list_targets":
        return await list_backup_targets()

    if operation == "backup_profile":
        if not browser:
            return {"success": False, "error": "browser is required for backup_profile"}
        return await backup_browser_profile(
            browser,
            profile_name,
            backup_destination or str(default_backup_root()),
        )

    if operation == "restore_profile":
        if not browser or not backup_file:
            return {"success": False, "error": "browser and backup_file are required for restore_profile"}
        return await restore_browser_profile(
            browser,
            backup_file,
            profile_name,
            overwrite=overwrite,
        )

    if operation == "batch_backup":
        return await batch_backup_profiles(
            browsers=browsers,
            backup_destination=backup_destination,
            dry_run=dry_run,
        )

    if operation == "batch_restore":
        plan = restore_plan or []
        if not plan and dry_run:
            return {
                "success": False,
                "error": "restore_plan required for batch_restore (unless dry_run with list_targets first)",
            }
        return await batch_restore_profiles(plan, overwrite=overwrite, dry_run=dry_run)

    return {"success": False, "error": f"Unsupported operation: {operation}"}

from typing import Any

from browser_bookmarks_tools.config.mcp_config import mcp
from browser_bookmarks_tools.services.browser.gecko_registry import is_gecko_browser, list_gecko_browser_ids
from browser_bookmarks_tools.services.browser.safari_registry import is_safari_browser
from browser_bookmarks_tools.tools.chromium import is_chromium_browser, list_chromium_browser_ids
from browser_bookmarks_tools.tools.sync_tree import sync_bookmarks_with_folders


@mcp.tool()
async def sync_bookmarks(
    source_browser: str,
    target_browser: str,
    dry_run: bool = True,
    limit: int = 1000,
    source_profile: str | None = None,
    target_profile: str | None = None,
    preserve_folders: bool = True,
) -> dict[str, Any]:
    """Sync bookmarks between browsers with optional folder preservation.

    Supports gecko, chromium, and safari families. Folder paths are preserved when the
    target browser supports folder writes (chromium, safari). Gecko targets receive flat imports.
    """
    if source_browser.lower() == target_browser.lower():
        return {
            "status": "error",
            "error_code": "SYNC_SAME_BROWSER",
            "error": "source_browser == target_browser",
            "context": {"source": source_browser, "target": target_browser},
            "fix": "set source_browser != target_browser",
        }

    valid = [*list_gecko_browser_ids(), *list_chromium_browser_ids(), "safari"]
    source_key = source_browser.lower()
    target_key = target_browser.lower()

    if not (is_gecko_browser(source_key) or is_chromium_browser(source_key) or is_safari_browser(source_key)):
        return {
            "status": "error",
            "error_code": "SYNC_INVALID_SOURCE",
            "error": f"source_browser={source_browser} not in supported list",
            "context": {"provided": source_browser, "valid": valid, "target": target_browser},
            "fix": f"set source_browser to one of: {'|'.join(valid)}",
        }

    if not (is_gecko_browser(target_key) or is_chromium_browser(target_key) or is_safari_browser(target_key)):
        return {
            "status": "error",
            "error_code": "SYNC_INVALID_TARGET",
            "error": f"target_browser={target_browser} not in supported list",
            "context": {"provided": target_browser, "valid": valid, "source": source_browser},
            "fix": f"set target_browser to one of: {'|'.join(valid)}",
        }

    return await sync_bookmarks_with_folders(
        source_browser=source_key,
        target_browser=target_key,
        source_profile=source_profile,
        target_profile=target_profile,
        dry_run=dry_run,
        limit=limit,
        preserve_folders=preserve_folders,
    )


async def sync_tools_health() -> dict[str, Any]:
    return {"status": "ok"}

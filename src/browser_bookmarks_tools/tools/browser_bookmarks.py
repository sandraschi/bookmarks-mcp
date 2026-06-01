"""
Universal browser bookmark management portmanteau tool.

This module provides a unified interface for bookmark management across all
supported browsers with full CRUD and advanced operations.
"""

from typing import Any

from browser_bookmarks_tools.config.mcp_config import mcp
from browser_bookmarks_tools.operation_types import BrowserBookmarkOperation
from browser_bookmarks_tools.tools.help_tools import HelpSystem


@mcp.tool()
@HelpSystem.register_tool
async def browser_bookmarks(
    operation: BrowserBookmarkOperation,
    browser: str,
    profile_name: str | None = None,
    # Core parameters
    folder_id: int | None = None,
    bookmark_id: str | None = None,
    url: str | None = None,
    title: str | None = None,
    folder: str | None = None,
    # Edit parameters
    new_title: str | None = None,
    new_folder: str | None = None,
    # Search/filter parameters
    tags: list[str] | None = None,
    search_query: str | None = None,
    search_type: str = "all",
    limit: int = 100,
    offset: int = 0,
    # Export parameters
    export_format: str = "json",
    export_path: str | None = None,
    # Advanced parameters
    batch_size: int = 100,
    similarity_threshold: float = 0.85,
    age_days: int = 365,
    check_links: bool = False,
    # Options
    allow_duplicates: bool = False,
    create_folders: bool = True,
    dry_run: bool = False,
    # Sync parameters
    target_browser: str | None = None,
    target_profile: str | None = None,
    preserve_folders: bool = True,
    # Firefox lock bypass
    force_access: bool = False,
) -> dict[str, Any]:
    """Universal browser bookmark management portmanteau tool.

    Browsers: gecko registry + chromium registry + safari (macOS plist).
    Core CRUD/search: chromium + safari. Advanced ops (duplicates, export, stats, broken links, age):
    all families except gecko-only tag operations.
    For full docs call help_system.

    Parameter guidance:
    - profile_name: Gecko profile name, or Chromium profile folder (Default, Profile 1, …).
      Ignored for flat-profile browsers (Opera, Opera GX) and Tor (single profile).
    - limit: Paginated cap for list/search operations; clamped to 1..10000.
    - search vs find_duplicates:
      - search/search_bookmarks: text lookup by title/url.
      - find_duplicates (Firefox-only): structural duplicate detection and similarity logic.

    Returns (success=True):
    - Common: success, browser, operation.
    - list_bookmarks/search: results/bookmarks, total_count|total_matches,
      returned_count, pagination with limit/offset/has_more.
    - CRUD: bookmark or operation-specific fields from browser backend.

    Returns (success=False):
    - success, browser, operation, error, and usually recovery_options.
    """
    limit = max(1, min(limit, 10_000))
    offset = max(0, offset)

    browser_lower = browser.lower()

    def _paginate(items: list[Any]) -> dict[str, Any]:
        total = len(items)
        page = items[offset : offset + limit]
        returned = len(page)
        return {
            "total_count": total,
            "returned_count": returned,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": offset + returned < total,
                "total_count": total,
            },
        }

    # Special handling for sync_bookmarks (cross-browser operation)
    if operation == "sync_bookmarks":
        if not target_browser:
            return {
                "success": False,
                "error": "sync_bookmarks operation requires 'target_browser' parameter",
            }
        from browser_bookmarks_tools.tools.sync_tools import sync_bookmarks

        return await sync_bookmarks(
            source_browser=browser,
            target_browser=target_browser,
            dry_run=dry_run,
            limit=limit,
            source_profile=profile_name,
            target_profile=target_profile,
            preserve_folders=preserve_folders,
        )

    # Gecko-family browsers — reuse firefox_bookmarks engine with registry paths
    from browser_bookmarks_tools.services.browser.gecko_registry import is_gecko_browser, list_gecko_browser_ids

    if is_gecko_browser(browser_lower):
        from browser_bookmarks_tools.tools.firefox_bookmarks import firefox_bookmarks as gecko_bookmarks

        gecko_operation = "search_bookmarks" if operation == "search" else operation

        result = await gecko_bookmarks(
            operation=gecko_operation,
            browser_id=browser_lower,
            profile_name=profile_name,
            folder_id=folder_id,
            bookmark_id=int(bookmark_id) if bookmark_id and bookmark_id.isdigit() else None,
            url=url,
            title=title,
            tags=tags,
            search_query=search_query,
            search_type=search_type,
            export_format=export_format,
            export_path=export_path,
            batch_size=batch_size,
            similarity_threshold=similarity_threshold,
            age_days=age_days,
            check_links=check_links,
            force_access=force_access,
        )
        result["browser"] = browser_lower
        if gecko_operation in ("list_bookmarks", "search_bookmarks") and result.get("success"):
            key = "bookmarks" if "bookmarks" in result else "results"
            items = result.get(key) or []
            if isinstance(items, list):
                page_info = _paginate(items)
                result[key] = items[offset : offset + limit]
                result.update(page_info)
        return result

    # Chromium-family browsers — registry-driven unified adapter
    from browser_bookmarks_tools.tools.chromium import (
        add_chromium_bookmark,
        delete_chromium_bookmark,
        edit_chromium_bookmark,
        get_chromium_bookmark,
        is_chromium_browser,
        list_chromium_bookmarks,
        search_chromium_bookmarks,
        supported_chromium_operations,
    )

    from browser_bookmarks_tools.tools.universal_bookmark_ops import (
        UNIVERSAL_ADVANCED_OPERATIONS,
        execute_universal_operation,
    )

    if is_chromium_browser(browser_lower):
        profile = profile_name or "Default"

        if operation in UNIVERSAL_ADVANCED_OPERATIONS:
            return await execute_universal_operation(
                operation,
                browser_lower,
                profile,
                limit=limit,
                export_format=export_format,
                export_path=export_path,
                similarity_threshold=similarity_threshold,
                age_days=age_days,
                check_links=check_links,
            )

        if operation == "list_bookmarks":
            result = await list_chromium_bookmarks(browser_lower, profile_name=profile)
            if result.get("success") and isinstance(result.get("bookmarks"), list):
                page_info = _paginate(result["bookmarks"])
                result["bookmarks"] = result["bookmarks"][offset : offset + limit]
                result.update(page_info)
            return result

        if operation == "add_bookmark":
            if not url or not title:
                return {
                    "success": False,
                    "browser": browser_lower,
                    "browser_family": "chromium",
                    "profile_name": profile,
                    "operation": operation,
                    "error": "add_bookmark requires 'url' and 'title' parameters",
                    "recovery_options": [
                        "Provide both url and title.",
                        "Use list_bookmarks to confirm target folder before adding.",
                    ],
                }
            return await add_chromium_bookmark(
                browser_lower,
                title=title,
                url=url,
                folder=folder,
                profile_name=profile,
            )

        if operation == "edit_bookmark":
            if not bookmark_id and not url:
                return {
                    "success": False,
                    "browser": browser_lower,
                    "browser_family": "chromium",
                    "profile_name": profile,
                    "operation": operation,
                    "error": "edit_bookmark requires 'bookmark_id' or 'url' parameter",
                    "recovery_options": [
                        "Pass bookmark_id for an exact edit target.",
                        "Use search_bookmarks first to find the correct bookmark.",
                    ],
                }
            return await edit_chromium_bookmark(
                browser_lower,
                id=bookmark_id,
                url=url,
                new_title=new_title,
                new_folder=new_folder,
                allow_duplicates=allow_duplicates,
                create_folders=create_folders,
                dry_run=dry_run,
                profile_name=profile,
            )

        if operation == "delete_bookmark":
            if not bookmark_id and not url:
                return {
                    "success": False,
                    "browser": browser_lower,
                    "browser_family": "chromium",
                    "profile_name": profile,
                    "operation": operation,
                    "error": "delete_bookmark requires 'bookmark_id' or 'url' parameter",
                    "recovery_options": [
                        "Pass bookmark_id for safest deletion.",
                        "Use dry_run=True first to preview the deletion.",
                    ],
                }
            return await delete_chromium_bookmark(
                browser_lower,
                id=bookmark_id,
                url=url,
                dry_run=dry_run,
                profile_name=profile,
            )

        if operation in ("search", "search_bookmarks"):
            if not search_query:
                return {
                    "success": False,
                    "browser": browser_lower,
                    "browser_family": "chromium",
                    "profile_name": profile,
                    "operation": operation,
                    "error": "search requires 'search_query' parameter",
                    "recovery_options": ["Provide search_query text to match title/url."],
                }
            result = await search_chromium_bookmarks(
                browser_lower,
                search_query,
                profile_name=profile,
                limit=limit,
            )
            if result.get("success") and isinstance(result.get("results"), list):
                page_info = _paginate(result["results"])
                result["results"] = result["results"][offset : offset + limit]
                result.update(page_info)
            return result

        if operation == "get_bookmark":
            if not bookmark_id and not url:
                return {
                    "success": False,
                    "browser": browser_lower,
                    "browser_family": "chromium",
                    "profile_name": profile,
                    "operation": operation,
                    "error": "get_bookmark requires 'bookmark_id' or 'url' parameter",
                }
            return await get_chromium_bookmark(
                browser_lower,
                bookmark_id=bookmark_id,
                url=url,
                profile_name=profile,
            )

        return {
            "success": False,
            "browser": browser_lower,
            "browser_family": "chromium",
            "profile_name": profile,
            "operation": operation,
            "error": f"Operation '{operation}' not supported for {browser_lower}",
            "supported_operations": [
                *supported_chromium_operations(),
                *UNIVERSAL_ADVANCED_OPERATIONS,
            ],
            "note": "Gecko-only: list_tags, merge_tags, batch_update_tags, clean_up_tags",
            "recovery_options": [
                "Use a supported operation from supported_operations.",
                "Use browser='firefox' (or zen/librewolf) for tag operations.",
            ],
        }

    from browser_bookmarks_tools.services.browser.safari_registry import is_safari_browser
    from browser_bookmarks_tools.tools.safari import (
        add_safari_bookmark,
        delete_safari_bookmark_op,
        get_safari_bookmark,
        list_safari_bookmarks,
        search_safari_bookmarks,
        supported_safari_operations,
    )

    if is_safari_browser(browser_lower):
        if operation in UNIVERSAL_ADVANCED_OPERATIONS:
            return await execute_universal_operation(
                operation,
                "safari",
                profile_name,
                limit=limit,
                export_format=export_format,
                export_path=export_path,
                similarity_threshold=similarity_threshold,
                age_days=age_days,
                check_links=check_links,
            )

        if operation == "list_bookmarks":
            result = await list_safari_bookmarks()
            if result.get("success") and isinstance(result.get("bookmarks"), list):
                page_info = _paginate(result["bookmarks"])
                result["bookmarks"] = result["bookmarks"][offset : offset + limit]
                result.update(page_info)
            return result

        if operation == "add_bookmark":
            if not url or not title:
                return {
                    "success": False,
                    "browser": "safari",
                    "operation": operation,
                    "error": "add_bookmark requires 'url' and 'title' parameters",
                }
            return await add_safari_bookmark(title=title, url=url, folder=folder, dry_run=dry_run)

        if operation == "delete_bookmark":
            if not url and not bookmark_id:
                return {
                    "success": False,
                    "browser": "safari",
                    "operation": operation,
                    "error": "delete_bookmark requires 'url' or 'bookmark_id'",
                }
            return await delete_safari_bookmark_op(url=url or bookmark_id, dry_run=dry_run)

        if operation in ("search", "search_bookmarks"):
            if not search_query:
                return {
                    "success": False,
                    "browser": "safari",
                    "operation": operation,
                    "error": "search requires 'search_query' parameter",
                }
            result = await search_safari_bookmarks(search_query, limit=limit)
            if result.get("success") and isinstance(result.get("results"), list):
                page_info = _paginate(result["results"])
                result["results"] = result["results"][offset : offset + limit]
                result.update(page_info)
            return result

        if operation == "get_bookmark":
            return await get_safari_bookmark(bookmark_id=bookmark_id, url=url)

        return {
            "success": False,
            "browser": "safari",
            "operation": operation,
            "error": f"Operation '{operation}' not supported for safari",
            "supported_operations": supported_safari_operations(),
        }

    from browser_bookmarks_tools.tools.chromium import list_chromium_browser_ids

    return {
        "success": False,
        "operation": operation,
        "browser": browser,
        "error": f"Unknown browser type: {browser}",
        "supported_browsers": [*list_gecko_browser_ids(), *list_chromium_browser_ids(), "safari"],
        "recovery_options": [
            f"Use a gecko id ({', '.join(list_gecko_browser_ids())}), "
            f"chromium id ({', '.join(list_chromium_browser_ids())}), or safari.",
        ],
    }

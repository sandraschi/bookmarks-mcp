"""Sidecar bookmark metadata portmanteau tool."""

from __future__ import annotations

from typing import Any, Literal

from browser_bookmarks_tools.config.mcp_config import mcp
from browser_bookmarks_tools.services.bookmark_import import metadata_rows_from_bookmarks, parse_bookmark_file
from browser_bookmarks_tools.services.metadata.sidecar_db import SidecarMetadataStore, default_sidecar_path
from browser_bookmarks_tools.tools.help_tools import HelpSystem

BookmarkMetadataOperation = Literal[
    "get_metadata",
    "set_metadata",
    "delete_metadata",
    "list_metadata",
    "record_read",
    "import_metadata",
    "sidecar_info",
]


@mcp.tool()
@HelpSystem.register_tool
async def bookmark_metadata(
    operation: BookmarkMetadataOperation,
    url: str | None = None,
    browser: str | None = None,
    profile_name: str | None = None,
    title: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    tags: list[str] | None = None,
    starred: int = 0,
    tag: str | None = None,
    starred_only: bool = False,
    search_query: str | None = None,
    import_path: str | None = None,
    import_format: str = "auto",
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Manage sidecar SQLite metadata for bookmarks (description, tags, stars, read stats, comments).

    Native browser files (Chromium JSON, Safari plist) do not store descriptions or user notes.
    Firefox stores some fields in places.sqlite but they do not travel with exports.
    This sidecar DB keys rows by (url, browser, profile_name). Use empty browser/profile for global scope.

    Sidecar path: ~/.bookmarks-mcp/metadata.db (override with BOOKMARKS_MCP_DATA_DIR).
    """
    limit = max(1, min(limit, 10_000))
    offset = max(0, offset)
    store = SidecarMetadataStore()

    if operation == "sidecar_info":
        return {
            "success": True,
            "operation": operation,
            "db_path": str(default_sidecar_path()),
            "scope_note": "Rows keyed by (url, browser, profile_name). Empty browser/profile = global.",
            "fields": [
                "description",
                "user_comment",
                "tags",
                "starred (0-5)",
                "read_count",
                "last_read_at",
            ],
        }

    if operation == "get_metadata":
        if not url:
            return {"success": False, "operation": operation, "error": "url is required"}
        metadata = store.get(url, browser=browser, profile_name=profile_name)
        return {
            "success": metadata is not None,
            "operation": operation,
            "metadata": metadata,
            "url": url,
        }

    if operation == "set_metadata":
        if not url:
            return {"success": False, "operation": operation, "error": "url is required"}
        result = store.upsert(
            url,
            browser=browser,
            profile_name=profile_name,
            title=title,
            description=description,
            user_comment=user_comment,
            tags=tags,
            starred=starred,
        )
        result["operation"] = operation
        return result

    if operation == "delete_metadata":
        if not url:
            return {"success": False, "operation": operation, "error": "url is required"}
        result = store.delete(url, browser=browser, profile_name=profile_name)
        result["operation"] = operation
        return result

    if operation == "record_read":
        if not url:
            return {"success": False, "operation": operation, "error": "url is required"}
        result = store.record_read(url, browser=browser, profile_name=profile_name)
        result["operation"] = operation
        return result

    if operation == "list_metadata":
        result = store.list_metadata(
            browser=browser,
            profile_name=profile_name,
            tag=tag,
            starred_only=starred_only,
            search_query=search_query,
            limit=limit,
            offset=offset,
        )
        result["operation"] = operation
        return result

    if operation == "import_metadata":
        if not import_path:
            return {"success": False, "operation": operation, "error": "import_path is required"}
        parsed = parse_bookmark_file(import_path, import_format)
        if not parsed.get("success"):
            parsed["operation"] = operation
            return parsed
        rows = metadata_rows_from_bookmarks(
            parsed.get("bookmarks") or [],
            browser=browser,
            profile_name=profile_name,
        )
        imported = store.import_rows(rows, merge=True)
        return {
            "success": True,
            "operation": operation,
            "import_path": import_path,
            "import_format": parsed.get("import_format"),
            "source_count": parsed.get("count"),
            **imported,
        }

    return {
        "success": False,
        "operation": operation,
        "error": f"Unsupported operation: {operation}",
    }

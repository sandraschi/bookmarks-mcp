"""Named bookmark collections portmanteau tool (e.g. "ai", "music", "politics").

Collections are the durable curation layer browsers don't give you: star,
comment, and group bookmarks into named sets with real CRUD - create, rename,
delete (member bookmarks are never touched, only membership). See
services/metadata/collection_store.py for the storage layer.
"""

from __future__ import annotations

from typing import Any, Literal

from browser_bookmarks_tools.config.mcp_config import mcp
from browser_bookmarks_tools.services.metadata.collection_store import CollectionStore
from browser_bookmarks_tools.tools.help_tools import HelpSystem

CollectionsOperation = Literal[
    "create_collection",
    "update_collection",
    "delete_collection",
    "list_collections",
    "add_to_collection",
    "remove_from_collection",
    "bulk_add_to_collection",
    "get_collections_for_urls",
]


@mcp.tool()
@HelpSystem.register_tool
async def collections(
    operation: CollectionsOperation,
    collection_id: int | None = None,
    name: str | None = None,
    description: str | None = None,
    color: str | None = None,
    url: str | None = None,
    urls: list[str] | None = None,
    browser: str | None = None,
    profile_name: str | None = None,
) -> dict[str, Any]:
    """Manage named bookmark collections and bookmark-to-collection membership.

    Collections live in the same sidecar SQLite file as bookmark_metadata
    (~/.bookmarks-mcp/metadata.db, override with BOOKMARKS_MCP_DATA_DIR), as a
    real CRUD entity rather than free-text tag strings: rename without
    touching every member, delete without touching the bookmarks themselves.

    OPERATIONS:
    - create_collection(name, description?, color?)
    - update_collection(collection_id, name?, description?, color?)
    - delete_collection(collection_id) - removes membership only, never bookmarks
    - list_collections() - all collections with member counts
    - add_to_collection(url, collection_id, browser?, profile_name?)
    - remove_from_collection(url, collection_id, browser?, profile_name?)
    - bulk_add_to_collection(urls, collection_id, browser?, profile_name?)
    - get_collections_for_urls(urls, browser?, profile_name?) - membership map for a page of rows
    """
    store = CollectionStore()

    if operation == "create_collection":
        if not name:
            return {"success": False, "operation": operation, "error": "name is required"}
        result = store.create_collection(name, description=description, color=color)
        result["operation"] = operation
        return result

    if operation == "update_collection":
        if collection_id is None:
            return {"success": False, "operation": operation, "error": "collection_id is required"}
        result = store.update_collection(collection_id, name=name, description=description, color=color)
        result["operation"] = operation
        return result

    if operation == "delete_collection":
        if collection_id is None:
            return {"success": False, "operation": operation, "error": "collection_id is required"}
        result = store.delete_collection(collection_id)
        result["operation"] = operation
        return result

    if operation == "list_collections":
        result = store.list_collections()
        result["operation"] = operation
        return result

    if operation == "add_to_collection":
        if not url or collection_id is None:
            return {"success": False, "operation": operation, "error": "url and collection_id are required"}
        result = store.add_to_collection(url, collection_id, browser=browser, profile_name=profile_name)
        result["operation"] = operation
        return result

    if operation == "remove_from_collection":
        if not url or collection_id is None:
            return {"success": False, "operation": operation, "error": "url and collection_id are required"}
        result = store.remove_from_collection(url, collection_id, browser=browser, profile_name=profile_name)
        result["operation"] = operation
        return result

    if operation == "bulk_add_to_collection":
        if not urls or collection_id is None:
            return {"success": False, "operation": operation, "error": "urls and collection_id are required"}
        result = store.bulk_add_to_collection(urls, collection_id, browser=browser, profile_name=profile_name)
        result["operation"] = operation
        return result

    if operation == "get_collections_for_urls":
        if not urls:
            return {"success": False, "operation": operation, "error": "urls is required"}
        mapping = store.get_collections_for_urls(urls, browser=browser, profile_name=profile_name)
        return {"success": True, "operation": operation, "collections_by_url": mapping}

    return {
        "success": False,
        "operation": operation,
        "error": f"Unsupported operation: {operation}",
    }

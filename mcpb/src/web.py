import json
import sqlite3
from pathlib import Path
from typing import Any

from browser_bookmarks_tools.activity_log import (
    SortOrder,
    clear_logs,
    export_logs,
    get_activity,
    install_log_handler,
    log_activity,
    log_stats,
    query_logs,
)
from browser_bookmarks_tools.auth import authenticate
from browser_bookmarks_tools.services.browser.gecko_paths import resolve_places_db_path
from browser_bookmarks_tools.services.browser.gecko_registry import is_gecko_browser, list_gecko_browsers
from browser_bookmarks_tools.services.browser.safari_registry import is_safari_browser, list_safari_browsers
from browser_bookmarks_tools.tools.chromium import is_chromium_browser, list_chromium_browsers
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
dist_dir = project_root / "web_sota" / "dist"


class ToolExecutionRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ExportRequest(BaseModel):
    browser: str
    profile_name: str | None = None
    export_format: str = "json"
    limit: int = 10_000


def _serialize_tool_result(result: Any) -> Any:
    if result is None:
        return None
    structured = getattr(result, "structured_content", None)
    if structured is not None:
        return structured
    content = getattr(result, "content", None)
    if content:
        texts = []
        for block in content:
            text = getattr(block, "text", None)
            if text:
                texts.append(text)
        if len(texts) == 1:
            try:
                return json.loads(texts[0])
            except json.JSONDecodeError:
                return texts[0]
        if texts:
            return texts
    if isinstance(result, dict):
        return result
    return str(result)


async def _list_mcp_tools(mcp_app) -> list[dict[str, Any]]:
    tools = await mcp_app.list_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": getattr(tool, "inputSchema", None) or getattr(tool, "parameters", None),
        }
        for tool in tools
    ]


def _chromium_node_to_tree(node: dict[str, Any], parent_path: str = "") -> dict[str, Any] | None:
    node_type = node.get("type")
    if node_type == "url":
        return {
            "type": "bookmark",
            "id": node.get("id"),
            "title": node.get("name") or "(untitled)",
            "url": node.get("url"),
        }
    if node_type == "folder":
        name = node.get("name") or "Folder"
        path = f"{parent_path}/{name}" if parent_path else name
        children: list[dict[str, Any]] = []
        for child in node.get("children", []) or []:
            mapped = _chromium_node_to_tree(child, path)
            if mapped:
                children.append(mapped)
        return {"type": "folder", "name": name, "path": path, "children": children}
    return None


def _read_chromium_tree(browser: str, profile_name: str | None = None) -> dict[str, Any]:
    from browser_bookmarks_tools.tools.chromium import resolve_bookmarks_path

    if not is_chromium_browser(browser):
        return {"success": False, "error": f"Unsupported browser for tree: {browser}"}

    path = resolve_bookmarks_path(browser, profile_name)
    if path is None or not path.exists():
        return {
            "success": False,
            "error": f"Bookmarks file not found for {browser} profile {profile_name or 'Default'}",
        }

    data = json.loads(path.read_text(encoding="utf-8"))
    roots = data.get("roots", {})
    tree: list[dict[str, Any]] = []
    for root_key in ("bookmark_bar", "other", "synced"):
        root_node = roots.get(root_key)
        if not root_node:
            continue
        mapped = _chromium_node_to_tree(root_node, root_key)
        if mapped:
            tree.append(mapped)
    return {
        "success": True,
        "browser": browser,
        "profile_name": profile_name or "Default",
        "tree": tree,
    }


def _read_safari_tree(bookmarks_path: str | None = None) -> dict[str, Any]:
    from browser_bookmarks_tools.services.browser.safari_plist import read_safari_bookmarks

    path = Path(bookmarks_path) if bookmarks_path else None
    result = read_safari_bookmarks(path)
    if result.get("status") != "success":
        return {"success": False, "error": result.get("error"), "browser": "safari"}

    tree: list[dict[str, Any]] = []

    def walk(node: dict[str, Any], parent_path: str = "") -> dict[str, Any] | None:
        if node.get("WebBookmarkType") == "WebBookmarkTypeLeaf":
            uri = node.get("URIDictionary") or {}
            return {
                "type": "bookmark",
                "title": uri.get("title") or uri.get("URLString") or "(untitled)",
                "url": uri.get("URLString"),
            }
        if node.get("WebBookmarkType") == "WebBookmarkTypeList":
            name = node.get("Title") or "Folder"
            path = f"{parent_path}/{name}" if parent_path else name
            children = []
            for child in node.get("Children") or []:
                if isinstance(child, dict):
                    mapped = walk(child, path)
                    if mapped:
                        children.append(mapped)
            return {"type": "folder", "name": name, "path": path, "children": children}
        return None

    with Path(result["bookmarks_path"]).open("rb") as handle:
        import plistlib

        data = plistlib.load(handle)

    for child in (data.get("Children") if isinstance(data, dict) else []) or []:
        if isinstance(child, dict):
            mapped = walk(child)
            if mapped:
                tree.append(mapped)

    return {"success": True, "browser": "safari", "profile_name": "default", "tree": tree}


def _read_gecko_tree(browser: str, profile_name: str | None) -> dict[str, Any]:
    places_db = resolve_places_db_path(browser, profile_name)
    if not places_db or not places_db.exists():
        return {
            "success": False,
            "error": f"places DB not found for {browser} profile: {profile_name or 'default'}",
        }
    return _read_firefox_tree_from_db(places_db, browser, profile_name)


def _read_firefox_tree_from_db(
    places_db: Path,
    browser: str = "firefox",
    profile_name: str | None = None,
) -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{places_db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, parent, type FROM moz_bookmarks ORDER BY id")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    nodes: dict[int, dict[str, Any]] = {}
    for row in rows:
        nodes[row["id"]] = {
            "id": row["id"],
            "title": row["title"] or ("Bookmarks" if row["type"] == 2 else "(untitled)"),
            "parent": row["parent"],
            "type": "folder" if row["type"] == 2 else "bookmark",
            "children": [],
        }

    bookmarks_by_parent: dict[int, list[dict[str, Any]]] = {}
    cursor = sqlite3.connect(f"file:{places_db}?mode=ro", uri=True).cursor()
    cursor.execute(
        """
        SELECT b.id, b.title, p.url, b.parent
        FROM moz_bookmarks b
        JOIN moz_places p ON b.fk = p.id
        WHERE b.type = 1
        """
    )
    for bid, title, url, parent in cursor.fetchall():
        bookmarks_by_parent.setdefault(parent, []).append(
            {"type": "bookmark", "id": bid, "title": title or "(untitled)", "url": url}
        )

    def build_folder(folder_id: int) -> dict[str, Any] | None:
        node = nodes.get(folder_id)
        if not node or node["type"] != "folder":
            return None
        children: list[dict[str, Any]] = []
        for child_id, child in nodes.items():
            if child.get("parent") == folder_id and child["type"] == "folder":
                built = build_folder(child_id)
                if built:
                    children.append(built)
        for bookmark in bookmarks_by_parent.get(folder_id, []):
            children.append(bookmark)
        return {
            "type": "folder",
            "id": folder_id,
            "name": node["title"],
            "path": node["title"],
            "children": children,
        }

    tree: list[dict[str, Any]] = []
    for folder_id, node in nodes.items():
        if node["type"] == "folder" and node.get("parent") in (None, 0):
            built = build_folder(folder_id)
            if built:
                tree.append(built)

    if not tree and rows:
        tree = [build_folder(row["id"]) for row in rows if row["type"] == 2 and row["id"] == 1]
        tree = [t for t in tree if t]

    return {"success": True, "browser": browser, "profile_name": profile_name, "tree": tree}


def _read_firefox_tree(profile_name: str | None) -> dict[str, Any]:
    return _read_gecko_tree("firefox", profile_name)


router = APIRouter(prefix="/api", dependencies=[Depends(authenticate)])


def setup_webapp(app, mcp_app=None) -> None:
    install_log_handler()
    if mcp_app:

        @router.get("/health")
        async def api_health():
            return {"status": "ok", "mcp": "bookmarks-mcp"}

        @router.get("/status")
        async def api_status():
            tools = await _list_mcp_tools(mcp_app)
            return {
                "status": "online",
                "server": "bookmarks-mcp",
                "version": "0.2.0",
                "tool_count": len(tools),
            }

        @router.get("/tools")
        async def list_tools():
            return {"tools": await _list_mcp_tools(mcp_app)}

        @router.post("/tools/call")
        async def call_tool_endpoint(request: ToolCallRequest):
            try:
                result = await mcp_app.call_tool(request.name, request.arguments)
                payload = _serialize_tool_result(result)
                is_error = isinstance(payload, dict) and payload.get("success") is False
                log_activity(
                    "tool_call",
                    f"{request.name} ({'error' if is_error else 'ok'})",
                    level="ERROR" if is_error else "INFO",
                    meta={"tool": request.name, "arguments": request.arguments},
                )
                return {"result": payload, "isError": is_error}
            except Exception as exc:
                log_activity(
                    "tool_call",
                    f"{request.name} (exception)",
                    level="ERROR",
                    meta={"error": str(exc)},
                )
                return {"result": {"success": False, "error": str(exc)}, "isError": True}

        @router.post("/tools/{tool_name}")
        async def execute_tool_legacy(tool_name: str, request: ToolExecutionRequest):
            try:
                result = await mcp_app.call_tool(tool_name, request.arguments)
                return {"result": _serialize_tool_result(result)}
            except Exception as exc:
                return {"error": str(exc)}

        @router.get("/browsers/safari")
        async def safari_browsers():
            return {"browsers": list_safari_browsers()}

        @router.get("/browsers/gecko")
        async def gecko_browsers():
            return {"browsers": list_gecko_browsers()}

        @router.get("/browsers/chromium")
        async def chromium_browsers():
            return {"browsers": list_chromium_browsers()}

        @router.get("/bookmarks/tree")
        async def bookmark_tree(
            browser: str = Query(...),
            profile_name: str | None = Query(None),
        ):
            browser_lower = browser.lower()
            if is_gecko_browser(browser_lower):
                return _read_gecko_tree(browser_lower, profile_name)
            if is_chromium_browser(browser_lower):
                return _read_chromium_tree(browser_lower, profile_name)
            if is_safari_browser(browser_lower):
                return _read_safari_tree()
            return {"success": False, "error": f"Unsupported browser: {browser}"}

        @router.get("/activity")
        async def activity_feed(limit: int = Query(50, ge=1, le=200)):
            return {"entries": get_activity(limit)}

        @router.delete("/activity")
        async def activity_clear():
            clear_logs()
            return {"success": True}

        @router.get("/logs")
        async def logs_query(
            limit: int = Query(50, ge=1, le=500),
            offset: int = Query(0, ge=0),
            level: str | None = Query(None),
            kind: str | None = Query(None),
            search: str | None = Query(None),
            sort: str = Query("desc"),
            after_id: str | None = Query(None),
        ):
            order: SortOrder = "asc" if sort == "asc" else "desc"
            return query_logs(
                limit=limit,
                offset=offset,
                level=level,
                kind=kind,
                search=search,
                sort=order,
                after_id=after_id,
            )

        @router.get("/logs/stats")
        async def logs_stats():
            return log_stats()

        @router.get("/logs/export")
        async def logs_export(
            format: str = Query("json"),
            level: str | None = Query(None),
            kind: str | None = Query(None),
            search: str | None = Query(None),
            sort: str = Query("desc"),
        ):
            order: SortOrder = "asc" if sort == "asc" else "desc"
            if format not in ("json", "csv"):
                format = "json"
            body, media_type, filename = export_logs(
                format=format,
                level=level,
                kind=kind,
                search=search,
                sort=order,
            )
            return Response(
                content=body,
                media_type=media_type,
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        @router.delete("/logs")
        async def logs_clear():
            clear_logs()
            log_activity("system", "Log buffer cleared", level="WARNING")
            return {"success": True}

        @router.post("/bookmarks/export")
        async def export_bookmarks_download(request: ExportRequest):
            browser_lower = request.browser.lower()
            if is_gecko_browser(browser_lower):
                result = await mcp_app.call_tool(
                    "browser_bookmarks",
                    {
                        "operation": "export_bookmarks",
                        "browser": browser_lower,
                        "profile_name": request.profile_name,
                        "export_format": request.export_format,
                    },
                )
                payload = _serialize_tool_result(result)
                log_activity("export", f"{browser_lower} {request.export_format}")
                return {"result": payload}

            if is_safari_browser(browser_lower) or is_chromium_browser(browser_lower):
                result = await mcp_app.call_tool(
                    "browser_bookmarks",
                    {
                        "operation": "export_bookmarks",
                        "browser": browser_lower,
                        "profile_name": request.profile_name,
                        "export_format": request.export_format,
                        "limit": request.limit,
                    },
                )
                payload = _serialize_tool_result(result)
                log_activity("export", f"{browser_lower} {request.export_format}")
                return {"result": payload}

            list_result = await mcp_app.call_tool(
                "browser_bookmarks",
                {
                    "operation": "list_bookmarks",
                    "browser": browser_lower,
                    "profile_name": request.profile_name,
                    "limit": request.limit,
                },
            )
            payload = _serialize_tool_result(list_result)
            bookmarks = payload.get("bookmarks", []) if isinstance(payload, dict) else []
            filename = f"{browser_lower}-bookmarks.json"
            log_activity("export", filename, meta={"count": len(bookmarks)})
            return JSONResponse(
                content=bookmarks,
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

    app.include_router(router)

    from browser_bookmarks_tools.ai import router as ai_router

    app.include_router(ai_router)

    if dist_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

        @app.get("/{full_path:path}", response_class=HTMLResponse)
        async def serve_spa(_request: Request, full_path: str):
            if full_path.startswith("api/") or full_path.startswith("mcp"):
                return None
            index_path = dist_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return HTMLResponse(content="<h1>Frontend not built</h1>", status_code=404)
    else:

        @app.get("/", response_class=HTMLResponse)
        async def dev_hint():
            return HTMLResponse(content="<h1>Static files missing</h1><p>Run npm run build in web_sota/</p>")

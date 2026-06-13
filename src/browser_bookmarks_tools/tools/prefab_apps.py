"""FastMCP 3.3 Prefab app tools — interactive UI for bookmark operations."""

from __future__ import annotations

from typing import Any

from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Alert,
    Badge,
    Card,
    CardContent,
    Column,
    DataTable,
    DataTableColumn,
    Grid,
    Heading,
    Metric,
    Row,
    Text,
)
from prefab_ui.components.charts import BarChart, ChartSeries

from browser_bookmarks_tools.config.mcp_config import mcp
from browser_bookmarks_tools.services.backup_service import batch_backup_profiles, list_backup_targets
from browser_bookmarks_tools.services.bookmark_import import parse_bookmark_file
from browser_bookmarks_tools.services.metadata.sidecar_db import SidecarMetadataStore
from browser_bookmarks_tools.tools.bookmark_import_ops import import_bookmarks_from_file
from browser_bookmarks_tools.tools.bookmark_loader import load_browser_bookmarks
from browser_bookmarks_tools.tools.help_tools import HelpSystem
from browser_bookmarks_tools.tools.sync_tree import sync_bookmarks_with_folders
from browser_bookmarks_tools.tools.universal_bookmark_ops import get_bookmark_stats_from_list


def _rows_for_bookmarks(bookmarks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in bookmarks:
        meta = item.get("metadata") or {}
        rows.append(
            {
                "title": item.get("title") or item.get("name") or "(untitled)",
                "url": item.get("url") or "",
                "folder": item.get("folder_path") or item.get("folder") or "",
                "tags": ", ".join(meta.get("tags") or item.get("tags") or []),
                "starred": meta.get("starred") or 0,
            }
        )
    return rows


def _error_app(message: str) -> PrefabApp:
    with Column(gap=4, css_class="p-6") as view:
        Alert(message, variant="destructive")
    return PrefabApp(view=view)


@mcp.tool(app=True)
@HelpSystem.register_tool
async def browse_bookmarks_ui(
    browser: str,
    profile_name: str | None = None,
    limit: int = 50,
    include_metadata: bool = False,
) -> PrefabApp:
    """Browse bookmarks in an interactive table (FastMCP Prefab UI)."""
    loaded = await load_browser_bookmarks(browser, profile_name, limit=limit)
    if not loaded.get("success"):
        return _error_app(loaded.get("error") or "Failed to load bookmarks")

    bookmarks = loaded.get("bookmarks") or []
    if include_metadata:
        from browser_bookmarks_tools.services.metadata.enrich import enrich_bookmarks

        bookmarks = enrich_bookmarks(bookmarks, browser=browser, profile_name=profile_name)

    rows = _rows_for_bookmarks(bookmarks)
    with PrefabApp() as app:
        with Column(gap=4, css_class="p-6"):
            with Row(gap=2, align="center"):
                Heading(f"{browser} bookmarks")
                Badge(f"{len(rows)} shown", variant="secondary")
            DataTable(
                columns=[
                    DataTableColumn(key="title", header="Title", sortable=True),
                    DataTableColumn(key="url", header="URL", sortable=True),
                    DataTableColumn(key="folder", header="Folder", sortable=True),
                    DataTableColumn(key="tags", header="Tags"),
                    DataTableColumn(key="starred", header="★", sortable=True),
                ],
                rows=rows,
                search=True,
            )
    return app


@mcp.tool(app=True)
@HelpSystem.register_tool
async def bookmark_stats_ui(
    browser: str,
    profile_name: str | None = None,
    limit: int = 5000,
) -> PrefabApp:
    """Bookmark statistics dashboard (folders, counts, top folders chart)."""
    loaded = await load_browser_bookmarks(browser, profile_name, limit=limit)
    if not loaded.get("success"):
        return _error_app(loaded.get("error") or "Failed to load bookmarks")

    stats = get_bookmark_stats_from_list(loaded.get("bookmarks") or [])
    payload = stats.get("stats") or {}
    top_folders = [{"folder": name, "count": count} for name, count in (payload.get("top_folders") or [])[:8]]

    with PrefabApp() as app:
        with Column(gap=6, css_class="p-6"):
            Heading(f"{browser} bookmark stats")
            with Grid(columns=[2, 2, 2], gap=4):
                Metric(label="Total", value=str(payload.get("total_bookmarks", 0)))
                Metric(label="Folders", value=str(payload.get("folders", 0)))
                Metric(label="Dated", value=str(payload.get("dated_bookmarks", 0)))
            if top_folders:
                BarChart(
                    data=top_folders,
                    series=[ChartSeries(data_key="count", label="Bookmarks")],
                    x_axis="folder",
                )
    return app


@mcp.tool(app=True)
@HelpSystem.register_tool
async def import_preview_ui(
    import_path: str,
    import_format: str = "auto",
    limit: int = 25,
) -> PrefabApp:
    """Preview bookmarks parsed from an HTML/JSON export file."""
    parsed = parse_bookmark_file(import_path, import_format)
    if not parsed.get("success"):
        return _error_app(parsed.get("error") or "Import parse failed")

    rows = _rows_for_bookmarks((parsed.get("bookmarks") or [])[:limit])
    with PrefabApp() as app:
        with Column(gap=4, css_class="p-6"):
            with Row(gap=2, align="center"):
                Heading("Import preview")
                Badge(parsed.get("import_format") or "auto", variant="outline")
                Badge(f"{parsed.get('count', 0)} total", variant="secondary")
            Text(import_path, css_class="text-sm text-muted-foreground")
            DataTable(
                columns=[
                    DataTableColumn(key="title", header="Title", sortable=True),
                    DataTableColumn(key="url", header="URL", sortable=True),
                    DataTableColumn(key="folder", header="Folder", sortable=True),
                ],
                rows=rows,
                search=True,
            )
    return app


@mcp.tool(app=True)
@HelpSystem.register_tool
async def metadata_browser_ui(
    browser: str | None = None,
    profile_name: str | None = None,
    limit: int = 50,
) -> PrefabApp:
    """Browse sidecar metadata (descriptions, tags, stars, read stats)."""
    store = SidecarMetadataStore()
    result = store.list_metadata(browser=browser, profile_name=profile_name, limit=limit)
    rows = [
        {
            "url": item.get("url"),
            "description": (item.get("description") or "")[:80],
            "tags": ", ".join(item.get("tags") or []),
            "starred": item.get("starred") or 0,
            "read_count": item.get("read_count") or 0,
            "last_read_at": item.get("last_read_at") or "",
        }
        for item in result.get("items") or []
    ]

    with PrefabApp() as app:
        with Column(gap=4, css_class="p-6"):
            Heading("Sidecar metadata")
            DataTable(
                columns=[
                    DataTableColumn(key="url", header="URL", sortable=True),
                    DataTableColumn(key="description", header="Description"),
                    DataTableColumn(key="tags", header="Tags"),
                    DataTableColumn(key="starred", header="★", sortable=True),
                    DataTableColumn(key="read_count", header="Reads", sortable=True),
                ],
                rows=rows,
                search=True,
            )
    return app


@mcp.tool(app=True)
@HelpSystem.register_tool
async def sync_preview_ui(
    source_browser: str,
    target_browser: str,
    source_profile: str | None = None,
    target_profile: str | None = None,
    preserve_folders: bool = True,
    limit: int = 20,
) -> PrefabApp:
    """Visual dry-run preview for cross-browser sync."""
    result = await sync_bookmarks_with_folders(
        source_browser=source_browser,
        target_browser=target_browser,
        source_profile=source_profile,
        target_profile=target_profile,
        preserve_folders=preserve_folders,
        dry_run=True,
        limit=limit,
    )
    if result.get("status") == "error":
        return _error_app(result.get("error") or "Sync preview failed")

    rows = [
        {
            "title": item.get("title"),
            "url": item.get("url"),
            "folder_path": item.get("folder_path") or "",
        }
        for item in result.get("sample") or []
    ]

    with PrefabApp() as app:
        with Column(gap=4, css_class="p-6"):
            with Row(gap=2, align="center"):
                Heading("Sync preview")
                Badge(f"{result.get('count', 0)} items", variant="secondary")
            Text(f"{source_browser} → {target_browser}", css_class="text-sm text-muted-foreground")
            with Row(gap=2):
                Badge(
                    "folders preserved" if result.get("preserve_folders") else "flat import",
                    variant="outline",
                )
                Badge(
                    "target supports folders" if result.get("folder_support_on_target") else "flat target",
                    variant="outline",
                )
            DataTable(
                columns=[
                    DataTableColumn(key="title", header="Title"),
                    DataTableColumn(key="url", header="URL"),
                    DataTableColumn(key="folder_path", header="Folder"),
                ],
                rows=rows,
            )
    return app


@mcp.tool(app=True)
@HelpSystem.register_tool
async def backup_manager_ui(
    browsers: list[str] | None = None,
    dry_run: bool = True,
) -> PrefabApp:
    """List backup targets or preview/run batch backup results."""
    if dry_run:
        targets = (await list_backup_targets()).get("targets") or []
        if browsers:
            allowed = {b.lower() for b in browsers}
            targets = [t for t in targets if t["browser"] in allowed]
        rows = [
            {
                "browser": t.get("browser"),
                "profile": t.get("profile_name"),
                "family": t.get("browser_family"),
                "available": "yes" if t.get("available") else "no",
            }
            for t in targets
        ]
        with PrefabApp() as app:
            with Column(gap=4, css_class="p-6"):
                Heading("Backup targets")
                Text("Set dry_run=False on backup_restore.batch_backup to execute.", css_class="text-sm")
                DataTable(
                    columns=[
                        DataTableColumn(key="browser", header="Browser", sortable=True),
                        DataTableColumn(key="profile", header="Profile", sortable=True),
                        DataTableColumn(key="family", header="Family"),
                        DataTableColumn(key="available", header="Available", sortable=True),
                    ],
                    rows=rows,
                    search=True,
                )
        return app

    result = await batch_backup_profiles(browsers=browsers, dry_run=False)
    rows = [
        {
            "browser": item.get("browser"),
            "profile": item.get("profile_name"),
            "success": "yes" if item.get("success") else "no",
            "backup_path": item.get("backup_path") or item.get("error") or "",
        }
        for item in result.get("results") or []
    ]
    with PrefabApp() as app:
        with Column(gap=4, css_class="p-6"):
            with Row(gap=2, align="center"):
                Heading("Batch backup results")
                Badge(f"{result.get('succeeded', 0)}/{result.get('attempted', 0)} ok", variant="success")
            DataTable(
                columns=[
                    DataTableColumn(key="browser", header="Browser"),
                    DataTableColumn(key="profile", header="Profile"),
                    DataTableColumn(key="success", header="OK"),
                    DataTableColumn(key="backup_path", header="Path / Error"),
                ],
                rows=rows,
            )
    return app


@mcp.tool(app=True)
@HelpSystem.register_tool
async def import_execute_ui(
    import_path: str,
    target_browser: str,
    target_profile: str | None = None,
    import_format: str = "auto",
    dry_run: bool = True,
    limit: int = 100,
) -> PrefabApp:
    """Import bookmarks from file with visual result summary."""
    result = await import_bookmarks_from_file(
        import_path=import_path,
        import_format=import_format,
        target_browser=target_browser,
        target_profile=target_profile,
        dry_run=dry_run,
        limit=limit,
    )
    status = result.get("status") or ("error" if not result.get("success") else "done")
    if status == "error" or not result.get("success"):
        return _error_app(result.get("error") or "Import failed")

    with PrefabApp() as app:
        with Column(gap=4, css_class="p-6"):
            Heading("Import result" if not dry_run else "Import plan")
            with Card():
                with CardContent():
                    with Column(gap=2):
                        Text(f"Source: {import_path}")
                        Text(f"Target: {target_browser} / {target_profile or 'Default'}")
                        Text(f"Count: {result.get('count', 0)}")
                        if dry_run:
                            Text("Dry run — set dry_run=False to write bookmarks.")
                        else:
                            Text(f"Succeeded: {result.get('succeeded', 0)} / {result.get('attempted', 0)}")
    return app

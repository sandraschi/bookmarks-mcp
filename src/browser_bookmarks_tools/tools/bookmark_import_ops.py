"""Import bookmarks from export files into browsers or sidecar metadata."""

from __future__ import annotations

from typing import Any

from browser_bookmarks_tools.services.bookmark_import import metadata_rows_from_bookmarks, parse_bookmark_file
from browser_bookmarks_tools.services.browser.gecko_registry import is_gecko_browser
from browser_bookmarks_tools.services.browser.safari_registry import is_safari_browser
from browser_bookmarks_tools.services.metadata.sidecar_db import SidecarMetadataStore
from browser_bookmarks_tools.tools.chromium import add_chromium_bookmark, is_chromium_browser
from browser_bookmarks_tools.tools.firefox.links import add_bookmark as add_gecko_bookmark
from browser_bookmarks_tools.tools.safari import add_safari_bookmark


async def import_bookmarks_from_file(
    *,
    import_path: str,
    import_format: str = "auto",
    target_browser: str | None = None,
    target_profile: str | None = None,
    import_to_metadata: bool = False,
    preserve_folders: bool = True,
    dry_run: bool = True,
    limit: int = 1000,
) -> dict[str, Any]:
    parsed = parse_bookmark_file(import_path, import_format)
    if not parsed.get("success"):
        return parsed

    bookmarks = (parsed.get("bookmarks") or [])[:limit]
    result: dict[str, Any] = {
        "success": True,
        "operation": "import_bookmarks",
        "import_path": import_path,
        "import_format": parsed.get("import_format"),
        "count": len(bookmarks),
        "dry_run": dry_run,
    }

    if import_to_metadata or not target_browser:
        store = SidecarMetadataStore()
        rows = metadata_rows_from_bookmarks(
            bookmarks,
            browser=target_browser,
            profile_name=target_profile,
        )
        if dry_run:
            result["status"] = "planned"
            result["metadata_rows"] = len(rows)
            result["sample"] = rows[:5]
            return result
        meta_result = store.import_rows(rows, merge=True)
        result["metadata_import"] = meta_result
        if not target_browser:
            result["note"] = "Metadata imported to sidecar only (no target_browser)."
            return result

    target_key = (target_browser or "").lower()
    target_profile_name = target_profile or "Default"
    folder_capable = is_chromium_browser(target_key) or is_safari_browser(target_key)

    planned: list[dict[str, Any]] = []
    for bookmark in bookmarks:
        folder_path = bookmark.get("folder_path") or ""
        folder = None
        if preserve_folders and folder_capable and folder_path:
            folder = folder_path.replace("\\", "/").strip("/")
            if folder_capable and is_safari_browser(target_key):
                folder = folder.split("/")[-1] if folder else None
        planned.append(
            {
                "title": bookmark.get("title") or bookmark.get("url"),
                "url": bookmark.get("url"),
                "folder": folder,
            }
        )

    if dry_run:
        result["status"] = "planned"
        result["target_browser"] = target_key
        result["target_profile"] = target_profile_name
        result["sample"] = planned[:5]
        return result

    successes = 0
    failures: list[dict[str, Any]] = []
    for item in planned:
        try:
            if is_gecko_browser(target_key):
                res = await add_gecko_bookmark(
                    url=item["url"],
                    title=item["title"],
                    profile_name=target_profile_name,
                    browser_id=target_key,
                )
            elif is_chromium_browser(target_key):
                res = await add_chromium_bookmark(
                    target_key,
                    title=item["title"],
                    url=item["url"],
                    folder=item.get("folder"),
                    profile_name=target_profile_name,
                )
            elif is_safari_browser(target_key):
                res = await add_safari_bookmark(
                    title=item["title"],
                    url=item["url"],
                    folder=item.get("folder"),
                )
            else:
                failures.append({"item": item, "message": f"Unsupported target browser: {target_browser}"})
                continue

            if res.get("success") or res.get("status") in ("success", "created", "updated"):
                successes += 1
            else:
                failures.append({"item": item, "message": res.get("error") or res.get("message") or "unknown error"})
        except Exception as exc:
            failures.append({"item": item, "message": str(exc)})

    result["status"] = "done"
    result["target_browser"] = target_key
    result["target_profile"] = target_profile_name
    result["attempted"] = len(planned)
    result["succeeded"] = successes
    result["failed"] = len(failures)
    result["failures"] = failures[:10]
    return result

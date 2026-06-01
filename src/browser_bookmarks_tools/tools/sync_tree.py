"""Folder-aware cross-browser bookmark sync helpers."""

from __future__ import annotations

from typing import Any

from browser_bookmarks_tools.services.browser.gecko_registry import is_gecko_browser
from browser_bookmarks_tools.services.browser.safari_registry import is_safari_browser
from browser_bookmarks_tools.tools.bookmark_loader import load_browser_bookmarks
from browser_bookmarks_tools.tools.chromium import add_chromium_bookmark, is_chromium_browser
from browser_bookmarks_tools.tools.firefox.links import add_bookmark as add_gecko_bookmark
from browser_bookmarks_tools.tools.safari import add_safari_bookmark


def _folder_for_write(folder_path: str | None, *, preserve_folders: bool) -> str | None:
    if not preserve_folders or not folder_path:
        return None
    cleaned = folder_path.replace("\\", "/").strip("/")
    return cleaned or None


async def sync_bookmarks_with_folders(
    *,
    source_browser: str,
    target_browser: str,
    source_profile: str | None = None,
    target_profile: str | None = None,
    dry_run: bool = True,
    limit: int = 1000,
    preserve_folders: bool = True,
) -> dict[str, Any]:
    loaded = await load_browser_bookmarks(source_browser, source_profile, limit=limit)
    if not loaded.get("success"):
        return {
            "status": "error",
            "error_code": "SYNC_READ_FAILED",
            "error": loaded.get("error") or "Failed to read source bookmarks",
            "source": source_browser,
            "target": target_browser,
        }

    bookmarks = loaded.get("bookmarks") or []
    target_key = target_browser.lower()
    folder_capable = is_chromium_browser(target_key) or is_safari_browser(target_key)

    planned: list[dict[str, Any]] = []
    for bookmark in bookmarks[:limit]:
        planned.append(
            {
                "title": bookmark.get("title") or bookmark.get("url"),
                "url": bookmark.get("url"),
                "folder_path": bookmark.get("folder_path") or "",
            }
        )

    if dry_run:
        return {
            "status": "planned",
            "source": source_browser,
            "target": target_browser,
            "source_profile": source_profile,
            "target_profile": target_profile or "Default",
            "count": len(planned),
            "preserve_folders": preserve_folders,
            "folder_support_on_target": folder_capable,
            "dry_run": True,
            "sample": planned[:5],
        }

    successes = 0
    failures: list[dict[str, Any]] = []
    target_profile_name = target_profile or "Default"

    for item in planned:
        title = item["title"]
        url = item["url"]
        folder = _folder_for_write(item.get("folder_path"), preserve_folders=preserve_folders and folder_capable)
        try:
            if is_gecko_browser(target_key):
                res = await add_gecko_bookmark(
                    url=url,
                    title=title,
                    profile_name=target_profile_name,
                    browser_id=target_key,
                )
            elif is_chromium_browser(target_key):
                res = await add_chromium_bookmark(
                    target_key,
                    title=title,
                    url=url,
                    folder=folder,
                    profile_name=target_profile_name,
                )
            elif is_safari_browser(target_key):
                folder_name = folder.split("/")[-1] if folder else None
                res = await add_safari_bookmark(title=title, url=url, folder=folder_name)
            else:
                failures.append({"item": item, "message": f"Unsupported target browser: {target_browser}"})
                continue

            if res.get("success") or res.get("status") in ("success", "created", "updated"):
                successes += 1
            else:
                failures.append({"item": item, "message": res.get("error") or res.get("message") or "unknown error"})
        except Exception as exc:
            failures.append({"item": item, "message": str(exc)})

    return {
        "status": "done",
        "source": source_browser,
        "target": target_browser,
        "source_profile": source_profile,
        "target_profile": target_profile_name,
        "attempted": len(planned),
        "succeeded": successes,
        "failed": len(failures),
        "preserve_folders": preserve_folders,
        "folder_support_on_target": folder_capable,
        "failures": failures[:10],
    }

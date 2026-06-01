"""Load normalized bookmarks from any supported browser family."""

from __future__ import annotations

from typing import Any

from browser_bookmarks_tools.services.bookmark_normalize import normalize_bookmarks
from browser_bookmarks_tools.services.browser.gecko_registry import is_gecko_browser
from browser_bookmarks_tools.services.browser.safari_registry import is_safari_browser
from browser_bookmarks_tools.tools.chromium import is_chromium_browser, list_chromium_bookmarks


async def load_browser_bookmarks(
    browser: str,
    profile_name: str | None = None,
    *,
    limit: int = 10_000,
    bookmarks_path: str | None = None,
) -> dict[str, Any]:
    browser_key = browser.lower()

    if is_gecko_browser(browser_key):
        from browser_bookmarks_tools.tools.firefox.links import list_bookmarks

        result = await list_bookmarks(
            profile_name=profile_name,
            browser_id=browser_key,
            limit=limit,
            offset=0,
        )
        if result.get("status") != "success":
            return {
                "success": False,
                "browser": browser_key,
                "browser_family": "gecko",
                "error": result.get("message") or "Failed to load gecko bookmarks",
            }
        bookmarks = normalize_bookmarks(result.get("bookmarks") or [], browser_family="gecko")
        return {
            "success": True,
            "browser": browser_key,
            "browser_family": "gecko",
            "profile_name": profile_name,
            "bookmarks": bookmarks,
            "count": len(bookmarks),
        }

    if is_chromium_browser(browser_key):
        result = await list_chromium_bookmarks(
            browser_key,
            profile_name=profile_name,
            bookmarks_path=bookmarks_path,
        )
        if not result.get("success"):
            return result
        bookmarks = normalize_bookmarks(result.get("bookmarks") or [], browser_family="chromium")
        return {
            "success": True,
            "browser": browser_key,
            "browser_family": "chromium",
            "profile_name": result.get("profile_name"),
            "bookmarks": bookmarks,
            "count": len(bookmarks),
        }

    if is_safari_browser(browser_key):
        from browser_bookmarks_tools.tools.safari import list_safari_bookmarks

        result = await list_safari_bookmarks(bookmarks_path=bookmarks_path)
        if not result.get("success"):
            return result
        bookmarks = normalize_bookmarks(result.get("bookmarks") or [], browser_family="safari")
        return {
            "success": True,
            "browser": "safari",
            "browser_family": "safari",
            "profile_name": "default",
            "bookmarks": bookmarks,
            "count": len(bookmarks),
        }

    return {
        "success": False,
        "browser": browser_key,
        "error": f"Unsupported browser for bookmark load: {browser}",
    }

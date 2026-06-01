"""
Browser bookmark management services.

This package provides browser-specific bookmark management implementations
for various browsers including Firefox, Chrome, Edge, Brave, and Safari.
"""

from browser_bookmarks_tools.services.browser.base_browser import (
    BaseBrowserManager,
)
from browser_bookmarks_tools.services.browser.chrome_core import ChromeManager
from browser_bookmarks_tools.services.browser.chromium_manager import ChromiumManager
from browser_bookmarks_tools.services.browser.chromium_registry import (
    get_chromium_spec,
    is_chromium_browser,
    list_chromium_browser_ids,
    list_chromium_browsers,
)
from browser_bookmarks_tools.services.browser.gecko_paths import (
    parse_profiles_ini,
    resolve_places_db_path,
    resolve_profile_directory,
)
from browser_bookmarks_tools.services.browser.gecko_registry import (
    get_gecko_spec,
    is_gecko_browser,
    list_gecko_browser_ids,
    list_gecko_browsers,
)

__all__ = [
    "BaseBrowserManager",
    "ChromeManager",
    "ChromiumManager",
    "get_chromium_spec",
    "get_gecko_spec",
    "is_chromium_browser",
    "is_gecko_browser",
    "list_chromium_browser_ids",
    "list_chromium_browsers",
    "list_gecko_browser_ids",
    "list_gecko_browsers",
    "parse_profiles_ini",
    "resolve_places_db_path",
    "resolve_profile_directory",
]

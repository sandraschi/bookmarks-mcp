"""Browser registry exports."""

from browser_bookmarks_tools.services.browser.chromium_registry import (
    get_chromium_spec,
    is_chromium_browser,
    list_chromium_browser_ids,
    list_chromium_browsers,
)
from browser_bookmarks_tools.services.browser.gecko_registry import (
    get_gecko_spec,
    is_gecko_browser,
    list_gecko_browser_ids,
    list_gecko_browsers,
)
from browser_bookmarks_tools.services.browser.safari_registry import (
    is_safari_browser,
    list_safari_browsers,
    safari_supported_on_platform,
)

__all__ = [
    "get_chromium_spec",
    "get_gecko_spec",
    "is_chromium_browser",
    "is_gecko_browser",
    "is_safari_browser",
    "list_chromium_browser_ids",
    "list_chromium_browsers",
    "list_gecko_browser_ids",
    "list_gecko_browsers",
    "list_safari_browsers",
    "safari_supported_on_platform",
]

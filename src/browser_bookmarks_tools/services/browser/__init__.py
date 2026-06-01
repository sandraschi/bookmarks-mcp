"""
Browser bookmark management services.

This package provides browser-specific bookmark management implementations
for various browsers including Firefox, Chrome, Edge, Brave, and Safari.
"""

from browser_bookmarks_tools.services.browser.base_browser import (
    BaseBrowserManager,
)
from browser_bookmarks_tools.services.browser.chrome_core import ChromeManager

__all__ = ["BaseBrowserManager", "ChromeManager"]

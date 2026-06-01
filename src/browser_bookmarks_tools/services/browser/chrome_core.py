"""
Chrome browser bookmark management implementation.

Thin wrapper around ChromiumManager for backward compatibility with chrome_profiles.
"""

from browser_bookmarks_tools.services.browser.chromium_manager import ChromiumManager


class ChromeManager(ChromiumManager):
    """Google Chrome bookmark manager (registry id: chrome)."""

    def __init__(self) -> None:
        super().__init__("chrome")

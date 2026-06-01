"""Firefox status checking utilities.

DEPRECATED: Individual tools deprecated. Use firefox_profiles portmanteau instead.
- is_firefox_running() ÔåÆ firefox_profiles(operation='check_firefox_status')
- check_firefox_database_access_safe() ÔåÆ firefox_profiles(operation='check_firefox_status')
"""

from pathlib import Path
from typing import Any

from browser_bookmarks_tools.services.browser.gecko_status import GeckoStatusChecker


class FirefoxStatusChecker:
    """Comprehensive Gecko status checking (default browser: Firefox)."""

    @staticmethod
    def is_firefox_running() -> dict[str, Any]:
        return GeckoStatusChecker.is_browser_running("firefox")

    @staticmethod
    def is_browser_running(browser_id: str) -> dict[str, Any]:
        return GeckoStatusChecker.is_browser_running(browser_id)

    @staticmethod
    def check_database_access_safe(profile_path: Path | None = None, browser_id: str = "firefox") -> dict[str, Any]:
        """Check if it's safe to access Gecko bookmark databases."""
        return GeckoStatusChecker.check_database_access_safe(browser_id, profile_path)


# DEPRECATED: Use firefox_profiles(operation='check_firefox_status') instead
def is_firefox_running() -> dict[str, Any]:
    """
    Check if Firefox is currently running.

    Returns detailed status information about Firefox processes.

    Returns:
        Dict containing Firefox running status, process count, and details
    """
    return FirefoxStatusChecker.is_firefox_running()


# DEPRECATED: Use firefox_profiles(operation='check_firefox_status') instead
def check_firefox_database_access_safe(profile_path: str | None = None) -> dict[str, Any]:
    """
    Check if it's safe to access Firefox bookmark databases.

    Args:
        profile_path: Optional path to Firefox profile directory

    Returns:
        Dict containing safety status and recommendations
    """
    path_obj = Path(profile_path) if profile_path else None
    return FirefoxStatusChecker.check_database_access_safe(path_obj)

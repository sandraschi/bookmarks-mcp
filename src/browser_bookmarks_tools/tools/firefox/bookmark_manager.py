"""Core bookmark management functionality with enhanced safety checks.

DEPRECATED: Individual tools deprecated. Use firefox_bookmarks portmanteau instead.
- list_bookmarks() → firefox_bookmarks(operation='list_bookmarks')
"""

from pathlib import Path
from typing import Any

# NOTE: @mcp.tool decorators removed - functionality moved to firefox_bookmarks portmanteau
from .db import FirefoxDB
from .exceptions import FirefoxNotClosedError
from .status import FirefoxStatusChecker
from .utils import get_profile_directory

_BOOKMARK_SELECT = """
    SELECT b.id, b.title, p.url, b.dateAdded, b.lastModified, b.parent
    FROM moz_bookmarks b
    JOIN moz_places p ON b.fk = p.id
    WHERE b.type = 1
"""


class BookmarkManager:
    """Handles bookmark operations with safety checks."""

    def __init__(self, profile_path: Path | None = None):
        self.profile_path = profile_path
        self.db = None

    def _ensure_safe_access(self) -> dict[str, Any]:
        """Ensure it's safe to access the database."""
        return FirefoxStatusChecker.check_database_access_safe(self.profile_path)

    def _get_db_connection(self) -> FirefoxDB:
        """Get database connection with safety checks."""
        if self.db is None:
            safety_check = self._ensure_safe_access()
            if not safety_check["safe"]:
                raise FirefoxNotClosedError(safety_check["message"])
            self.db = FirefoxDB(self.profile_path)
        return self.db

    def get_bookmarks(self, folder_id: int | None = None) -> list[dict[str, Any]]:
        """Retrieve bookmarks, optionally filtered by folder."""
        db = self._get_db_connection()
        query = _BOOKMARK_SELECT
        params: list[Any] = []
        if folder_id is not None:
            query += " AND b.parent = ?"
            params.append(folder_id)

        cursor = db.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def get_bookmark(self, bookmark_id: int) -> dict[str, Any] | None:
        """Retrieve a single bookmark by moz_bookmarks id."""
        db = self._get_db_connection()
        query = _BOOKMARK_SELECT + " AND b.id = ?"
        cursor = db.execute(query, (bookmark_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# DEPRECATED: Use firefox_bookmarks(operation='list_bookmarks') instead
async def list_bookmarks(profile_name: str | None = None, folder_id: int | None = None) -> dict[str, Any]:
    """List bookmarks with optional folder filtering.

    Args:
        profile_name: Firefox profile name to list bookmarks from (optional)
        folder_id: Specific folder ID to list bookmarks from (optional)

    Note: Firefox must be closed to access bookmark databases safely.
    """
    try:
        # Get profile path
        profile_path = None
        if profile_name:
            profile_path = get_profile_directory(profile_name)
            if not profile_path:
                return {"status": "error", "message": f"Profile '{profile_name}' not found"}

        manager = BookmarkManager(profile_path)
        bookmarks = manager.get_bookmarks(folder_id)

        response = {
            "status": "success",
            "profile_used": profile_name or "default",
            "count": len(bookmarks),
            "bookmarks": bookmarks,
        }

        if len(bookmarks) == 0:
            response["note"] = "No bookmarks found. This could mean the profile is empty or Firefox is running."

        return response

    except FirefoxNotClosedError as e:
        return {
            "status": "error",
            "message": str(e),
            "firefox_status": FirefoxStatusChecker.is_firefox_running(),
            "solution": "Close Firefox completely and try again",
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list bookmarks: {e!s}"}

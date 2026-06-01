"""Literal aliases for bookmark portmanteau `operation` parameters."""

from __future__ import annotations

from typing import Literal

ChromeProfilesOperation = Literal[
    "get_chrome_profiles",
    "get_profile_info",
    "validate_profile",
    "is_chrome_running",
    "get_profile_directory",
    "get_bookmarks_db_path",
    "get_chrome_platform",
    "get_database_info",
    "check_chrome_status",
    "backup_profile",
    "restore_profile",
    "create_profile",
    "delete_profile",
    "switch_profile",
]

FirefoxProfilesOperation = Literal[
    "get_firefox_profiles",
    "create_firefox_profile",
    "delete_firefox_profile",
    "create_loaded_profile",
    "create_portmanteau_profile",
    "suggest_portmanteau_profiles",
    "create_loaded_profile_from_preset",
    "check_firefox_status",
]

FirefoxCuratedOperation = Literal[
    "get_curated_source",
    "list_curated_sources",
    "list_curated_bookmark_sources",
]

BrowserBookmarkOperation = Literal[
    "list_bookmarks",
    "get_bookmark",
    "add_bookmark",
    "edit_bookmark",
    "delete_bookmark",
    "search",
    "search_bookmarks",
    "sync_bookmarks",
    "find_duplicates",
    "export_bookmarks",
    "batch_update_tags",
    "remove_unused_tags",
    "list_tags",
    "find_similar_tags",
    "merge_tags",
    "clean_up_tags",
    "find_old_bookmarks",
    "find_forgotten_bookmarks",
    "refresh_bookmarks",
    "get_bookmark_stats",
    "find_broken_links",
]

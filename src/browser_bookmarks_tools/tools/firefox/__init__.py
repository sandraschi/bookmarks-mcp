"""Firefox bookmark management tools."""

# Import the global MCP instance from the central config
from browser_bookmarks_tools.config.mcp_config import mcp

from .age_analyzer import find_forgotten_bookmarks, find_old_bookmarks, get_bookmark_stats

# Import AI portmanteau tool
from .ai_portmanteau import ai_bookmark_portmanteau

# Import bulk operations
from .bulk_operations import batch_update_tags, export_bookmarks

# Import core functionality
from .core import get_firefox_profiles
from .folder_based_tagging import batch_tag_from_folder, tag_from_folder

# Import other tools
from .link_checker import find_broken_links
from .links import add_bookmark, get_bookmark, list_bookmarks

# Import search functionality
from .search_tools import BookmarkSearcher, find_duplicates, search_bookmarks

# Import tag management
from .tag_manager import TagManager, clean_up_tags, find_similar_tags, list_tags, merge_tags
from .year_based_tagging import batch_tag_from_year, tag_from_year

# Category constant for help system
TOOL_CATEGORY = "firefox"


# Tools are registered using the @mcp.tool() decorator in their respective modules
# The mcp instance is imported from the central config

# Export all tools
__all__ = [
    "BookmarkSearcher",
    "TagManager",
    "add_bookmark",
    "ai_bookmark_portmanteau",  # AI portmanteau tool
    "batch_tag_from_folder",
    "batch_tag_from_year",
    "batch_update_tags",
    "clean_up_tags",
    "export_bookmarks",
    "find_broken_links",
    "find_duplicates",
    "find_forgotten_bookmarks",
    "find_old_bookmarks",
    "find_similar_tags",
    "get_bookmark",
    "get_bookmark_stats",
    "get_firefox_profiles",
    "list_bookmarks",
    "list_tags",
    "mcp",  # Export the mcp instance
    "merge_tags",
    "search_bookmarks",
    "tag_from_folder",
    "tag_from_year",
]

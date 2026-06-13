"""Sidecar metadata storage — enrichment beyond native browser bookmark files."""

from browser_bookmarks_tools.services.metadata.enrich import enrich_bookmark, enrich_bookmarks
from browser_bookmarks_tools.services.metadata.sidecar_db import SidecarMetadataStore

__all__ = ["SidecarMetadataStore", "enrich_bookmark", "enrich_bookmarks"]

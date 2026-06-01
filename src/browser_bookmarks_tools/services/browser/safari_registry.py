"""Safari bookmark storage registry (macOS WebKit plist)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SafariBrowserSpec:
    id: str = "safari"
    display_name: str = "Apple Safari"
    process_names: frozenset[str] = frozenset({"Safari", "com.apple.WebKit.WebContent"})


SAFARI_SPEC = SafariBrowserSpec()


def is_safari_browser(browser_id: str) -> bool:
    return browser_id.lower().strip() in {"safari", "apple_safari"}


def safari_supported_on_platform() -> bool:
    return sys.platform == "darwin"


def resolve_safari_bookmarks_plist() -> Path | None:
    if not safari_supported_on_platform():
        return None
    path = Path.home() / "Library" / "Safari" / "Bookmarks.plist"
    return path if path.exists() else None


def list_safari_browsers() -> list[dict[str, str | bool]]:
    return [
        {
            "id": SAFARI_SPEC.id,
            "display_name": SAFARI_SPEC.display_name,
            "supported_on_platform": safari_supported_on_platform(),
        }
    ]

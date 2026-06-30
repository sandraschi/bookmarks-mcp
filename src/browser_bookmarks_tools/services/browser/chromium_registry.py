"""Registry of Chromium-family browsers and their on-disk profile locations."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ProfileLayout(StrEnum):
    """How a browser lays out bookmark storage on disk."""

    CHROMIUM_USER_DATA = "chromium_user_data"
    FLAT_PROFILE = "flat_profile"


@dataclass(frozen=True)
class ChromiumBrowserSpec:
    id: str
    display_name: str
    user_data_dir_candidates: tuple[str, ...]
    process_names: frozenset[str]
    profile_layout: ProfileLayout = ProfileLayout.CHROMIUM_USER_DATA
    default_profile: str = "Default"


def _expand_path(template: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(template)))


def _platform_paths(windows: list[str], darwin: list[str], linux: list[str]) -> tuple[str, ...]:
    if sys.platform == "win32":
        return tuple(windows)
    if sys.platform == "darwin":
        return tuple(darwin)
    return tuple(linux)


def _build_specs() -> dict[str, ChromiumBrowserSpec]:
    local = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    home = str(Path.home())

    return {
        "chrome": ChromiumBrowserSpec(
            id="chrome",
            display_name="Google Chrome",
            user_data_dir_candidates=_platform_paths(
                [rf"{local}\Google\Chrome\User Data"],
                [f"{home}/Library/Application Support/Google/Chrome"],
                [f"{home}/.config/google-chrome"],
            ),
            process_names=frozenset({"chrome.exe", "Google Chrome", "chrome"}),
        ),
        "edge": ChromiumBrowserSpec(
            id="edge",
            display_name="Microsoft Edge",
            user_data_dir_candidates=_platform_paths(
                [rf"{local}\Microsoft\Edge\User Data"],
                [f"{home}/Library/Application Support/Microsoft Edge"],
                [f"{home}/.config/microsoft-edge"],
            ),
            process_names=frozenset({"msedge.exe", "Microsoft Edge", "msedge"}),
        ),
        "brave": ChromiumBrowserSpec(
            id="brave",
            display_name="Brave",
            user_data_dir_candidates=_platform_paths(
                [rf"{local}\BraveSoftware\Brave-Browser\User Data"],
                [f"{home}/Library/Application Support/BraveSoftware/Brave-Browser"],
                [f"{home}/.config/BraveSoftware/Brave-Browser"],
            ),
            process_names=frozenset({"brave.exe", "Brave Browser", "brave"}),
        ),
        "opera": ChromiumBrowserSpec(
            id="opera",
            display_name="Opera",
            user_data_dir_candidates=_platform_paths(
                [rf"{appdata}\Opera Software\Opera Stable"],
                [f"{home}/Library/Application Support/com.operasoftware.Opera"],
                [f"{home}/.config/opera"],
            ),
            process_names=frozenset({"opera.exe", "Opera", "opera"}),
            profile_layout=ProfileLayout.FLAT_PROFILE,
        ),
        "opera_gx": ChromiumBrowserSpec(
            id="opera_gx",
            display_name="Opera GX",
            user_data_dir_candidates=_platform_paths(
                [rf"{appdata}\Opera Software\Opera GX Stable"],
                [f"{home}/Library/Application Support/com.operasoftware.OperaGX"],
                [f"{home}/.config/opera-gx"],
            ),
            process_names=frozenset({"opera.exe", "Opera GX", "opera"}),
            profile_layout=ProfileLayout.FLAT_PROFILE,
        ),
        "vivaldi": ChromiumBrowserSpec(
            id="vivaldi",
            display_name="Vivaldi",
            user_data_dir_candidates=_platform_paths(
                [rf"{local}\Vivaldi\User Data"],
                [f"{home}/Library/Application Support/Vivaldi"],
                [f"{home}/.config/vivaldi"],
            ),
            process_names=frozenset({"vivaldi.exe", "Vivaldi", "vivaldi"}),
        ),
        "chromium": ChromiumBrowserSpec(
            id="chromium",
            display_name="Chromium",
            user_data_dir_candidates=_platform_paths(
                [rf"{local}\Chromium\User Data"],
                [f"{home}/Library/Application Support/Chromium"],
                [f"{home}/.config/chromium"],
            ),
            process_names=frozenset({"chromium.exe", "Chromium", "chromium"}),
        ),
        "arc": ChromiumBrowserSpec(
            id="arc",
            display_name="Arc",
            user_data_dir_candidates=(
                f"{home}/Library/Application Support/Arc/User Data",
                rf"{local}\Arc\User Data",
            ),
            process_names=frozenset({"Arc", "arc"}),
        ),
        "comet": ChromiumBrowserSpec(
            id="comet",
            display_name="Perplexity Comet",
            user_data_dir_candidates=_platform_paths(
                [rf"{local}\Perplexity\Comet\User Data"],
                [f"{home}/Library/Application Support/Perplexity/Comet/User Data"],
                [f"{home}/.config/Perplexity/Comet"],
            ),
            process_names=frozenset({"comet.exe", "Comet", "comet"}),
        ),
        "dia": ChromiumBrowserSpec(
            id="dia",
            display_name="Dia",
            user_data_dir_candidates=(
                f"{home}/Library/Application Support/Dia/User Data",
                f"{home}/Library/Application Support/The Browser Company/Dia/User Data",
            ),
            process_names=frozenset({"Dia", "dia"}),
        ),
    }


CHROMIUM_BROWSER_SPECS: dict[str, ChromiumBrowserSpec] = _build_specs()


def list_chromium_browser_ids() -> list[str]:
    return sorted(CHROMIUM_BROWSER_SPECS.keys())


def list_chromium_browsers() -> list[dict[str, str]]:
    return [
        {"id": spec.id, "display_name": spec.display_name, "profile_layout": spec.profile_layout.value}
        for spec in CHROMIUM_BROWSER_SPECS.values()
    ]


def get_chromium_spec(browser_id: str) -> ChromiumBrowserSpec:
    key = browser_id.lower().strip()
    spec = CHROMIUM_BROWSER_SPECS.get(key)
    if spec is None:
        raise ValueError(f"Unknown Chromium browser: {browser_id}. Supported: {', '.join(list_chromium_browser_ids())}")
    return spec


def is_chromium_browser(browser_id: str) -> bool:
    return browser_id.lower().strip() in CHROMIUM_BROWSER_SPECS


def resolve_user_data_dir(browser_id: str) -> Path | None:
    spec = get_chromium_spec(browser_id)
    for candidate in spec.user_data_dir_candidates:
        path = _expand_path(candidate)
        if path.exists():
            return path
    return None


def resolve_bookmarks_file(browser_id: str, profile_name: str | None = None) -> Path | None:
    spec = get_chromium_spec(browser_id)
    user_data = resolve_user_data_dir(browser_id)
    if user_data is None:
        return None

    profile = profile_name or spec.default_profile

    if spec.profile_layout == ProfileLayout.FLAT_PROFILE:
        bookmarks = user_data / "Bookmarks"
        return bookmarks if bookmarks.exists() else None

    bookmarks = user_data / profile / "Bookmarks"
    if bookmarks.exists():
        return bookmarks

    if profile == spec.default_profile:
        default_bookmarks = user_data / spec.default_profile / "Bookmarks"
        if default_bookmarks.exists():
            return default_bookmarks

    return None


def legacy_default_bookmark_paths(browser_id: str) -> list[str]:
    """Backward-compatible path strings for modules that still use path lists."""
    spec = get_chromium_spec(browser_id)
    paths: list[str] = []
    for candidate in spec.user_data_dir_candidates:
        base = candidate
        if spec.profile_layout == ProfileLayout.FLAT_PROFILE:
            paths.append(f"{base}/Bookmarks")
        else:
            paths.append(f"{base}/{spec.default_profile}/Bookmarks")
    return paths

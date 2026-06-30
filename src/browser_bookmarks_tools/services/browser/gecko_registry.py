"""Registry of Gecko-family browsers (places.sqlite via profiles.ini or fixed profile)."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class GeckoProfileLayout(StrEnum):
    PROFILES_INI = "profiles_ini"
    SINGLE_PROFILE = "single_profile"


@dataclass(frozen=True)
class GeckoBrowserSpec:
    id: str
    display_name: str
    install_root_candidates: tuple[str, ...]
    process_names: frozenset[str]
    profile_layout: GeckoProfileLayout = GeckoProfileLayout.PROFILES_INI
    read_only_recommended: bool = False
    notes: str | None = None


def _platform_paths(windows: list[str], darwin: list[str], linux: list[str]) -> tuple[str, ...]:
    if sys.platform == "win32":
        return tuple(windows)
    if sys.platform == "darwin":
        return tuple(darwin)
    return tuple(linux)


def _build_specs() -> dict[str, GeckoBrowserSpec]:
    appdata = os.environ.get("APPDATA", "")
    local = os.environ.get("LOCALAPPDATA", "")
    home = str(Path.home())

    return {
        "firefox": GeckoBrowserSpec(
            id="firefox",
            display_name="Mozilla Firefox",
            install_root_candidates=_platform_paths(
                [rf"{appdata}\Mozilla\Firefox"],
                [f"{home}/Library/Application Support/Firefox"],
                [f"{home}/.mozilla/firefox"],
            ),
            process_names=frozenset({"firefox.exe", "firefox", "Firefox"}),
        ),
        "zen": GeckoBrowserSpec(
            id="zen",
            display_name="Zen Browser",
            install_root_candidates=_platform_paths(
                [rf"{appdata}\zen"],
                [f"{home}/Library/Application Support/zen"],
                [f"{home}/.zen"],
            ),
            process_names=frozenset({"zen.exe", "zen", "Zen"}),
        ),
        "librewolf": GeckoBrowserSpec(
            id="librewolf",
            display_name="LibreWolf",
            install_root_candidates=_platform_paths(
                [rf"{appdata}\LibreWolf"],
                [f"{home}/Library/Application Support/LibreWolf"],
                [f"{home}/.librewolf"],
            ),
            process_names=frozenset({"librewolf.exe", "librewolf", "LibreWolf"}),
        ),
        "waterfox": GeckoBrowserSpec(
            id="waterfox",
            display_name="Waterfox",
            install_root_candidates=_platform_paths(
                [rf"{appdata}\Waterfox"],
                [f"{home}/Library/Application Support/Waterfox"],
                [f"{home}/.waterfox"],
            ),
            process_names=frozenset({"waterfox.exe", "waterfox", "Waterfox"}),
        ),
        "floorp": GeckoBrowserSpec(
            id="floorp",
            display_name="Floorp",
            install_root_candidates=_platform_paths(
                [rf"{appdata}\Floorp\Profiles"],
                [f"{home}/Library/Application Support/Floorp/Profiles"],
                [f"{home}/.floorp"],
            ),
            process_names=frozenset({"floorp.exe", "floorp", "Floorp"}),
        ),
        "tor": GeckoBrowserSpec(
            id="tor",
            display_name="Tor Browser",
            install_root_candidates=_platform_paths(
                [rf"{local}\Tor Browser\Browser\TorBrowser\Data\Browser\profile.default"],
                [f"{home}/Library/Application Support/TorBrowser-Data/Browser/profile.default"],
                [
                    f"{home}/.local/share/torbrowser/tbb/x86_64/tor-browser/Browser/TorBrowser/Data/Browser/profile.default"
                ],
            ),
            process_names=frozenset({"firefox.exe", "tor.exe", "tor browser", "Tor Browser"}),
            profile_layout=GeckoProfileLayout.SINGLE_PROFILE,
            read_only_recommended=True,
            notes="Single isolated profile; writes affect anonymity profile — prefer read-only ops.",
        ),
    }


GECKO_BROWSER_SPECS: dict[str, GeckoBrowserSpec] = _build_specs()


def list_gecko_browser_ids() -> list[str]:
    return sorted(GECKO_BROWSER_SPECS.keys())


def list_gecko_browsers() -> list[dict[str, str | bool | None]]:
    return [
        {
            "id": spec.id,
            "display_name": spec.display_name,
            "profile_layout": spec.profile_layout.value,
            "read_only_recommended": spec.read_only_recommended,
            "notes": spec.notes,
        }
        for spec in GECKO_BROWSER_SPECS.values()
    ]


def get_gecko_spec(browser_id: str) -> GeckoBrowserSpec:
    key = browser_id.lower().strip()
    spec = GECKO_BROWSER_SPECS.get(key)
    if spec is None:
        raise ValueError(f"Unknown Gecko browser: {browser_id}. Supported: {', '.join(list_gecko_browser_ids())}")
    return spec


def is_gecko_browser(browser_id: str) -> bool:
    return browser_id.lower().strip() in GECKO_BROWSER_SPECS


def resolve_install_root(browser_id: str) -> Path | None:
    spec = get_gecko_spec(browser_id)
    for candidate in spec.install_root_candidates:
        path = Path(os.path.expandvars(os.path.expanduser(candidate)))
        if path.exists():
            return path
    return None

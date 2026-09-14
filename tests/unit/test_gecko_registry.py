from pathlib import Path

import pytest

from browser_bookmarks_tools.services.browser.gecko_paths import (
    parse_profiles_ini,
    resolve_places_db_path,
    resolve_profile_directory,
)
from browser_bookmarks_tools.services.browser.gecko_registry import (
    GeckoProfileLayout,
    get_gecko_spec,
    is_gecko_browser,
    list_gecko_browser_ids,
)


def test_gecko_registry_includes_forks():
    ids = list_gecko_browser_ids()
    assert "firefox" in ids
    assert "zen" in ids
    assert "librewolf" in ids
    assert "tor" in ids


def test_is_gecko_browser():
    assert is_gecko_browser("firefox")
    assert is_gecko_browser("zen")
    assert not is_gecko_browser("chrome")
    assert not is_gecko_browser("comet")


def test_tor_single_profile_layout():
    spec = get_gecko_spec("tor")
    assert spec.profile_layout == GeckoProfileLayout.SINGLE_PROFILE
    assert spec.read_only_recommended is True


def test_parse_profiles_ini_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "Mozilla" / "Firefox"
    profile_dir = root / "abc.default"
    profile_dir.mkdir(parents=True)
    (profile_dir / "places.sqlite").write_bytes(b"sqlite")

    profiles_ini = root / "profiles.ini"
    profiles_ini.write_text(
        """
[Install4F96D1932A9F858E]
Default=abc.default
Locked=1

[Profile0]
Name=default
IsRelative=1
Path=abc.default
Default=1
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "browser_bookmarks_tools.services.browser.gecko_paths.resolve_install_root",
        lambda browser_id: root if browser_id == "firefox" else None,
    )

    profiles = parse_profiles_ini("firefox")
    assert "default" in profiles
    assert resolve_profile_directory("firefox", "default") == profile_dir
    assert resolve_places_db_path("firefox", "default") == profile_dir / "places.sqlite"


def test_resolve_profile_directory_prefers_install_default_over_stale_legacy_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Reproduces a real bug: profiles.ini can carry a legacy [ProfileN] Default=1
    flag that's gone stale (profile emptied/abandoned) alongside a modern
    [InstallXXXX] Default= that correctly points at the profile Firefox
    actually uses. The install section must win, or auto-detection resolves
    to a profile with no places.sqlite ("places db not found, no bookmarks")
    while the real bookmarks sit in the other profile untouched.
    """
    root = tmp_path / "Mozilla" / "Firefox"
    stale_dir = root / "Profiles" / "u8g9sf3x.default"
    stale_dir.mkdir(parents=True)
    # No places.sqlite here - this profile was abandoned.

    real_dir = root / "Profiles" / "airiswdq.default-release"
    real_dir.mkdir(parents=True)
    (real_dir / "places.sqlite").write_bytes(b"sqlite")

    profiles_ini = root / "profiles.ini"
    profiles_ini.write_text(
        """
[Install308046B0AF4A39CB]
Default=Profiles/airiswdq.default-release
Locked=1

[Profile1]
Name=default
IsRelative=1
Path=Profiles/u8g9sf3x.default
Default=1

[Profile0]
Name=default-release
IsRelative=1
Path=Profiles/airiswdq.default-release
StoreID=47a422b1
ShowSelector=0
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "browser_bookmarks_tools.services.browser.gecko_paths.resolve_install_root",
        lambda browser_id: root if browser_id == "firefox" else None,
    )

    resolved = resolve_profile_directory("firefox", None)
    assert resolved == real_dir
    assert resolve_places_db_path("firefox", None) == real_dir / "places.sqlite"


def test_resolve_profile_directory_falls_back_to_legacy_flag_without_install_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    root = tmp_path / "Mozilla" / "Firefox"
    profile_dir = root / "xyz.default"
    profile_dir.mkdir(parents=True)
    (profile_dir / "places.sqlite").write_bytes(b"sqlite")

    profiles_ini = root / "profiles.ini"
    profiles_ini.write_text(
        """
[Profile0]
Name=default
IsRelative=1
Path=xyz.default
Default=1
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "browser_bookmarks_tools.services.browser.gecko_paths.resolve_install_root",
        lambda browser_id: root if browser_id == "firefox" else None,
    )

    assert resolve_profile_directory("firefox", None) == profile_dir

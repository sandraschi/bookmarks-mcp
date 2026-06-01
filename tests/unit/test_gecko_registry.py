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

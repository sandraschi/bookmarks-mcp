from pathlib import Path

import pytest

from browser_bookmarks_tools.services.browser.gecko_status import GeckoStatusChecker


@pytest.fixture
def firefox_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "Mozilla" / "Firefox"
    monkeypatch.setattr(
        "browser_bookmarks_tools.services.browser.gecko_paths.resolve_install_root",
        lambda browser_id: root if browser_id == "firefox" else None,
    )
    return root


def _write_profiles_ini(root: Path, body: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "profiles.ini").write_text(body.strip(), encoding="utf-8")


def test_empty_stale_profile_lists_the_one_with_real_data(firefox_root: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(GeckoStatusChecker, "is_browser_running", lambda _browser_id: {"is_running": False})

    stale = firefox_root / "Profiles" / "empty.default"
    stale.mkdir(parents=True)

    real = firefox_root / "Profiles" / "real.default-release"
    real.mkdir(parents=True)
    (real / "places.sqlite").write_bytes(b"sqlite")

    _write_profiles_ini(
        firefox_root,
        """
[Profile1]
Name=empty
IsRelative=1
Path=Profiles/empty.default

[Profile0]
Name=real
IsRelative=1
Path=Profiles/real.default-release
""",
    )

    result = GeckoStatusChecker.check_database_access_safe("firefox", profile_path=stale)
    assert result["safe"] is False
    assert result["reason"] == "database_not_found"
    assert "real" in result["message"]
    assert "pass profile_name explicitly" in result["message"]
    assert result["details"]["profiles_with_data"] == ["real"]


def test_genuinely_no_profiles_have_data_says_so_plainly(firefox_root: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(GeckoStatusChecker, "is_browser_running", lambda _browser_id: {"is_running": False})

    fresh = firefox_root / "Profiles" / "fresh.default-release"
    fresh.mkdir(parents=True)

    _write_profiles_ini(
        firefox_root,
        """
[Profile0]
Name=fresh
IsRelative=1
Path=Profiles/fresh.default-release
Default=1
""",
    )

    result = GeckoStatusChecker.check_database_access_safe("firefox", profile_path=fresh)
    assert result["safe"] is False
    assert "if you just installed it" in result["message"]
    assert result["details"]["profiles_with_data"] == []

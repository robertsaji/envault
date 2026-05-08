"""Unit tests for envault.profile."""
from __future__ import annotations

import pytest

from envault.profile import (
    ProfileError,
    apply_profile,
    delete_profile,
    get_profile,
    list_profiles,
    set_profile,
)


@pytest.fixture()
def cfg_file(tmp_path):
    path = tmp_path / "envault.toml"
    # Write a minimal valid config so load_config is happy
    path.write_text('[envault]\nenv_file = ".env"\nencrypted_file = ".env.gpg"\n')
    return path


class TestListProfiles:
    def test_empty_when_none_defined(self, cfg_file):
        assert list_profiles(cfg_file) == []

    def test_returns_sorted_names(self, cfg_file):
        set_profile(cfg_file, "staging", {})
        set_profile(cfg_file, "dev", {})
        assert list_profiles(cfg_file) == ["dev", "staging"]


class TestSetProfile:
    def test_creates_profile(self, cfg_file):
        set_profile(cfg_file, "prod", {"ENV": "production"})
        assert "prod" in list_profiles(cfg_file)

    def test_replaces_existing_profile(self, cfg_file):
        set_profile(cfg_file, "dev", {"DEBUG": "true"})
        set_profile(cfg_file, "dev", {"DEBUG": "false"})
        assert get_profile(cfg_file, "dev") == {"DEBUG": "false"}

    def test_raises_on_invalid_name(self, cfg_file):
        with pytest.raises(ProfileError, match="invalid"):
            set_profile(cfg_file, "bad-name!", {})

    def test_raises_on_empty_name(self, cfg_file):
        with pytest.raises(ProfileError):
            set_profile(cfg_file, "", {})


class TestGetProfile:
    def test_returns_overrides(self, cfg_file):
        set_profile(cfg_file, "qa", {"HOST": "qa.example.com"})
        assert get_profile(cfg_file, "qa") == {"HOST": "qa.example.com"}

    def test_raises_when_missing(self, cfg_file):
        with pytest.raises(ProfileError, match="not found"):
            get_profile(cfg_file, "ghost")


class TestDeleteProfile:
    def test_removes_profile(self, cfg_file):
        set_profile(cfg_file, "temp", {})
        delete_profile(cfg_file, "temp")
        assert "temp" not in list_profiles(cfg_file)

    def test_raises_when_missing(self, cfg_file):
        with pytest.raises(ProfileError, match="not found"):
            delete_profile(cfg_file, "nonexistent")


class TestApplyProfile:
    def test_merges_overrides(self):
        base = {"KEY": "base", "OTHER": "keep"}
        result = apply_profile(base, {"KEY": "overridden"})
        assert result == {"KEY": "overridden", "OTHER": "keep"}

    def test_does_not_mutate_base(self):
        base = {"KEY": "original"}
        apply_profile(base, {"KEY": "new"})
        assert base["KEY"] == "original"

    def test_adds_new_keys(self):
        result = apply_profile({}, {"NEW": "val"})
        assert result["NEW"] == "val"

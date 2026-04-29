"""Tests for envault.config module."""

import os
import pytest
import tomllib

from envault.config import (
    load_config,
    save_config,
    init_config,
    get_recipients,
    ConfigError,
)


class TestLoadConfig:
    def test_raises_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ConfigError, match="not found"):
            load_config(".envault.toml")

    def test_loads_valid_toml(self, tmp_path):
        cfg_file = tmp_path / ".envault.toml"
        cfg_file.write_bytes(b'[envault]\nenv_file = ".env"\n')
        config = load_config(str(cfg_file))
        assert config["envault"]["env_file"] == ".env"

    def test_raises_on_invalid_toml(self, tmp_path):
        cfg_file = tmp_path / ".envault.toml"
        cfg_file.write_text("[[invalid toml")
        with pytest.raises(ConfigError, match="Invalid TOML"):
            load_config(str(cfg_file))


class TestSaveConfig:
    def test_roundtrip(self, tmp_path):
        cfg_file = tmp_path / ".envault.toml"
        config = init_config(".env", ["alice@example.com"])
        save_config(config, str(cfg_file))
        with open(cfg_file, "rb") as f:
            loaded = tomllib.load(f)
        assert loaded["recipients"] == ["alice@example.com"]
        assert loaded["envault"]["env_file"] == ".env"


class TestInitConfig:
    def test_defaults(self):
        config = init_config()
        assert config["envault"]["env_file"] == ".env"
        assert config["envault"]["encrypted_file"] == ".env.gpg"
        assert config["recipients"] == []

    def test_custom_values(self):
        config = init_config(".env.production", ["bob@example.com"])
        assert config["envault"]["env_file"] == ".env.production"
        assert "bob@example.com" in config["recipients"]


class TestGetRecipients:
    def test_returns_recipients(self):
        config = {"recipients": ["alice@example.com", "bob@example.com"]}
        assert get_recipients(config) == ["alice@example.com", "bob@example.com"]

    def test_raises_when_empty(self):
        with pytest.raises(ConfigError, match="No recipients"):
            get_recipients({"recipients": []})

    def test_raises_when_missing(self):
        with pytest.raises(ConfigError, match="No recipients"):
            get_recipients({})

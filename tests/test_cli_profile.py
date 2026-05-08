"""Unit tests for envault.cli_profile."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from envault.cli_profile import cmd_profile_delete, cmd_profile_list, cmd_profile_set, cmd_profile_show
from envault.profile import set_profile


@pytest.fixture()
def cfg_file(tmp_path):
    path = tmp_path / "envault.toml"
    path.write_text('[envault]\nenv_file = ".env"\nencrypted_file = ".env.gpg"\n')
    return path


def _ns(cfg_file, **kwargs):
    return Namespace(config=str(cfg_file), **kwargs)


class TestCmdProfileList:
    def test_prints_no_profiles(self, cfg_file, capsys):
        cmd_profile_list(_ns(cfg_file))
        assert "No profiles" in capsys.readouterr().out

    def test_prints_profile_names(self, cfg_file, capsys):
        set_profile(cfg_file, "dev", {})
        set_profile(cfg_file, "prod", {})
        cmd_profile_list(_ns(cfg_file))
        out = capsys.readouterr().out
        assert "dev" in out
        assert "prod" in out


class TestCmdProfileSet:
    def test_saves_profile(self, cfg_file, capsys):
        cmd_profile_set(_ns(cfg_file, name="staging", overrides='{"ENV": "staging"}'))
        out = capsys.readouterr().out
        assert "saved" in out

    def test_exits_on_invalid_json(self, cfg_file):
        with pytest.raises(SystemExit):
            cmd_profile_set(_ns(cfg_file, name="x", overrides="not-json"))

    def test_exits_on_non_object_json(self, cfg_file):
        with pytest.raises(SystemExit):
            cmd_profile_set(_ns(cfg_file, name="x", overrides='["a"]'))

    def test_exits_on_invalid_profile_name(self, cfg_file):
        with pytest.raises(SystemExit):
            cmd_profile_set(_ns(cfg_file, name="bad name!", overrides="{}"))


class TestCmdProfileShow:
    def test_prints_json(self, cfg_file, capsys):
        set_profile(cfg_file, "dev", {"DEBUG": "true"})
        cmd_profile_show(_ns(cfg_file, name="dev"))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data == {"DEBUG": "true"}

    def test_exits_when_missing(self, cfg_file):
        with pytest.raises(SystemExit):
            cmd_profile_show(_ns(cfg_file, name="ghost"))


class TestCmdProfileDelete:
    def test_deletes_profile(self, cfg_file, capsys):
        set_profile(cfg_file, "tmp", {})
        cmd_profile_delete(_ns(cfg_file, name="tmp"))
        assert "deleted" in capsys.readouterr().out

    def test_exits_when_missing(self, cfg_file):
        with pytest.raises(SystemExit):
            cmd_profile_delete(_ns(cfg_file, name="ghost"))

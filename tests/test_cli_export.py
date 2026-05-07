"""Unit tests for envault.cli_export."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_export import cmd_export
from envault.export import ExportError


def _ns(**kwargs) -> Namespace:
    defaults = {"file": ".env", "format": "shell", "output": "", "no_export": False}
    defaults.update(kwargs)
    return Namespace(**defaults)


class TestCmdExport:
    def test_prints_to_stdout(self, tmp_path: Path, capsys) -> None:
        env = tmp_path / ".env"
        env.write_text("FOO=bar\n", encoding="utf-8")
        cmd_export(_ns(file=str(env)))
        out = capsys.readouterr().out
        assert "FOO=" in out

    def test_writes_to_output_file(self, tmp_path: Path, capsys) -> None:
        env = tmp_path / ".env"
        env.write_text("BAR=baz\n", encoding="utf-8")
        out_file = tmp_path / "out.sh"
        cmd_export(_ns(file=str(env), output=str(out_file)))
        assert out_file.exists()
        assert "BAR=" in out_file.read_text()

    def test_json_format(self, tmp_path: Path, capsys) -> None:
        env = tmp_path / ".env"
        env.write_text("KEY=value\n", encoding="utf-8")
        cmd_export(_ns(file=str(env), format="json"))
        data = json.loads(capsys.readouterr().out)
        assert data["KEY"] == "value"

    def test_exits_on_export_error(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc_info:
            cmd_export(_ns(file=str(tmp_path / "missing.env")))
        assert exc_info.value.code == 1

    def test_prints_error_message_on_failure(self, tmp_path: Path, capsys) -> None:
        with pytest.raises(SystemExit):
            cmd_export(_ns(file=str(tmp_path / "missing.env")))
        err = capsys.readouterr().err
        assert "export error" in err

    def test_no_export_flag(self, tmp_path: Path, capsys) -> None:
        env = tmp_path / ".env"
        env.write_text("X=1\n", encoding="utf-8")
        cmd_export(_ns(file=str(env), no_export=True))
        out = capsys.readouterr().out
        assert not any(line.startswith("export ") for line in out.splitlines())

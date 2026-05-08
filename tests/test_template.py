"""Tests for envault.template."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.template import TemplateError, render_template, _parse_env


# ---------------------------------------------------------------------------
# _parse_env helpers
# ---------------------------------------------------------------------------

class TestParseEnv:
    def test_simple_pairs(self):
        assert _parse_env("FOO=bar\nBAZ=qux") == {"FOO": "bar", "BAZ": "qux"}

    def test_ignores_comments(self):
        result = _parse_env("# comment\nKEY=val")
        assert "KEY" in result and len(result) == 1

    def test_ignores_blank_lines(self):
        assert _parse_env("\n\nA=1\n\n") == {"A": "1"}

    def test_strips_double_quotes(self):
        assert _parse_env('SECRET="hello world"') == {"SECRET": "hello world"}

    def test_strips_single_quotes(self):
        assert _parse_env("TOKEN='abc'") == {"TOKEN": "abc"}


# ---------------------------------------------------------------------------
# render_template
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("HOST=localhost\nPORT=5432\nPASS=s3cr3t\n")
    return p


class TestRenderTemplate:
    def test_raises_when_template_missing(self, tmp_path, env_file):
        with pytest.raises(TemplateError, match="Template file not found"):
            render_template(tmp_path / "missing.tmpl", env_file)

    def test_raises_when_env_missing(self, tmp_path):
        tmpl = tmp_path / "t.tmpl"
        tmpl.write_text("${HOST}")
        with pytest.raises(TemplateError, match="Env file not found"):
            render_template(tmpl, tmp_path / "nonexistent.env")

    def test_substitutes_brace_syntax(self, tmp_path, env_file):
        tmpl = tmp_path / "t.tmpl"
        tmpl.write_text("db://${HOST}:${PORT}")
        result = render_template(tmpl, env_file)
        assert result == "db://localhost:5432"

    def test_substitutes_dollar_syntax(self, tmp_path, env_file):
        tmpl = tmp_path / "t.tmpl"
        tmpl.write_text("host=$HOST port=$PORT")
        result = render_template(tmpl, env_file)
        assert result == "host=localhost port=5432"

    def test_strict_raises_on_missing_var(self, tmp_path, env_file):
        tmpl = tmp_path / "t.tmpl"
        tmpl.write_text("${UNDEFINED_VAR}")
        with pytest.raises(TemplateError, match="UNDEFINED_VAR"):
            render_template(tmpl, env_file, strict=True)

    def test_non_strict_leaves_unresolved(self, tmp_path, env_file):
        tmpl = tmp_path / "t.tmpl"
        tmpl.write_text("${UNDEFINED_VAR}")
        result = render_template(tmpl, env_file, strict=False)
        assert result == "${UNDEFINED_VAR}"

    def test_writes_output_file(self, tmp_path, env_file):
        tmpl = tmp_path / "t.tmpl"
        tmpl.write_text("${HOST}")
        out = tmp_path / "sub" / "rendered.txt"
        render_template(tmpl, env_file, out)
        assert out.exists()
        assert out.read_text() == "localhost"

    def test_returns_rendered_text(self, tmp_path, env_file):
        tmpl = tmp_path / "t.tmpl"
        tmpl.write_text("pass=${PASS}")
        result = render_template(tmpl, env_file)
        assert result == "pass=s3cr3t"

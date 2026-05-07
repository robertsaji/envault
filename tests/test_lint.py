"""Tests for envault.lint and envault.cli_lint."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

import pytest

from envault.lint import (
    LintError,
    LintResult,
    format_results,
    lint_file,
)
from envault.cli_lint import cmd_lint


def _ns(**kwargs):
    defaults = {'files': [], 'summary': False}
    defaults.update(kwargs)
    return Namespace(**defaults)


# ---------------------------------------------------------------------------
# lint_file
# ---------------------------------------------------------------------------

class TestLintFile:
    def test_raises_when_file_missing(self, tmp_path):
        with pytest.raises(LintError, match='File not found'):
            lint_file(tmp_path / 'nonexistent.env')

    def test_clean_file_has_no_issues(self, tmp_path):
        env = tmp_path / '.env'
        env.write_text('API_KEY=abc123\nDEBUG=true\n')
        result = lint_file(env)
        assert result.ok
        assert result.issues == []

    def test_detects_trailing_whitespace(self, tmp_path):
        env = tmp_path / '.env'
        env.write_text('API_KEY=abc  \n')
        result = lint_file(env)
        codes = [i.code for i in result.issues]
        assert 'W001' in codes

    def test_detects_invalid_pair(self, tmp_path):
        env = tmp_path / '.env'
        env.write_text('NOTAPAIR\n')
        result = lint_file(env)
        codes = [i.code for i in result.issues]
        assert 'E001' in codes

    def test_detects_lowercase_key(self, tmp_path):
        env = tmp_path / '.env'
        env.write_text('my_key=value\n')
        result = lint_file(env)
        codes = [i.code for i in result.issues]
        assert 'W002' in codes

    def test_detects_unmatched_double_quote(self, tmp_path):
        env = tmp_path / '.env'
        env.write_text('KEY="unclosed\n')
        result = lint_file(env)
        codes = [i.code for i in result.issues]
        assert 'E002' in codes

    def test_ignores_comments_and_blank_lines(self, tmp_path):
        env = tmp_path / '.env'
        env.write_text('# comment\n\nKEY=val\n')
        result = lint_file(env)
        assert result.ok

    def test_line_number_is_correct(self, tmp_path):
        env = tmp_path / '.env'
        env.write_text('GOOD=ok\nBAD LINE\n')
        result = lint_file(env)
        assert result.issues[0].line_number == 2


# ---------------------------------------------------------------------------
# format_results
# ---------------------------------------------------------------------------

def test_format_results_ok(tmp_path):
    result = LintResult(path=tmp_path / '.env')
    assert 'no issues' in format_results(result)


def test_format_results_with_issues(tmp_path):
    from envault.lint import LintIssue
    result = LintResult(
        path=tmp_path / '.env',
        issues=[LintIssue(3, 'W001', 'Trailing whitespace')],
    )
    output = format_results(result)
    assert 'W001' in output
    assert 'line 3' in output


# ---------------------------------------------------------------------------
# cmd_lint
# ---------------------------------------------------------------------------

class TestCmdLint:
    def test_exits_zero_on_clean_file(self, tmp_path, capsys):
        env = tmp_path / '.env'
        env.write_text('KEY=value\n')
        with pytest.raises(SystemExit) as exc:
            cmd_lint(_ns(files=[str(env)]))
        assert exc.value.code == 0

    def test_exits_one_on_issues(self, tmp_path):
        env = tmp_path / '.env'
        env.write_text('bad line\n')
        with pytest.raises(SystemExit) as exc:
            cmd_lint(_ns(files=[str(env)]))
        assert exc.value.code == 1

    def test_exits_on_missing_file(self, tmp_path):
        with pytest.raises(SystemExit) as exc:
            cmd_lint(_ns(files=[str(tmp_path / 'missing.env')]))
        assert exc.value.code == 1

    def test_summary_flag_prints_extra_line(self, tmp_path, capsys):
        env = tmp_path / '.env'
        env.write_text('bad\n')
        with pytest.raises(SystemExit):
            cmd_lint(_ns(files=[str(env)], summary=True))
        captured = capsys.readouterr()
        assert 'issue(s)' in captured.err

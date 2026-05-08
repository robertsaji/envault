"""Tests for envault.redact."""

from __future__ import annotations

import pytest

from envault.redact import (
    RedactResult,
    _is_sensitive,
    _mask_value,
    redact_dict,
    redact_env_text,
)

# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key",
    ["PASSWORD", "db_password", "API_KEY", "auth_token", "SECRET", "private_key"],
)
def test_sensitive_keys_detected(key: str) -> None:
    assert _is_sensitive(key) is True


@pytest.mark.parametrize("key", ["HOST", "PORT", "APP_NAME", "LOG_LEVEL"])
def test_non_sensitive_keys_pass(key: str) -> None:
    assert _is_sensitive(key) is False


# ---------------------------------------------------------------------------
# _mask_value
# ---------------------------------------------------------------------------


def test_mask_returns_placeholder() -> None:
    assert _mask_value("supersecret") == "********"


def test_mask_empty_value_unchanged() -> None:
    assert _mask_value("") == ""


def test_mask_with_reveal_chars() -> None:
    result = _mask_value("supersecret", reveal_chars=3)
    assert result.endswith("ret")
    assert result.startswith("***")


def test_mask_reveal_exceeds_length_fully_masked() -> None:
    assert _mask_value("hi", reveal_chars=10) == "********"


# ---------------------------------------------------------------------------
# redact_env_text
# ---------------------------------------------------------------------------

SAMPLE_ENV = """\
# database config
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=s3cr3t!
API_KEY=abc123xyz
APP_NAME=myapp
"""


def test_redacts_sensitive_values() -> None:
    result = redact_env_text(SAMPLE_ENV)
    assert "s3cr3t!" not in result.text
    assert "abc123xyz" not in result.text


def test_preserves_non_sensitive_values() -> None:
    result = redact_env_text(SAMPLE_ENV)
    assert "localhost" in result.text
    assert "5432" in result.text
    assert "myapp" in result.text


def test_redacted_count_is_correct() -> None:
    result = redact_env_text(SAMPLE_ENV)
    assert result.redacted_count == 2


def test_original_count_is_correct() -> None:
    result = redact_env_text(SAMPLE_ENV)
    assert result.original_count == 5


def test_comments_and_blanks_preserved() -> None:
    result = redact_env_text(SAMPLE_ENV)
    assert "# database config" in result.text


def test_extra_keys_are_redacted() -> None:
    env = "CUSTOM_FIELD=topsecret\nHOST=example.com\n"
    result = redact_env_text(env, extra_keys=["CUSTOM_FIELD"])
    assert "topsecret" not in result.text
    assert "example.com" in result.text


def test_reveal_chars_partial_exposure() -> None:
    env = "DB_PASSWORD=abcdefgh\n"
    result = redact_env_text(env, reveal_chars=3)
    assert result.text.endswith("fgh")


# ---------------------------------------------------------------------------
# redact_dict
# ---------------------------------------------------------------------------


def test_redact_dict_masks_sensitive() -> None:
    data = {"API_KEY": "secret", "HOST": "localhost"}
    out = redact_dict(data)
    assert out["API_KEY"] == "********"
    assert out["HOST"] == "localhost"


def test_redact_dict_does_not_mutate_original() -> None:
    data = {"PASSWORD": "hunter2"}
    redact_dict(data)
    assert data["PASSWORD"] == "hunter2"


def test_redact_dict_extra_keys() -> None:
    data = {"MY_FIELD": "sensitive", "OTHER": "fine"}
    out = redact_dict(data, extra_keys=["MY_FIELD"])
    assert out["MY_FIELD"] == "********"
    assert out["OTHER"] == "fine"

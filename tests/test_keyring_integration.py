"""Integration tests: keyring file persists across add/remove cycles."""

from pathlib import Path

import pytest

from envault.keyring import (
    KEYRING_FILE,
    KeyringError,
    add_key,
    load_keyring,
    remove_key,
    save_keyring,
)

FP_A = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
FP_B = "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
FP_C = "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"


def test_full_lifecycle(tmp_path: Path) -> None:
    """Add three keys, remove one, verify state."""
    add_key(FP_A, tmp_path)
    add_key(FP_B, tmp_path)
    add_key(FP_C, tmp_path)

    keys = load_keyring(tmp_path)
    assert len(keys) == 3

    remove_key(FP_B, tmp_path)
    keys = load_keyring(tmp_path)
    assert len(keys) == 2
    assert FP_B.upper() not in [k.upper() for k in keys]


def test_keyring_file_is_human_readable(tmp_path: Path) -> None:
    save_keyring([FP_A, FP_B], tmp_path)
    raw = (tmp_path / KEYRING_FILE).read_text()
    assert raw.startswith("#")
    assert FP_A in raw
    assert FP_B in raw


def test_duplicate_rejected_after_reload(tmp_path: Path) -> None:
    add_key(FP_A, tmp_path)
    with pytest.raises(KeyringError, match="already trusted"):
        add_key(FP_A.lower(), tmp_path)  # case-insensitive duplicate


def test_remove_then_re_add(tmp_path: Path) -> None:
    add_key(FP_A, tmp_path)
    remove_key(FP_A, tmp_path)
    keys = add_key(FP_A, tmp_path)  # should not raise
    assert FP_A.upper() in [k.upper() for k in keys]

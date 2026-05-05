"""Tests for envault.keyring."""

import pytest
from pathlib import Path

from envault.keyring import (
    KeyringError,
    add_key,
    load_keyring,
    remove_key,
    save_keyring,
    KEYRING_FILE,
)

FP1 = "AABBCCDD11223344AABBCCDD11223344AABBCCDD"
FP2 = "1122334455667788112233445566778811223344"


class TestLoadKeyring:
    def test_returns_empty_when_file_absent(self, tmp_path):
        assert load_keyring(tmp_path) == []

    def test_loads_fingerprints(self, tmp_path):
        (tmp_path / KEYRING_FILE).write_text(f"# comment\n{FP1}\n{FP2}\n")
        assert load_keyring(tmp_path) == [FP1, FP2]

    def test_ignores_blank_lines(self, tmp_path):
        (tmp_path / KEYRING_FILE).write_text(f"\n{FP1}\n\n")
        assert load_keyring(tmp_path) == [FP1]


class TestSaveKeyring:
    def test_writes_file(self, tmp_path):
        path = save_keyring([FP1], tmp_path)
        assert path.exists()
        assert FP1 in path.read_text()

    def test_raises_on_invalid_fingerprint(self, tmp_path):
        with pytest.raises(KeyringError, match="Invalid fingerprint"):
            save_keyring(["not-a-fingerprint"], tmp_path)

    def test_roundtrip(self, tmp_path):
        save_keyring([FP1, FP2], tmp_path)
        assert load_keyring(tmp_path) == [FP1.upper(), FP2.upper()]


class TestAddKey:
    def test_adds_new_key(self, tmp_path):
        keys = add_key(FP1, tmp_path)
        assert FP1.upper() in keys

    def test_raises_on_duplicate(self, tmp_path):
        add_key(FP1, tmp_path)
        with pytest.raises(KeyringError, match="already trusted"):
            add_key(FP1, tmp_path)

    def test_raises_on_invalid(self, tmp_path):
        with pytest.raises(KeyringError, match="Invalid fingerprint"):
            add_key("bad", tmp_path)


class TestRemoveKey:
    def test_removes_existing_key(self, tmp_path):
        add_key(FP1, tmp_path)
        add_key(FP2, tmp_path)
        keys = remove_key(FP1, tmp_path)
        assert FP1.upper() not in [k.upper() for k in keys]

    def test_raises_when_not_found(self, tmp_path):
        with pytest.raises(KeyringError, match="not found"):
            remove_key(FP1, tmp_path)

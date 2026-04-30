"""Tests for envault.sync."""

import pytest
from pathlib import Path

from envault.sync import SyncError, push, pull, remote_exists


# ---------------------------------------------------------------------------
# push
# ---------------------------------------------------------------------------

class TestPush:
    def test_raises_when_source_missing(self, tmp_path):
        with pytest.raises(SyncError, match="not found"):
            push(tmp_path / "missing.gpg", str(tmp_path / "remote"))

    def test_copies_file_to_remote(self, tmp_path):
        src = tmp_path / "local" / ".env.gpg"
        src.parent.mkdir()
        src.write_bytes(b"encrypted")
        remote = tmp_path / "remote"

        dest = push(src, str(remote))

        assert dest == remote / ".env.gpg"
        assert dest.read_bytes() == b"encrypted"

    def test_creates_remote_dir_if_absent(self, tmp_path):
        src = tmp_path / ".env.gpg"
        src.write_bytes(b"data")
        remote = tmp_path / "a" / "b" / "c"

        push(src, str(remote))

        assert (remote / ".env.gpg").exists()

    def test_returns_destination_path(self, tmp_path):
        src = tmp_path / "file.gpg"
        src.write_bytes(b"x")
        dest = push(src, str(tmp_path / "remote"))
        assert isinstance(dest, Path)


# ---------------------------------------------------------------------------
# pull
# ---------------------------------------------------------------------------

class TestPull:
    def test_raises_when_remote_file_missing(self, tmp_path):
        with pytest.raises(SyncError, match="not found"):
            pull(str(tmp_path / "remote"), "missing.gpg", tmp_path / "local")

    def test_copies_file_to_local(self, tmp_path):
        remote = tmp_path / "remote"
        remote.mkdir()
        (remote / ".env.gpg").write_bytes(b"secret")
        local = tmp_path / "local"

        dest = pull(str(remote), ".env.gpg", local)

        assert dest == local / ".env.gpg"
        assert dest.read_bytes() == b"secret"

    def test_creates_local_dir_if_absent(self, tmp_path):
        remote = tmp_path / "remote"
        remote.mkdir()
        (remote / "f.gpg").write_bytes(b"y")
        local = tmp_path / "a" / "b"

        pull(str(remote), "f.gpg", local)

        assert (local / "f.gpg").exists()


# ---------------------------------------------------------------------------
# remote_exists
# ---------------------------------------------------------------------------

def test_remote_exists_true(tmp_path):
    (tmp_path / "env.gpg").write_bytes(b"")
    assert remote_exists(str(tmp_path), "env.gpg") is True


def test_remote_exists_false(tmp_path):
    assert remote_exists(str(tmp_path), "env.gpg") is False

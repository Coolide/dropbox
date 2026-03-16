from pathlib import Path

import pytest

from src.server.storage import PathTraversalError, Storage


@pytest.fixture
def store(tmp_path: Path) -> Storage:
    return Storage(root=tmp_path)


def test_write_and_read(store: Storage, tmp_path: Path):
    store.write("subdir/hello.txt", b"Hello world")
    assert (tmp_path / "subdir" / "hello.txt").read_bytes() == b"Hello world"


def test_write_creates_parent_dirs(store: Storage, tmp_path: Path):
    store.write("a/b/c/deep.txt", b"test")
    assert (tmp_path / "a" / "b" / "c" / "deep.txt").exists()


def test_delete(store: Storage, tmp_path: Path):
    store.write("to_delete.txt", b"test")
    store.delete("to_delete.txt")
    assert not (tmp_path / "to_delete.txt").exists()


def test_delete_nonexistent_is_ok(store: Storage):
    store.delete("ghost.txt")


def test_read_bytes(store: Storage):
    store.write("read_me.txt", b"contents")
    assert store.read("read_me.txt") == b"contents"


def test_path_traversal_blocked(store: Storage):
    with pytest.raises(PathTraversalError):
        store.write("../../etc/passwd", b"evil")


def test_path_traversal_blocked_on_delete(store: Storage):
    with pytest.raises(PathTraversalError):
        store.delete("../outside.txt")

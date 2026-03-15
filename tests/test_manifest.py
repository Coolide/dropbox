import pytest
from pathlib import Path
from src.client.manifest import Manifest, compute_sha256


def test_compute_sha256(tmp_path: Path):
    f = tmp_path / "test.txt"
    f.write_bytes(b"hello")
    digest = compute_sha256(f)
    assert digest == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824" # hash of 'hello'

def test_empty_manifest(tmp_path: Path):
    m = Manifest(tmp_path / "manifest.json")
    assert m.get("anything") is None

def test_add_and_get(tmp_path: Path):
    m = Manifest(tmp_path / "manifest.json")
    m.set("notes/todo.txt", sha256="abc", mtime=1.0)
    record = m.get("notes/todo.txt")
    assert record is not None
    assert record["sha256"] == "abc"
    assert record["mtime"] == 1.0

def test_persistence(tmp_path: Path):
    path = tmp_path / "manifest.json"
    m1 = Manifest(path)
    m1.set("a.txt", sha256="x", mtime=2.0)
    m1.save()

    m2 = Manifest(path)
    assert m2.get("a.txt")["sha256"] == "x"

def test_remove(tmp_path: Path):
    m = Manifest(tmp_path / "manifest.json")
    m.set("a.txt", sha256="y", mtime=3.0)
    m.remove("a.txt")
    assert m.get("a.txt") is None

def test_all_path(tmp_path: Path):
    m = Manifest(tmp_path / "manifest.json")
    m.set("a.txt", sha256="1", mtime=1.0)
    m.set("b.txt", sha256="2", mtime=2.0)
    assert set(m.all_paths()) == {"a.txt", "b.txt"}
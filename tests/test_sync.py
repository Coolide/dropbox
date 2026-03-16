from pathlib import Path

from src.client.manifest import Manifest, compute_sha256
from src.client.sync import compute_diff


def test_new_file_detected(tmp_path: Path):
    (tmp_path / "new.txt").write_bytes(b"data")
    manifest = Manifest(tmp_path / "manifest.json")
    diff = compute_diff(source_dir=tmp_path, manifest=manifest)
    assert "new.txt" in diff.to_upload


def test_changed_file_detected(tmp_path: Path):
    f = tmp_path / "changed.txt"
    f.write_bytes(b"version 2")
    manifest = Manifest(tmp_path / "manifest.json")
    manifest.set("changed.txt", sha256="old_hash", mtime=0.0)

    diff = compute_diff(source_dir=tmp_path, manifest=manifest)
    assert "changed.txt" in diff.to_upload


def test_unchanged_file_skipped(tmp_path: Path):
    f = tmp_path / "same.txt"
    f.write_bytes(b"stable")
    digest = compute_sha256(f)
    manifest = Manifest(tmp_path / "manifest.json")
    manifest.set("same.txt", sha256=digest, mtime=f.stat().st_mtime)

    diff = compute_diff(source_dir=tmp_path, manifest=manifest)
    assert "same.txt" not in diff.to_upload
    assert "same.txt" not in diff.to_delete


def test_deleted_file_detected(tmp_path: Path):
    manifest = Manifest(tmp_path / "manifest.json")
    manifest.set("deleted.txt", sha256="some_hash", mtime=0.0)

    diff = compute_diff(source_dir=tmp_path, manifest=manifest)
    assert "deleted.txt" in diff.to_delete

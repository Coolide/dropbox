import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock, call
from src.client.watcher import start_watcher


def test_new_file_triggers_upload(tmp_path: Path):
    mock_client = MagicMock()
    mock_manifest = MagicMock()
    mock_manifest.get.return_value = None

    stop = start_watcher(
        source_dir=tmp_path,
        client=mock_client,
        manifest=mock_manifest,
    )

    (tmp_path / "new_file.txt").write_bytes(b"hello")
    time.sleep(0.1)

    stop()

    mock_client.upload.assert_called_once_with("new_file.txt", b"hello")
    mock_manifest.set.assert_called_once()
    mock_manifest.save.assert_called_once()

def test_deleted_file_triggers_delete(tmp_path: Path):
    f = tmp_path / "existing.txt"
    f.write_bytes(b"data")

    mock_client = MagicMock()
    mock_manifest = MagicMock()
    mock_manifest.get.return_value = {"sha256": "x", "mtime": 0.0}

    stop = start_watcher(
        source_dir=tmp_path,
        client=mock_client,
        manifest=mock_manifest,
    )

    f.unlink()
    time.sleep(1.0)

    stop()
    mock_client.delete.assert_called_once_with("existing.txt")
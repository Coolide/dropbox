import hashlib
import json
from pathlib import Path
from typing import TypedDict


class FileRecord(TypedDict):
    sha256: str
    mtime: float


type ManifestData = dict[str, FileRecord]


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class Manifest:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._data: ManifestData = {}
        if self._path.exists():
            self._data = json.loads(self._path.read_text())

    def get(self, relative: str) -> FileRecord | None:
        return self._data.get(relative)

    def set(self, relative: str, *, sha256: str, mtime: float) -> None:
        self._data[relative] = {"sha256": sha256, "mtime": mtime}

    def remove(self, relative: str) -> None:
        self._data.pop(relative, None)

    def all_paths(self) -> list[str]:
        return list(self._data.keys())

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2))

from pathlib import Path


class PathTraversalError(ValueError):
    pass


class Storage:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def _safe_path(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve()
        if not str(candidate).startswith(str(self.root)):
            raise PathTraversalError(f"Path '{relative}' escapes root '{self.root}'")
        return candidate

    def write(self, relative: str, data: bytes) -> None:
        path = self._safe_path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def delete(self, relative: str) -> None:
        path = self._safe_path(relative)
        path.unlink(missing_ok=True)

    def read(self, relative: str) -> bytes:
        path = self._safe_path(relative)
        return path.read_bytes()

    def exists(self, relative: str) -> bool:
        return self._safe_path(relative).exists()

from dataclasses import dataclass, field
from pathlib import Path

from src.client.manifest import Manifest, compute_sha256

@dataclass
class DiffResult:
    to_upload: list[str] = field(default_factory=list)
    to_delete: list[str] = field(default_factory=list)

def compute_diff(source_dir: Path, manifest: Manifest) -> DiffResult:
    diff = DiffResult()
    disk_paths: set[str] = set()
    for file_path in source_dir.rglob("*"):
        if not file_path.is_file():
            continue

        relative = file_path.relative_to(source_dir).as_posix()
        disk_paths.add(relative)

        current_sha256 = compute_sha256(file_path)
        record = manifest.get(relative)

        if record is None or record["sha256"] != current_sha256:
            diff.to_upload.append(relative)
    
    for tracked_path in manifest.all_paths():
        if tracked_path not in disk_paths:
            diff.to_delete.append(tracked_path)

    return diff
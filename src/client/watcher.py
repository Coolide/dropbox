import threading
import time
from collections.abc import Callable
from pathlib import Path
from queue import Empty, Queue

from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from src.client.http import SyncClient
from src.client.manifest import Manifest, compute_sha256
from src.client.sync import should_ignore

DEBOUNCE = 0.5


class _Handler(FileSystemEventHandler):
    """Translates watchdog events into (relative_path, action) tuples on a queue."""

    def __init__(self, source_dir: Path, queue: Queue[tuple[str, str]]) -> None:
        self._source_dir = source_dir
        self._queue = queue

    def _to_relative(self, abs_path: str) -> str:
        return Path(abs_path).relative_to(self._source_dir).as_posix()

    def _enqueue(self, rel_path: str, action: str) -> None:
        if not should_ignore(rel_path):
            self._queue.put((rel_path, action))

    def on_created(self, event: FileSystemEvent) -> None:
        if isinstance(event, FileCreatedEvent):
            self._enqueue(self._to_relative(event.src_path), "upload")

    def on_modified(self, event: FileSystemEvent) -> None:
        if isinstance(event, FileModifiedEvent):
            self._enqueue(self._to_relative(event.src_path), "upload")

    def on_deleted(self, event: FileSystemEvent) -> None:
        if isinstance(event, FileDeletedEvent):
            self._enqueue(self._to_relative(event.src_path), "delete")

    def on_moved(self, event: FileSystemEvent) -> None:
        if isinstance(event, FileMovedEvent):
            # delete the old path, upload the new destination path
            self._enqueue(self._to_relative(event.src_path), "delete")
            self._enqueue(self._to_relative(event.dest_path), "upload")


def _processing_loop(
    source_dir: Path,
    queue: Queue[tuple[str, str]],
    client: SyncClient,
    manifest: Manifest,
    stop_event: threading.Event,
) -> None:
    while not stop_event.is_set():
        pending: dict[str, str] = {}

        try:
            path, action = queue.get(timeout=0.2)
            pending[path] = action
            deadline = time.monotonic() + DEBOUNCE
            while time.monotonic() < deadline:
                try:
                    path, action = queue.get_nowait()
                    pending[path] = action
                except Empty:
                    time.sleep(0.05)
        except Empty:
            continue

        for rel_path, action in pending.items():
            abs_path = source_dir / rel_path
            try:
                if action == "upload" and abs_path.is_file():
                    data = abs_path.read_bytes()
                    client.upload(rel_path, data)
                    manifest.set(
                        rel_path, sha256=compute_sha256(abs_path), mtime=abs_path.stat().st_mtime
                    )
                    print(f"[watcher] Uploaded: {rel_path}")  # TODO: use logging instead
                elif action == "delete":
                    client.delete(rel_path)
                    manifest.remove(rel_path)
                    print(f"[watcher] Deleted: {rel_path}")  # TODO: use logging instead
            except Exception as e:
                print(f"[watcher] Error syncing {rel_path}: {e}")  # TODO: use logging instead
        manifest.save()


def start_watcher(
    source_dir: Path,
    client: SyncClient,
    manifest: Manifest,
) -> Callable[[], None]:
    """Start the filesystem watcher and return a stop() function."""
    queue: Queue[tuple[str, str]] = Queue()
    stop_event = threading.Event()

    handler = _Handler(source_dir, queue)
    observer = Observer()
    observer.schedule(handler, str(source_dir), recursive=True)
    observer.start()
    processing_thread = threading.Thread(
        target=_processing_loop,
        args=(source_dir, queue, client, manifest, stop_event),
        daemon=True,  # ensure thread exits when main thread exits
    )

    processing_thread.start()

    def stop() -> None:
        stop_event.set()
        observer.stop()
        observer.join()
        processing_thread.join(timeout=2.0)

    return stop

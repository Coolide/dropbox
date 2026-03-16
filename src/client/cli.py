import argparse
import os
import signal
import sys
from pathlib import Path

from src.client.http import SyncClient
from src.client.manifest import Manifest, compute_sha256
from src.client.sync import compute_diff
from src.client.watcher import start_watcher


def _parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync a local source directory to a remote server! Your own Dropbox."
    )

    parser.add_argument("--source", required=True, help="Local directory to sync")

    parser.add_argument(
        "--server",
        default=os.environ.get("SYNC_SERVER", "https://localhost:8443"),
        help="Remote server URL",
    )

    parser.add_argument(
        "--secret",
        default=os.environ.get("SYNC_SECRET", "dev-secret-change-me"),
        help="Secret key for authentication, must match the server",
    )

    parser.add_argument(
        "--cert", default=os.environ.get("SYNC_CERT", None), help="Path to server's PEM cert"
    )

    parser.add_argument(
        "--manifest",
        default=str(Path.home() / ".sync-manifest.json"),
        help="Path to the local manifest file (default: ~/.sync_manifest.json)",
    )

    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Disable TLS verification entirely (not recommended)",
    )

    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    source_dir = Path(args.source).expanduser().resolve()

    if not source_dir.is_dir():
        print(f"[client] ERROR: source dir does not exist: {source_dir}")
        sys.exit(1)

    if args.no_verify:
        verify: bool | str = False
        print("[client] WARNING: TLS verification disabled")
    elif args.cert:
        verify = args.cert
    else:
        verify = True  # use system certificate authorities

    manifest = Manifest(args.manifest)

    with SyncClient(base_url=args.server, secret=args.secret, verify=verify) as client:
        print(f"[client] Scanning {source_dir} for offline changes...")
        diff = compute_diff(source_dir, manifest)

        if diff.to_upload or diff.to_delete:
            n_up, n_del = len(diff.to_upload), len(diff.to_delete)
            print(f"[client] Catch-up: {n_up} upload(s), {n_del} delete(s)")
        else:
            print("[client] Already up to date!")

        for relative_path in diff.to_upload:
            abs_path = source_dir / relative_path
            data = abs_path.read_bytes()
            print(f"[client] Uploading: {relative_path}")
            client.upload(relative_path, data)
            manifest.set(
                relative_path, sha256=compute_sha256(abs_path), mtime=abs_path.stat().st_mtime
            )

        for relative_path in diff.to_delete:
            print(f"[client] Deleting: {relative_path}")
            client.delete(relative_path)
            manifest.remove(relative_path)

        manifest.save()

        print(f"[client] Waiting for changes in {source_dir}. Press Ctrl+C to stop.")
        stop = start_watcher(source_dir=source_dir, client=client, manifest=manifest)

        try:
            signal.pause()
        except KeyboardInterrupt, AttributeError:
            try:
                while True:
                    import time  # TODO: move to top level

                    time.sleep(0.1)
            except KeyboardInterrupt:
                pass

        print("\n[client] Shutting down...")
        stop()

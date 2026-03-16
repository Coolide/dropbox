"""Integration tests:

These tests exercise the entire request pipeline together:
  HMACAuthMiddleware → Routes → Storage
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.server.app import create_app
from src.server.auth import sign_request
from src.server.config import Settings

SECRET = "integration-test-secret"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    """Full app with a temp storage dir and a known secret."""
    settings = Settings(
        dest_dir=str(tmp_path),
        sync_secret=SECRET,
        cert_dir=str(tmp_path / ".certs"),
    )
    return TestClient(create_app(settings), raise_server_exceptions=True)


# ── Health (no auth required) ─────────────────────────────────────────────────


def test_health_no_auth_required(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── HMAC auth enforcement ─────────────────────────────────────────────────────


def test_unsigned_request_rejected(client: TestClient):
    resp = client.put("/files/secret.txt", content=b"data")
    assert resp.status_code == 401


def test_wrong_secret_rejected(client: TestClient):
    body = b"data"
    headers = sign_request("PUT", "/files/x.txt", body, "WRONG_SECRET")
    resp = client.put("/files/x.txt", content=body, headers=headers)
    assert resp.status_code == 401


# ── PUT ───────────────────────────────────────────────────────────────────────


def test_put_creates_file(client: TestClient, tmp_path: Path):
    body = b"hello from integration test"
    headers = sign_request("PUT", "/files/greet.txt", body, SECRET)
    resp = client.put("/files/greet.txt", content=body, headers=headers)
    assert resp.status_code == 200
    assert (tmp_path / "greet.txt").read_bytes() == body


def test_put_nested_path(client: TestClient, tmp_path: Path):
    body = b"nested"
    headers = sign_request("PUT", "/files/a/b/c.txt", body, SECRET)
    resp = client.put("/files/a/b/c.txt", content=body, headers=headers)
    assert resp.status_code == 200
    assert (tmp_path / "a" / "b" / "c.txt").exists()


# ── GET ───────────────────────────────────────────────────────────────────────


def test_get_downloads_file(client: TestClient, tmp_path: Path):
    (tmp_path / "serve.txt").write_bytes(b"serve me")
    headers = sign_request("GET", "/files/serve.txt", b"", SECRET)
    resp = client.get("/files/serve.txt", headers=headers)
    assert resp.status_code == 200
    assert resp.content == b"serve me"


def test_get_missing_file_returns_404(client: TestClient):
    headers = sign_request("GET", "/files/missing.txt", b"", SECRET)
    resp = client.get("/files/missing.txt", headers=headers)
    assert resp.status_code == 404


# ── DELETE ────────────────────────────────────────────────────────────────────


def test_delete_removes_file(client: TestClient, tmp_path: Path):
    (tmp_path / "bye.txt").write_bytes(b"goodbye")
    headers = sign_request("DELETE", "/files/bye.txt", b"", SECRET)
    resp = client.delete("/files/bye.txt", headers=headers)
    assert resp.status_code == 200
    assert not (tmp_path / "bye.txt").exists()


def test_delete_missing_file_returns_404(client: TestClient):
    headers = sign_request("DELETE", "/files/nobody.txt", b"", SECRET)
    resp = client.delete("/files/nobody.txt", headers=headers)
    assert resp.status_code == 404


# ── Round-trip ────────────────────────────────────────────────────────────────


def test_upload_then_download_roundtrip(client: TestClient):
    """Upload binary data then download it — bytes must be identical."""
    content = b"\x00\x01\x02\x03" * 1024  # 4 KB of binary data
    put_headers = sign_request("PUT", "/files/binary.bin", content, SECRET)
    client.put("/files/binary.bin", content=content, headers=put_headers)
    get_headers = sign_request("GET", "/files/binary.bin", b"", SECRET)
    resp = client.get("/files/binary.bin", headers=get_headers)
    assert resp.content == content

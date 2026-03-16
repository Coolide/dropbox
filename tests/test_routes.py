from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.server.routes import make_router
from src.server.storage import Storage

SECRET = "test-route-secret"


def make_app(tmp_path: Path):
    store = Storage(tmp_path)
    app = FastAPI()
    app.include_router(make_router(store))

    client = TestClient(app, raise_server_exceptions=True)
    return client, store


@pytest.fixture
def setup(tmp_path: Path):
    return make_app(tmp_path)


def test_put_creates_file(setup):
    client, store = setup
    response = client.put("/files/notes/hello.txt", content=b"hello")
    assert response.status_code == 200
    assert store.read("notes/hello.txt") == b"hello"


def test_put_overwrites_files(setup):
    client, store = setup
    client.put("/files/a.txt", content=b"v1")
    client.put("/files/a.txt", content=b"v2")
    assert store.read("a.txt") == b"v2"


def test_delete_remove_files(setup):
    client, store = setup
    store.write("to_delete.txt", b"bye")
    response = client.delete("/files/to_delete.txt")
    assert response.status_code == 200
    assert not store.exists("to_delete.txt")


def test_delete_nonexistent_returns_404(setup):
    client, _ = setup
    response = client.delete("/files/ghost.txt")
    assert response.status_code == 404


def test_get_downloads_files(setup):
    client, store = setup
    store.write("download_me.txt", b"content bytes")
    response = client.get("/files/download_me.txt")
    assert response.status_code == 200
    assert response.content == b"content bytes"


def test_get_nonexistent_returns_404(setup):
    client, _ = setup
    response = client.get("/files/nope.txt")
    assert response.status_code == 404


def test_health_endpoint(setup):
    client, _ = setup
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

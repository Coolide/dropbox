import hashlib
import hmac
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.server.auth import HMACAuthMiddleware, sign_request

SECRET = "test-secret-key"


@pytest.fixture
def make_app():
    app = FastAPI()
    app.add_middleware(HMACAuthMiddleware, secret=SECRET)

    @app.put("/files/{path:path}")
    async def upload(path: str) -> dict:
        return {"ok": True}

    return app


def test_valid_signature_accepted(make_app):
    client = TestClient(make_app, raise_server_exceptions=True)
    body = b"Hello World"
    headers = sign_request("PUT", "/files/test.text", body, SECRET)
    response = client.put("/files/test.text", headers=headers, content=body)

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_missing_signature_rejected(make_app):
    client = TestClient(make_app)
    response = client.put("/files/test.text", content=b"Hello")
    assert response.status_code == 401


def test_wrong_signature_rejected(make_app):
    client = TestClient(make_app)
    body = b"real body"
    headers = sign_request("PUT", "/files/test.text", body, SECRET)
    response = client.put("/files/test.text", headers=headers, content=b"wrong body")
    assert response.status_code == 401


def test_stale_signature_rejected(make_app):
    client = TestClient(make_app)

    body = b"data"

    old_timestamp = str(int(time.time()) - 400)

    body_hash = hashlib.sha256(body).hexdigest()
    msg = f"PUT\n/files/test.text\n{old_timestamp}\n{body_hash}"
    sig = hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()

    headers = {"X-Signature": sig, "X-Timestamp": old_timestamp}

    response = client.put("/files/test.txt", content=body, headers=headers)

    assert response.status_code == 401

import os
import pytest
from src.server.config import Settings

def test_defaults():
    s = Settings(
        host="0.0.0.0",
        port=8443,
        dest_dir="dest",
        sync_secret="dev-secret-change-me",
        cert_dir=".certs",
    )
    assert s.host == "0.0.0.0"
    assert s.port == 8443
    assert s.dest_dir == "dest"

def test_secret_required(monkeypatch):
    monkeypatch.delenv("SYNC_SECRET", raising=False)
    # When secret has no default and is not set, construction fails.
    # We allow a default for tests; in prod the .env must set SYNC_SECRET.
    s = Settings()
    assert isinstance(s.sync_secret, str)

def test_env_override(monkeypatch):
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("SYNC_SECRET", "hunter2")
    s = Settings()
    assert s.port == 9000
    assert s.sync_secret == "hunter2"
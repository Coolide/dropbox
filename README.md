# Open Source Dropbox

A bare-metal, self-hosted file sync tool. Drop files into a local folder and they appear on the server in real time — no cloud, no third party, full control.

## Contents

- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration](#configuration)
- [Running](#running)
- [All client flags](#all-client-flags)
- [Tests](#tests)
- [Project structure](#project-structure)
- [Security notes](#security-notes)
- [Design documentation](DESIGN.md)

---

## How it works

```
[ Client Machine ]                        [ Server Machine ]
  source_dir/                               dest_dir/
  └── notes/                                └── notes/
      └── todo.txt  ──── HTTPS + HMAC ────►     └── todo.txt
```

- **Watchdog** monitors the source directory for changes
- **HMAC-SHA256** signs every request so the server rejects anything not from your client
- **TLS** encrypts all traffic in transit
- On startup, the client does a full **manifest diff** to catch any files that changed while it was offline

---

## Requirements

- Python 3.14+
- uv package manager

Install uv on macOS / Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install uv on Windows:
```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

---

## Setup

```bash
git clone <your-repo-url>
cd dropbox-sync

# Create a local virtual environment pinned to Python 3.14
uv venv .venv --python 3.14

# Activate it
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Install all dependencies into the venv (not globally)
uv sync
```

---

## Configuration

Copy `.env.example` to `.env` on the **server machine** and fill in your values:

```bash
cp .env.example .env
```

Generate a strong shared secret — copy the output into `.env` and pass it to the client with `--secret`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Running

### Scenario A — Same trusted network, no certificate verification (quickest start)

Use this when both machines are on the same private WiFi/LAN and you want to get started immediately.

**Server** (run once, keep it running):
```bash
uv run server
```

**Client**:
```bash
uv run client \
  --source ~/path/to/folder \
  --server https://<server-ip>:8443 \
  --secret <your-shared-secret> \
  --no-verify
```

> `--no-verify` disables TLS certificate checking. Safe on a trusted private network,
> but do not use this over the internet.

---

### Scenario B — Two machines, verify with self-signed cert (recommended)

The server generates a self-signed certificate on first startup. Copy it to the client so it can verify the server's identity without disabling TLS.

**Step 1 — Start the server** (generates `.certs/cert.pem` automatically):
```bash
uv run server
```

**Step 2 — Copy the cert to the client machine** (`cert.pem` is public — safe to transfer):
```bash
scp user@<server-ip>:/path/to/project/.certs/cert.pem ~/server_cert.pem
```

**Step 3 — Start the client**:
```bash
uv run client \
  --source ~/path/to/folder \
  --server https://<server-ip>:8443 \
  --secret <your-shared-secret> \
  --cert ~/server_cert.pem
```

---

### Scenario C — Internet-facing server (production)

Use Let's Encrypt for a real trusted certificate instead of self-signed. Point uvicorn at the certbot-generated files:

```bash
# In .env on the server
CERT_DIR=/etc/letsencrypt/live/yourdomain.com
```

The client needs no `--cert` flag because Let's Encrypt certs are trusted by all systems by default.

---

## All client flags

```
uv run client --help

  --source      Local directory to watch and sync          (required)
  --server      Server base URL                            (default: https://localhost:8443)
  --secret      Shared HMAC secret — must match server     (default: $SYNC_SECRET)
  --cert        Path to server PEM cert for self-signed    (optional)
  --no-verify   Disable TLS verification entirely          (dev/LAN only)
  --manifest    Path to local manifest file                (default: ~/.sync_manifest.json)
```

---

## Tests

```bash
uv run pytest -v
```

---

## Project structure

```
dropbox-sync/
├── src/
│   ├── server/
│   │   ├── app.py        FastAPI app factory + uvicorn entry point
│   │   ├── routes.py     PUT / DELETE / GET /files endpoints
│   │   ├── auth.py       HMAC-SHA256 middleware
│   │   ├── storage.py    Path-safe disk I/O
│   │   ├── tls.py        Self-signed cert generation
│   │   └── config.py     Pydantic settings (env vars / .env)
│   └── client/
│       ├── cli.py        CLI entry point (argparse)
│       ├── watcher.py    Watchdog filesystem event handler
│       ├── manifest.py   SHA-256 state tracking (JSON on disk)
│       ├── sync.py       Offline diff: manifest vs disk
│       └── http.py       HMAC-signed httpx wrapper
├── tests/
│   ├── test_auth.py          HMAC middleware unit tests
│   ├── test_config.py        Settings unit tests
│   ├── test_storage.py       Storage layer unit tests
│   ├── test_manifest.py      Manifest unit tests
│   ├── test_sync.py          Diff logic unit tests
│   ├── test_routes.py        Route unit tests (no middleware)
│   ├── test_integration.py   Full stack integration tests
│   ├── test_http_client.py   SyncClient unit tests
│   └── test_watcher.py       Watchdog watcher unit tests
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Security notes

| Layer | What it protects against |
|---|---|
| TLS | Eavesdropping — encrypts all traffic in transit |
| HMAC-SHA256 | Unauthorised requests — only clients with the secret can talk to the server |
| Timestamp window (5 min) | Replay attacks — old captured requests are rejected |
| Body signing | Tampering — any modification to file bytes in transit is detected |
| Path traversal check | Directory escape attacks — `../../etc/passwd` style paths are blocked |

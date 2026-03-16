from fastapi import FastAPI

from src.server.auth import HMACAuthMiddleware
from src.server.config import Settings
from src.server.routes import make_router
from src.server.storage import Storage
from src.server.tls import ensure_certs


def create_app(settings: Settings | None = None) -> FastAPI:
    s = settings or Settings()
    store = Storage(s.dest_dir)
    app = FastAPI(title="Dropbox Sync Server")

    app.add_middleware(HMACAuthMiddleware, secret=s.sync_secret)

    app.include_router(make_router(store))

    return app


def run() -> None:
    import uvicorn

    settings = Settings()
    cert_path, key_path = ensure_certs(settings.cert_dir)

    print(
        f"[server] Listening on https://{settings.host}:{settings.port}"
    )  # TODO: use logging instead
    print(f"[server] Storing files in: {settings.dest_dir}")

    uvicorn.run(
        "src.server.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        ssl_certfile=str(cert_path),
        ssl_keyfile=str(key_path),
        reload=False,
    )

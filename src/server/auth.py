import hashlib
import hmac
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

TIMESTAMP_TOLERANCE = 300  # 5 minutes


def sign_request(
    method: str,
    path: str,
    body: bytes,
    secret: str,
) -> dict:
    timestamp = str(int(time.time()))
    body_hash = hashlib.sha256(body).hexdigest()
    signing_string = f"{method}\n{path}\n{timestamp}\n{body_hash}"

    signature = hmac.new(
        secret.encode(),
        signing_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    return {"X-Signature": signature, "X-Timestamp": timestamp}


class HMACAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, secret: str) -> None:
        super().__init__(app)
        self.secret = secret

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        sig_header = request.headers.get("X-Signature")
        timestamp_header = request.headers.get("X-Timestamp")

        if not sig_header or not timestamp_header:
            return JSONResponse(status_code=401, content={"error": "Missing auth headers"})

        try:
            request_timestamp = int(timestamp_header)
        except ValueError:
            return JSONResponse(status_code=401, content={"error": "Invalid timestamp"})

        if abs(time.time() - request_timestamp) > TIMESTAMP_TOLERANCE:
            return JSONResponse(status_code=401, content={"error": "Stale timestamp"})

        body = await request.body()
        body_hash = hashlib.sha256(body).hexdigest()
        signing_string = f"{request.method}\n{request.url.path}\n{request_timestamp}\n{body_hash}"

        expected_signature = hmac.new(
            self.secret.encode(),
            signing_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(sig_header, expected_signature):
            return JSONResponse(status_code=401, content={"error": "Invalid signature"})

        return await call_next(request)

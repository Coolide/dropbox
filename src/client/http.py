"""HMAC-signed httpx wrapper used by the sync engine.

SyncClient is intentionally synchronous — the watcher callback runs in a
standard thread, not an asyncio event loop, so sync httpx is simpler here.
"""

import httpx

from src.server.auth import sign_request


class SyncClient:
    def __init__(
        self,
        base_url: str,
        secret: str,
        verify: bool | str = True,
    ) -> None:
        self._secret = secret
        self._http = httpx.Client(base_url=base_url, verify=verify)

    def upload(self, relative_path: str, data: bytes) -> None:
        url_path = f"/files/{relative_path}"
        auth_headers = sign_request("PUT", url_path, data, self._secret)
        response = self._http.put(
            url_path,
            content=data,
            headers=auth_headers,
        )
        response.raise_for_status()

    def delete(self, relative_path: str) -> None:
        url_path = f"/files/{relative_path}"
        auth_headers = sign_request("DELETE", url_path, b"", self._secret)
        response = self._http.delete(url_path, headers=auth_headers)
        response.raise_for_status()

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> SyncClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

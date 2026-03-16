import httpx
import pytest
import respx

from src.client.http import SyncClient

BASE_URL = "https://localhost:8443"
SECRET = "test-secret-key"


@respx.mock
def test_upload_put_file():
    route = respx.put(f"{BASE_URL}/files/test.txt").mock(
        return_value=httpx.Response(200, json={"path": "test.txt", "bytes": 5})
    )
    client = SyncClient(base_url=BASE_URL, secret=SECRET, verify=False)
    client.upload("test.txt", b"hello")
    assert route.called


@respx.mock
def test_delete_sends_delete_request():
    route = respx.delete(f"{BASE_URL}/files/old.txt").mock(
        return_value=httpx.Response(200, json={"deleted": "old.txt"})
    )

    client = SyncClient(base_url=BASE_URL, secret=SECRET, verify=False)
    client.delete("old.txt")
    assert route.called


@respx.mock
def test_upload_raises_on_server_error():
    respx.put(f"{BASE_URL}/files/bad.txt").mock(
        return_value=httpx.Response(500, json={"error": "Server error"})
    )
    client = SyncClient(base_url=BASE_URL, secret=SECRET, verify=False)
    with pytest.raises(httpx.HTTPStatusError):
        client.upload("bad.txt", b"data")

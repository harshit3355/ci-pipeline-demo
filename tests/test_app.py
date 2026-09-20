"""HTTP-level tests for the demo service."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator

import pytest

from src.app import create_server


@pytest.fixture
def service_url() -> Iterator[str]:
    server = create_server(host="127.0.0.1", port=0, version="test-version")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_homepage_includes_message_and_version(service_url: str) -> None:
    with urllib.request.urlopen(f"{service_url}/", timeout=2) as response:
        payload = json.load(response)

    assert response.status == 200
    assert payload == {
        "message": "CI Pipeline Demo",
        "version": "test-version",
    }


def test_health_endpoint_returns_ok(service_url: str) -> None:
    with urllib.request.urlopen(f"{service_url}/health", timeout=2) as response:
        payload = json.load(response)

    assert response.status == 200
    assert payload == {"status": "ok"}


def test_unknown_path_returns_json_404(service_url: str) -> None:
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(f"{service_url}/missing", timeout=2)

    assert error.value.code == 404
    assert json.load(error.value) == {"error": "not found"}

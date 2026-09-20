"""A tiny HTTP service for practicing CI, containers, and observability."""

from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


LOGGER = logging.getLogger("ci_pipeline_demo")


class DemoRequestHandler(BaseHTTPRequestHandler):
    """Serve a status page and health endpoint."""

    server: ThreadingHTTPServer

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path == "/":
            status_code = 200
            payload: dict[str, Any] = {
                "message": "CI Pipeline Demo",
                "version": self.server.app_version,  # type: ignore[attr-defined]
            }
        elif self.path == "/health":
            status_code = 200
            payload = {"status": "ok"}
        else:
            status_code = 404
            payload = {"error": "not found"}

        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string: str, *args: object) -> None:
        LOGGER.info("%s - %s", self.address_string(), format_string % args)


def create_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    version: str | None = None,
) -> ThreadingHTTPServer:
    """Create the HTTP server; the injectable bind address supports tests."""
    server = ThreadingHTTPServer((host, port), DemoRequestHandler)
    server.app_version = version or os.environ.get("APP_VERSION", "dev")  # type: ignore[attr-defined]
    return server


def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    port = int(os.environ.get("APP_PORT", "8080"))
    server = create_server(port=port)
    LOGGER.info("Starting demo service on port %s", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("Shutting down demo service")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

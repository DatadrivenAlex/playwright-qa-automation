"""Start the demo shop on a free local port for the test session."""

from __future__ import annotations

import socket
import threading
import time

import httpx
import uvicorn

from demo_app.main import create_app


class EmbeddedServer:
    def __init__(self) -> None:
        self.base_url = ""
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> str:
        last_error: Exception | None = None
        for _ in range(5):
            port = _free_port()
            config = uvicorn.Config(
                create_app(),
                host="127.0.0.1",
                port=port,
                log_level="warning",
                access_log=False,
            )
            server = _QuietServer(config)
            thread = threading.Thread(target=server.run, name="harbor-sut", daemon=True)
            thread.start()
            try:
                _wait_until_ready(server, port)
            except TimeoutError as exc:
                server.should_exit = True
                thread.join(timeout=2)
                last_error = exc
                continue
            self._server = server
            self._thread = thread
            self.base_url = f"http://127.0.0.1:{port}"
            return self.base_url
        raise RuntimeError("Could not start the demo shop") from last_error

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)


class _QuietServer(uvicorn.Server):
    def install_signal_handlers(self) -> None:
        return


def wait_until_healthy(base_url: str, timeout_seconds: float = 15) -> None:
    deadline = time.monotonic() + timeout_seconds
    url = f"{base_url.rstrip('/')}/health"
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            response = httpx.get(url, timeout=0.5)
            if response.status_code == 200:
                return
        except httpx.HTTPError as exc:
            last_error = exc
        time.sleep(0.1)
    raise TimeoutError(f"Demo shop did not become healthy at {url}") from last_error


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_until_ready(server: uvicorn.Server, port: int) -> None:
    deadline = time.monotonic() + 15
    url = f"http://127.0.0.1:{port}/health"
    while time.monotonic() < deadline:
        if getattr(server, "started", False):
            try:
                response = httpx.get(url, timeout=0.5)
                if response.status_code == 200:
                    return
            except httpx.HTTPError:
                pass
        time.sleep(0.05)
    raise TimeoutError(f"demo shop did not answer on port {port}")

"""Session app, HTTP clients, and failure screenshots for the HTML report."""

from __future__ import annotations

import base64
import re
from collections.abc import Callable, Iterator
from pathlib import Path

import httpx
import pytest
import pytest_html

from qa_framework.server import EmbeddedServer, wait_until_healthy
from qa_framework.settings import Settings, headless_forced_off, load_settings
from tests.factories import UserFactory

_BROWSERS = {"chromium", "firefox", "webkit"}


def pytest_configure(config: pytest.Config) -> None:
    settings = load_settings()
    for folder in ("reports/playwright", "reports/screenshots", "reports/allure-results"):
        Path(folder).mkdir(parents=True, exist_ok=True)
    if settings.browser not in _BROWSERS:
        raise pytest.UsageError("BROWSER must be chromium, firefox, or webkit.")
    if not config.getoption("--browser"):
        config.option.browser = [settings.browser]
    if headless_forced_off():
        config.option.headed = True
    if not config.getoption("--slowmo"):
        config.option.slowmo = settings.slow_mo_ms


@pytest.fixture(scope="session")
def settings() -> Settings:
    return load_settings()


@pytest.fixture(scope="session")
def base_url(pytestconfig: pytest.Config) -> Iterator[str]:
    configured = (pytestconfig.getoption("--base-url") or "").strip()
    if not configured:
        configured = load_settings().base_url or ""
    if configured:
        wait_until_healthy(configured)
        yield configured.rstrip("/")
        return
    server = EmbeddedServer()
    server.start()
    try:
        yield server.base_url
    finally:
        server.stop()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    return {**browser_context_args, "viewport": {"width": 1280, "height": 800}}


@pytest.fixture(autouse=True)
def _page_timeout(request: pytest.FixtureRequest, settings: Settings) -> None:
    if "page" not in request.fixturenames:
        return
    page = request.getfixturevalue("page")
    page.set_default_timeout(settings.action_timeout_ms)


@pytest.fixture
def api(base_url: str) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        yield client


@pytest.fixture
def auth_api(api: httpx.Client) -> httpx.Client:
    response = api.post("/api/login", json=UserFactory.valid().credentials())
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    api.headers["Authorization"] = f"Bearer {token}"
    return api


@pytest.fixture
def login(base_url: str) -> Iterator[Callable[[UserFactory], httpx.Client]]:
    clients: list[httpx.Client] = []

    def _open(user: UserFactory) -> httpx.Client:
        client = httpx.Client(base_url=base_url, timeout=10.0)
        response = client.post("/api/login", json=user.credentials())
        assert response.status_code == 200, response.text
        client.headers["Authorization"] = f"Bearer {response.json()['token']}"
        clients.append(client)
        return client

    yield _open
    for client in clients:
        client.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> Iterator[None]:
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    page = item.funcargs.get("page")
    if page is None:
        return
    try:
        png = page.screenshot(full_page=True)
    except Exception:
        return
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", item.nodeid)[:180]
    target = Path("reports/screenshots") / f"{safe_name}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(png)
    encoded = base64.b64encode(png).decode("ascii")
    report.extras = [
        *getattr(report, "extras", []),
        pytest_html.extras.png(encoded, name="Failure screenshot"),
    ]

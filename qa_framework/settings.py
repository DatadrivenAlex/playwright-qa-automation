"""Runtime configuration loaded from the environment and an optional .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_FALSY = {"0", "false", "no", "off"}


def load_dotenv(path: Path | None = None) -> None:
    """Load KEY=VALUE lines. Existing environment variables win."""
    env_file = path or Path(__file__).resolve().parents[1] / ".env"
    if not env_file.is_file():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    base_url: str | None
    demo_username: str
    demo_password: str
    headless: bool
    browser: str
    slow_mo_ms: int
    action_timeout_ms: int


def load_settings() -> Settings:
    load_dotenv()
    base_url = os.getenv("BASE_URL", "").strip() or None
    headless_raw = os.getenv("HEADLESS", "true").strip().lower()
    browser = os.getenv("BROWSER", "chromium").strip().lower() or "chromium"
    return Settings(
        base_url=base_url.rstrip("/") if base_url else None,
        demo_username=os.getenv("DEMO_USERNAME", "alex").strip() or "alex",
        demo_password=os.getenv("DEMO_PASSWORD", "demo123"),
        headless=headless_raw not in _FALSY,
        browser=browser,
        slow_mo_ms=_positive_int("SLOW_MO", 0),
        action_timeout_ms=_positive_int("ACTION_TIMEOUT_MS", 15000),
    )


def headless_forced_off() -> bool:
    return os.getenv("HEADLESS", "").strip().lower() in _FALSY


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")
    return value


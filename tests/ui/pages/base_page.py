"""Shared navigation for Harbor Market pages."""

from __future__ import annotations

from playwright.sync_api import Locator, Page


class BasePage:
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")

    def goto(self, path: str) -> None:
        if not path.startswith("/"):
            path = f"/{path}"
        self.page.goto(f"{self.base_url}{path}")

    @property
    def cart_count(self) -> Locator:
        return self.page.get_by_test_id("cart-count")

    @property
    def flash(self) -> Locator:
        return self.page.get_by_test_id("flash")

    @property
    def greeting(self) -> Locator:
        return self.page.get_by_test_id("greeting")

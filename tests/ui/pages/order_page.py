"""Order confirmation."""

from __future__ import annotations

from playwright.sync_api import Locator

from tests.ui.pages.base_page import BasePage


class OrderPage(BasePage):
    @property
    def number(self) -> Locator:
        return self.page.get_by_test_id("order-number")

    @property
    def total(self) -> Locator:
        return self.page.get_by_test_id("order-total")

    @property
    def status(self) -> Locator:
        return self.page.get_by_test_id("order-status")

    @property
    def heading(self) -> Locator:
        return self.page.get_by_role("heading", name="Order placed")

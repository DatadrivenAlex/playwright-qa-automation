"""Checkout form."""

from __future__ import annotations

from playwright.sync_api import Locator

from tests.ui.pages.base_page import BasePage


class CheckoutPage(BasePage):
    def open(self) -> CheckoutPage:
        self.goto("/checkout")
        return self

    def fill(self, data: dict[str, str]) -> None:
        for field, value in data.items():
            self.page.get_by_test_id(field).fill(value)

    def submit(self) -> None:
        self.page.get_by_test_id("checkout-submit").click()

    def place_order(self, data: dict[str, str]) -> None:
        self.fill(data)
        self.submit()

    def field_error(self, field: str) -> Locator:
        return self.page.get_by_test_id(f"error-{field}")

    @property
    def blocked(self) -> Locator:
        return self.page.get_by_test_id("checkout-blocked")

    @property
    def heading(self) -> Locator:
        return self.page.get_by_role("heading", name="Checkout")

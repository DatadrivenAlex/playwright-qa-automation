"""Shopping cart."""

from __future__ import annotations

from playwright.sync_api import Locator

from tests.ui.pages.base_page import BasePage


class CartPage(BasePage):
    def open(self) -> CartPage:
        self.goto("/cart")
        return self

    def line_names(self) -> list[str]:
        return [text.strip() for text in self.page.get_by_test_id("line-name").all_inner_texts()]

    def set_quantity(self, product_id: str, quantity: int) -> None:
        self.page.get_by_test_id(f"qty-{product_id}").fill(str(quantity))
        self.page.get_by_test_id(f"update-{product_id}").click()

    def remove(self, product_id: str) -> None:
        self.page.get_by_test_id(f"remove-{product_id}").click()

    def proceed_to_checkout(self) -> None:
        self.page.get_by_test_id("checkout-link").click()

    @property
    def total(self) -> Locator:
        return self.page.get_by_test_id("cart-total")

    @property
    def empty(self) -> Locator:
        return self.page.get_by_test_id("cart-empty")

"""Product list."""

from __future__ import annotations

from playwright.sync_api import Locator

from tests.ui.pages.base_page import BasePage


class CatalogPage(BasePage):
    def open(self) -> CatalogPage:
        self.goto("/catalog")
        return self

    @property
    def heading(self) -> Locator:
        return self.page.get_by_role("heading", name="Catalog")

    def product_names(self) -> list[str]:
        return [text.strip() for text in self.page.get_by_test_id("product-name").all_inner_texts()]

    def price_for(self, product_id: str) -> Locator:
        card = self.page.locator(f"[data-product-id='{product_id}']")
        return card.get_by_test_id("product-price")

    def add_to_cart(self, product_id: str, quantity: int = 1) -> None:
        if quantity != 1:
            self.page.get_by_test_id(f"quantity-{product_id}").fill(str(quantity))
        self.page.get_by_test_id(f"add-{product_id}").click()

    def log_out(self) -> None:
        self.page.get_by_test_id("logout").click()

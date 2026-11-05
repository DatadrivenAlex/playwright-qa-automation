"""Cart updates from the browser."""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import expect

from tests.factories import CatalogFactory
from tests.ui.pages.cart_page import CartPage
from tests.ui.pages.catalog_page import CatalogPage


@allure.feature("Cart")
@allure.story("Update quantity")
@pytest.mark.regression
@pytest.mark.ui
def test_update_quantity_recalculates_the_total(logged_in_catalog: CatalogPage) -> None:
    logged_in_catalog.add_to_cart(CatalogFactory.MUG.id)
    cart = CartPage(logged_in_catalog.page, logged_in_catalog.base_url)
    cart.open()
    expect(cart.total).to_have_text("$12.00")
    cart.set_quantity(CatalogFactory.MUG.id, 3)
    expect(cart.flash).to_have_text("Cart updated.")
    expect(cart.total).to_have_text("$36.00")
    expect(cart.cart_count).to_have_text("3")


@allure.feature("Cart")
@allure.story("Remove an item")
@pytest.mark.regression
@pytest.mark.ui
def test_remove_item_shows_an_empty_cart(logged_in_catalog: CatalogPage) -> None:
    logged_in_catalog.add_to_cart(CatalogFactory.COASTERS.id)
    cart = CartPage(logged_in_catalog.page, logged_in_catalog.base_url)
    cart.open()
    assert cart.line_names() == [CatalogFactory.COASTERS.name]
    cart.remove(CatalogFactory.COASTERS.id)
    expect(cart.flash).to_have_text("Removed from cart.")
    expect(cart.empty).to_be_visible()
    expect(cart.cart_count).to_have_text("0")

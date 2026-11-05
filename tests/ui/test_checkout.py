"""Checkout form, from an empty cart through a placed order."""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import expect

from tests.factories import CatalogFactory, CheckoutFactory
from tests.ui.pages.cart_page import CartPage
from tests.ui.pages.catalog_page import CatalogPage
from tests.ui.pages.checkout_page import CheckoutPage
from tests.ui.pages.order_page import OrderPage


@allure.feature("Checkout")
@allure.story("Place an order")
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.ui
def test_checkout_happy_path(logged_in_catalog: CatalogPage) -> None:
    logged_in_catalog.add_to_cart(CatalogFactory.LAMP.id)
    cart = CartPage(logged_in_catalog.page, logged_in_catalog.base_url)
    cart.open()
    cart.proceed_to_checkout()
    checkout = CheckoutPage(logged_in_catalog.page, logged_in_catalog.base_url)
    expect(checkout.heading).to_be_visible()
    expect(logged_in_catalog.page.get_by_test_id("checkout-total")).to_have_text("$34.00")
    checkout.place_order(CheckoutFactory.valid())
    order = OrderPage(logged_in_catalog.page, logged_in_catalog.base_url)
    expect(order.heading).to_be_visible()
    expect(order.number).to_have_text(re.compile(r"HM-\d+"))
    expect(order.status).to_have_text("placed")
    expect(order.total).to_have_text("$34.00")
    expect(logged_in_catalog.cart_count).to_have_text("0")


@allure.feature("Checkout")
@allure.story("Validation")
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.parametrize(
    ("overrides", "field", "message"),
    [
        pytest.param(
            {"email": "not-an-email"},
            "email",
            "Enter a valid email.",
            id="bad-email",
        ),
        pytest.param(
            {"full_name": "A"},
            "full_name",
            "Enter your full name.",
            id="short-name",
        ),
        pytest.param(
            {"address": "x"},
            "address",
            "Enter a street address.",
            id="short-address",
        ),
    ],
)
def test_checkout_rejects_invalid_fields(
    logged_in_catalog: CatalogPage,
    overrides: dict[str, str],
    field: str,
    message: str,
) -> None:
    logged_in_catalog.add_to_cart(CatalogFactory.MUG.id)
    checkout = CheckoutPage(logged_in_catalog.page, logged_in_catalog.base_url)
    checkout.open()
    checkout.place_order(CheckoutFactory.valid(**overrides))
    expect(checkout.field_error(field)).to_have_text(message)
    expect(checkout.page).to_have_url(re.compile(r"/checkout$"))


@allure.feature("Checkout")
@allure.story("Empty cart")
@pytest.mark.regression
@pytest.mark.ui
def test_checkout_empty_cart_is_blocked(logged_in_catalog: CatalogPage) -> None:
    checkout = CheckoutPage(logged_in_catalog.page, logged_in_catalog.base_url)
    checkout.open()
    expect(checkout.blocked).to_be_visible()
    expect(checkout.page.get_by_test_id("checkout-submit")).to_have_count(0)

"""Catalog browsing and add-to-cart."""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from qa_framework.settings import Settings
from tests.factories import CatalogFactory
from tests.ui.pages.catalog_page import CatalogPage
from tests.ui.pages.login_page import LoginPage


@allure.feature("Catalog")
@allure.story("List products")
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.ui
def test_catalog_lists_seed_products(page: Page, base_url: str) -> None:
    catalog = CatalogPage(page, base_url)
    catalog.open()
    expect(catalog.heading).to_be_visible()
    assert catalog.product_names() == [product.name for product in CatalogFactory.all()]
    expect(catalog.price_for(CatalogFactory.MUG.id)).to_have_text("$12.00")
    expect(catalog.price_for(CatalogFactory.LAMP.id)).to_have_text("$34.00")


@allure.feature("Catalog")
@allure.story("Add an item")
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.ui
def test_add_to_cart_updates_the_badge(logged_in_catalog: CatalogPage) -> None:
    logged_in_catalog.add_to_cart(CatalogFactory.MUG.id)
    expect(logged_in_catalog.flash).to_have_text("Added Ceramic Mug to cart.")
    expect(logged_in_catalog.cart_count).to_have_text("1")


@allure.feature("Catalog")
@allure.story("Add an item")
@pytest.mark.regression
@pytest.mark.ui
def test_add_to_cart_respects_the_quantity(logged_in_catalog: CatalogPage) -> None:
    logged_in_catalog.add_to_cart(CatalogFactory.NOTEBOOK.id, quantity=2)
    expect(logged_in_catalog.flash).to_have_text("Added Linen Notebook to cart.")
    expect(logged_in_catalog.cart_count).to_have_text("2")


@allure.feature("Catalog")
@allure.story("Auth boundary")
@pytest.mark.regression
@pytest.mark.ui
def test_adding_without_a_session_asks_for_login(
    page: Page,
    base_url: str,
    settings: Settings,
) -> None:
    catalog = CatalogPage(page, base_url)
    catalog.open()
    catalog.add_to_cart(CatalogFactory.MUG.id)
    expect(page).to_have_url(re.compile(r"/login\?next=/catalog"))
    login = LoginPage(page, base_url)
    login.sign_in(settings.demo_username, settings.demo_password)
    expect(page.get_by_test_id("cart-count")).to_have_text("0")

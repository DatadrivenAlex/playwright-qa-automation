"""UI fixtures. The browser itself comes from pytest-playwright."""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from qa_framework.settings import Settings
from tests.ui.pages.catalog_page import CatalogPage
from tests.ui.pages.login_page import LoginPage


@pytest.fixture
def login_page(page, base_url: str) -> LoginPage:
    return LoginPage(page, base_url)


@pytest.fixture
def logged_in_catalog(login_page: LoginPage, settings: Settings) -> CatalogPage:
    login_page.open()
    login_page.sign_in(settings.demo_username, settings.demo_password)
    catalog = CatalogPage(login_page.page, login_page.base_url)
    expect(catalog.heading).to_be_visible()
    return catalog

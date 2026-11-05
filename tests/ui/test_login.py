"""Sign-in screen."""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import expect

from qa_framework.settings import load_settings
from tests.factories import UserFactory
from tests.ui.pages.catalog_page import CatalogPage
from tests.ui.pages.login_page import LoginPage

_USER = load_settings()


@allure.feature("Authentication")
@allure.story("Sign in")
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.ui
def test_valid_login_lands_on_catalog(login_page: LoginPage) -> None:
    login_page.open()
    expect(login_page.heading).to_be_visible()
    login_page.sign_in(_USER.demo_username, _USER.demo_password)
    catalog = CatalogPage(login_page.page, login_page.base_url)
    expect(catalog.heading).to_be_visible()
    expect(login_page.greeting).to_contain_text(UserFactory.valid().display_name)


@allure.feature("Authentication")
@allure.story("Rejected credentials")
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.parametrize(
    ("username", "password", "message"),
    [
        pytest.param(
            _USER.demo_username,
            "wrong-password",
            "Those credentials do not match.",
            id="bad-password",
        ),
        pytest.param(
            "nobody",
            "demo123",
            "Those credentials do not match.",
            id="unknown-user",
        ),
        pytest.param("", "", "Enter your username and password.", id="blank"),
    ],
)
def test_invalid_login_shows_an_error(
    login_page: LoginPage,
    username: str,
    password: str,
    message: str,
) -> None:
    login_page.open()
    login_page.sign_in(username, password)
    expect(login_page.error).to_have_text(message)
    expect(login_page.page).to_have_url(re.compile(r"/login$"))


@allure.feature("Authentication")
@allure.story("Sign out")
@pytest.mark.regression
@pytest.mark.ui
def test_logout_returns_to_login(logged_in_catalog: CatalogPage) -> None:
    logged_in_catalog.log_out()
    expect(logged_in_catalog.page).to_have_url(re.compile(r"/login$"))
    expect(logged_in_catalog.page.get_by_role("heading", name="Sign in")).to_be_visible()


@allure.feature("Authentication")
@allure.story("Auth boundary")
@pytest.mark.regression
@pytest.mark.ui
def test_cart_requires_login(login_page: LoginPage) -> None:
    login_page.goto("/cart")
    expect(login_page.page).to_have_url(re.compile(r"/login\?next=/cart"))
    expect(login_page.heading).to_be_visible()

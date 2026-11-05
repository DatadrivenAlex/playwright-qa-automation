"""Sign-in screen."""

from __future__ import annotations

from playwright.sync_api import Locator

from tests.ui.pages.base_page import BasePage


class LoginPage(BasePage):
    def open(self) -> LoginPage:
        self.goto("/login")
        return self

    def sign_in(self, username: str, password: str) -> None:
        self.page.get_by_test_id("username").fill(username)
        self.page.get_by_test_id("password").fill(password)
        self.page.get_by_test_id("login-submit").click()

    @property
    def error(self) -> Locator:
        return self.page.get_by_test_id("login-error")

    @property
    def heading(self) -> Locator:
        return self.page.get_by_role("heading", name="Sign in")

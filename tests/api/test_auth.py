"""Login and logout over HTTP."""

from __future__ import annotations

import allure
import httpx
import pytest

from tests.factories import UserFactory


@allure.feature("Authentication")
@allure.story("Sign in")
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.api
def test_login_success(api: httpx.Client) -> None:
    user = UserFactory.valid()
    response = api.post("/api/login", json=user.credentials())
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == user.username
    assert body["display_name"] == user.display_name
    assert body["token"]


@allure.feature("Authentication")
@allure.story("Rejected credentials")
@pytest.mark.regression
@pytest.mark.api
def test_login_rejects_bad_password(api: httpx.Client) -> None:
    response = api.post("/api/login", json=UserFactory.invalid_password())
    assert response.status_code == 401
    assert response.json()["detail"] == "Those credentials do not match."


@allure.feature("Authentication")
@allure.story("Rejected credentials")
@pytest.mark.regression
@pytest.mark.api
def test_login_rejects_unknown_user(api: httpx.Client) -> None:
    response = api.post("/api/login", json=UserFactory.unknown())
    assert response.status_code == 401
    assert response.json()["detail"] == "Those credentials do not match."


@allure.feature("Authentication")
@allure.story("Rejected credentials")
@pytest.mark.regression
@pytest.mark.api
def test_login_rejects_blank_fields(api: httpx.Client) -> None:
    response = api.post("/api/login", json={"username": "  ", "password": ""})
    assert response.status_code == 422
    assert response.json()["detail"] == "Enter your username and password."


@allure.feature("Authentication")
@allure.story("Rejected credentials")
@pytest.mark.regression
@pytest.mark.api
@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"password": "demo123"}, id="missing-username"),
        pytest.param({"username": "alex"}, id="missing-password"),
        pytest.param({}, id="empty-body"),
    ],
)
def test_login_missing_fields(api: httpx.Client, payload: dict[str, str]) -> None:
    response = api.post("/api/login", json=payload)
    assert response.status_code == 422


@allure.feature("Authentication")
@allure.story("Sign out")
@pytest.mark.regression
@pytest.mark.api
def test_logout_rejects_reused_token(api: httpx.Client) -> None:
    login = api.post("/api/login", json=UserFactory.valid().credentials())
    api.headers["Authorization"] = f"Bearer {login.json()['token']}"
    assert api.post("/api/logout").status_code == 200
    assert api.get("/api/cart").status_code == 401

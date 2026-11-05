"""Placing an order and reading it back."""

from __future__ import annotations

import re
from collections.abc import Callable

import allure
import httpx
import pytest

from tests.factories import CartFactory, CatalogFactory, CheckoutFactory, UserFactory


def _add_mug(client: httpx.Client) -> None:
    response = client.post("/api/cart/items", json=CartFactory.item(CatalogFactory.MUG))
    assert response.status_code == 200, response.text


@allure.feature("Checkout")
@allure.story("Place an order")
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.api
def test_checkout_success(auth_api: httpx.Client) -> None:
    _add_mug(auth_api)
    response = auth_api.post("/api/checkout", json=CheckoutFactory.valid())
    assert response.status_code == 201
    body = response.json()
    assert re.fullmatch(r"HM-\d+", body["id"])
    assert body["status"] == "placed"
    assert body["total_cents"] == CatalogFactory.MUG.price_cents
    assert body["email"] == "alex@example.com"
    assert body["items"][0]["name"] == CatalogFactory.MUG.name
    assert auth_api.get("/api/cart").json()["item_count"] == 0


@allure.feature("Checkout")
@allure.story("Empty cart")
@pytest.mark.regression
@pytest.mark.api
def test_checkout_empty_cart(auth_api: httpx.Client) -> None:
    response = auth_api.post("/api/checkout", json=CheckoutFactory.valid())
    assert response.status_code == 409
    assert response.json()["detail"] == "Cart is empty."


@allure.feature("Checkout")
@allure.story("Validation")
@pytest.mark.regression
@pytest.mark.api
@pytest.mark.parametrize(
    "email",
    [
        pytest.param("not-an-email", id="missing-at"),
        pytest.param("a@", id="missing-domain"),
        pytest.param("alex@localhost", id="missing-dot"),
        pytest.param("", id="blank"),
    ],
)
def test_checkout_rejects_invalid_email(auth_api: httpx.Client, email: str) -> None:
    _add_mug(auth_api)
    response = auth_api.post("/api/checkout", json=CheckoutFactory.valid(email=email))
    assert response.status_code == 422
    assert response.json()["errors"]["email"] == "Enter a valid email."
    assert auth_api.get("/api/cart").json()["item_count"] == 1


@allure.feature("Checkout")
@allure.story("Validation")
@pytest.mark.regression
@pytest.mark.api
def test_checkout_rejects_a_short_name(auth_api: httpx.Client) -> None:
    _add_mug(auth_api)
    response = auth_api.post("/api/checkout", json=CheckoutFactory.valid(full_name="A"))
    assert response.status_code == 422
    assert response.json()["errors"]["full_name"] == "Enter your full name."


@allure.feature("Checkout")
@allure.story("Order lookup")
@pytest.mark.regression
@pytest.mark.api
def test_order_lookup(auth_api: httpx.Client) -> None:
    _add_mug(auth_api)
    created = auth_api.post("/api/checkout", json=CheckoutFactory.valid())
    order_id = created.json()["id"]
    fetched = auth_api.get(f"/api/orders/{order_id}")
    assert fetched.status_code == 200
    assert fetched.json()["total"] == "$12.00"
    history = auth_api.get("/api/orders")
    assert history.status_code == 200
    assert order_id in [order["id"] for order in history.json()]


@allure.feature("Checkout")
@allure.story("Order lookup")
@pytest.mark.regression
@pytest.mark.api
def test_order_is_hidden_from_another_customer(
    login: Callable[[UserFactory], httpx.Client],
) -> None:
    alex = login(UserFactory.valid())
    _add_mug(alex)
    order_id = alex.post("/api/checkout", json=CheckoutFactory.valid()).json()["id"]
    guest = login(UserFactory.second_customer())
    hidden = guest.get(f"/api/orders/{order_id}")
    assert hidden.status_code == 404
    assert hidden.json()["detail"] == "Order not found."
    assert alex.get(f"/api/orders/{order_id}").status_code == 200


@allure.feature("Checkout")
@allure.story("Order lookup")
@pytest.mark.regression
@pytest.mark.api
def test_unknown_order_is_not_found(auth_api: httpx.Client) -> None:
    response = auth_api.get("/api/orders/HM-9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found."

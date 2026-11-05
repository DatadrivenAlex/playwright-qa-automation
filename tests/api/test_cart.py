"""Cart mutations. Each test logs in, so it owns a private session."""

from __future__ import annotations

from collections.abc import Callable

import allure
import httpx
import pytest

from tests.factories import CartFactory, CatalogFactory, UserFactory


@allure.feature("Cart")
@allure.story("Auth boundary")
@pytest.mark.regression
@pytest.mark.api
def test_cart_requires_auth(api: httpx.Client) -> None:
    response = api.get("/api/cart")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@allure.feature("Cart")
@allure.story("Add an item")
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.api
def test_add_lists_line_and_total(auth_api: httpx.Client) -> None:
    response = auth_api.post("/api/cart/items", json=CartFactory.item(CatalogFactory.MUG, 2))
    assert response.status_code == 200
    body = response.json()
    assert body["item_count"] == 2
    assert body["total_cents"] == 2400
    assert body["items"][0]["name"] == CatalogFactory.MUG.name
    listed = auth_api.get("/api/cart")
    assert listed.status_code == 200
    assert listed.json()["total"] == "$24.00"


@allure.feature("Cart")
@allure.story("Add an item")
@pytest.mark.regression
@pytest.mark.api
def test_adding_the_same_product_accumulates(auth_api: httpx.Client) -> None:
    assert auth_api.post("/api/cart/items", json=CartFactory.item(quantity=1)).status_code == 200
    response = auth_api.post("/api/cart/items", json=CartFactory.item(quantity=2))
    assert response.status_code == 200
    assert response.json()["items"][0]["quantity"] == 3
    assert response.json()["total_cents"] == 3600


@allure.feature("Cart")
@allure.story("Add an item")
@pytest.mark.regression
@pytest.mark.api
def test_add_accepts_the_maximum_quantity(auth_api: httpx.Client) -> None:
    response = auth_api.post("/api/cart/items", json=CartFactory.item(quantity=10))
    assert response.status_code == 200
    assert response.json()["items"][0]["quantity"] == 10


@allure.feature("Cart")
@allure.story("Update quantity")
@pytest.mark.regression
@pytest.mark.api
def test_update_quantity(auth_api: httpx.Client) -> None:
    auth_api.post("/api/cart/items", json=CartFactory.item(CatalogFactory.MUG, 1))
    response = auth_api.patch(
        f"/api/cart/items/{CatalogFactory.MUG.id}",
        json={"quantity": 4},
    )
    assert response.status_code == 200
    assert response.json()["total_cents"] == 4800
    assert response.json()["item_count"] == 4


@allure.feature("Cart")
@allure.story("Remove an item")
@pytest.mark.regression
@pytest.mark.api
def test_remove_item(auth_api: httpx.Client) -> None:
    auth_api.post("/api/cart/items", json=CartFactory.item(CatalogFactory.MUG))
    auth_api.post("/api/cart/items", json=CartFactory.item(CatalogFactory.NOTEBOOK))
    response = auth_api.delete(f"/api/cart/items/{CatalogFactory.MUG.id}")
    assert response.status_code == 200
    names = [item["name"] for item in response.json()["items"]]
    assert names == [CatalogFactory.NOTEBOOK.name]


@allure.feature("Cart")
@allure.story("Rejected item")
@pytest.mark.regression
@pytest.mark.api
def test_unknown_product_is_rejected(auth_api: httpx.Client) -> None:
    response = auth_api.post("/api/cart/items", json={"product_id": "nope", "quantity": 1})
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found."


@allure.feature("Cart")
@allure.story("Rejected item")
@pytest.mark.regression
@pytest.mark.api
@pytest.mark.parametrize("quantity", [0, -1, 11])
def test_invalid_quantity_is_rejected(auth_api: httpx.Client, quantity: int) -> None:
    response = auth_api.post(
        "/api/cart/items",
        json={"product_id": CatalogFactory.MUG.id, "quantity": quantity},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Quantity must be between 1 and 10."


@allure.feature("Cart")
@allure.story("Rejected item")
@pytest.mark.regression
@pytest.mark.api
def test_quantity_must_be_a_number(auth_api: httpx.Client) -> None:
    response = auth_api.post(
        "/api/cart/items",
        json={"product_id": CatalogFactory.MUG.id, "quantity": "two"},
    )
    assert response.status_code == 422


@allure.feature("Cart")
@allure.story("Rejected item")
@pytest.mark.regression
@pytest.mark.api
def test_quantity_above_stock_is_rejected(auth_api: httpx.Client) -> None:
    response = auth_api.post("/api/cart/items", json=CartFactory.item(CatalogFactory.THROW, 6))
    assert response.status_code == 409
    assert response.json()["detail"] == "Not enough stock for that quantity."


@allure.feature("Cart")
@allure.story("Isolation")
@pytest.mark.regression
@pytest.mark.api
def test_sessions_do_not_share_carts(login: Callable[[UserFactory], httpx.Client]) -> None:
    alex = login(UserFactory.valid())
    guest = login(UserFactory.second_customer())
    alex.post("/api/cart/items", json=CartFactory.item(CatalogFactory.MUG))
    guest.post("/api/cart/items", json=CartFactory.item(CatalogFactory.LAMP))
    assert alex.get("/api/cart").json()["items"][0]["product_id"] == CatalogFactory.MUG.id
    assert guest.get("/api/cart").json()["items"][0]["product_id"] == CatalogFactory.LAMP.id

"""Public catalog and service health."""

from __future__ import annotations

import allure
import httpx
import pytest

from tests.factories import CatalogFactory


@allure.feature("Catalog")
@allure.story("Health")
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.api
def test_health(api: httpx.Client) -> None:
    response = api.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@allure.feature("Catalog")
@allure.story("List products")
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.api
def test_list_products(api: httpx.Client) -> None:
    response = api.get("/api/products")
    assert response.status_code == 200
    products = response.json()
    assert [item["id"] for item in products] == [item.id for item in CatalogFactory.all()]
    mug = products[0]
    assert mug["name"] == CatalogFactory.MUG.name
    assert mug["price_cents"] == CatalogFactory.MUG.price_cents
    assert mug["price"] == "$12.00"
    assert mug["stock"] == 20


@allure.feature("Catalog")
@allure.story("Product detail")
@pytest.mark.regression
@pytest.mark.api
def test_get_product(api: httpx.Client) -> None:
    response = api.get(f"/api/products/{CatalogFactory.LAMP.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == CatalogFactory.LAMP.name
    assert body["price_cents"] == CatalogFactory.LAMP.price_cents


@allure.feature("Catalog")
@allure.story("Product detail")
@pytest.mark.regression
@pytest.mark.api
def test_unknown_product_is_not_found(api: httpx.Client) -> None:
    response = api.get("/api/products/not-on-the-shelf")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found."


@allure.feature("Catalog")
@allure.story("Contract")
@pytest.mark.regression
@pytest.mark.api
def test_openapi_lists_shop_routes(api: httpx.Client) -> None:
    response = api.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    for path in ("/api/login", "/api/products", "/api/cart", "/api/checkout"):
        assert path in paths

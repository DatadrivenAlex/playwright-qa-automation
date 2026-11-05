"""Test data for the accounts and catalog baked into the demo shop.

These factories describe the contract the tests expect. They do not read the
application source, so a renamed product or a changed price fails the suite.
"""

from __future__ import annotations

from qa_framework.settings import load_settings

DISPLAY_NAMES = {
    "alex": "Alexandru Cojocari",
    "guest": "Guest Shopper",
}


class UserFactory:
    def __init__(self, username: str, password: str, display_name: str) -> None:
        self.username = username
        self.password = password
        self.display_name = display_name

    def credentials(self) -> dict[str, str]:
        return {"username": self.username, "password": self.password}

    @classmethod
    def valid(cls) -> UserFactory:
        settings = load_settings()
        return cls(
            settings.demo_username,
            settings.demo_password,
            DISPLAY_NAMES.get(settings.demo_username, settings.demo_username),
        )

    @classmethod
    def second_customer(cls) -> UserFactory:
        return cls("guest", "demo123", "Guest Shopper")

    @classmethod
    def invalid_password(cls) -> dict[str, str]:
        user = cls.valid()
        return {"username": user.username, "password": "not-the-password"}

    @classmethod
    def unknown(cls) -> dict[str, str]:
        return {"username": "nobody", "password": "demo123"}


class ProductRef:
    def __init__(self, product_id: str, name: str, price_cents: int) -> None:
        self.id = product_id
        self.name = name
        self.price_cents = price_cents


class CatalogFactory:
    MUG = ProductRef("ceramic-mug", "Ceramic Mug", 1200)
    NOTEBOOK = ProductRef("linen-notebook", "Linen Notebook", 950)
    LAMP = ProductRef("desk-lamp", "Desk Lamp", 3400)
    THROW = ProductRef("wool-throw", "Wool Throw", 4800)
    KETTLE = ProductRef("pour-over-kettle", "Pour-over Kettle", 4200)
    COASTERS = ProductRef("oak-coasters", "Oak Coasters", 1600)

    @classmethod
    def all(cls) -> list[ProductRef]:
        return [cls.MUG, cls.NOTEBOOK, cls.LAMP, cls.THROW, cls.KETTLE, cls.COASTERS]


class CartFactory:
    @staticmethod
    def item(product: ProductRef | None = None, quantity: int = 1) -> dict[str, object]:
        chosen = product or CatalogFactory.MUG
        return {"product_id": chosen.id, "quantity": quantity}


class CheckoutFactory:
    @staticmethod
    def valid(**overrides: str) -> dict[str, str]:
        data = {
            "full_name": "Alexandru Cojocari",
            "email": "alex@example.com",
            "address": "14 Stefan cel Mare",
            "city": "Chisinau",
            "postal_code": "MD-2001",
        }
        data.update(overrides)
        return data

"""In-memory shop. Carts and orders belong to a session, so tests do not share state."""

from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, field

MAX_QUANTITY = 10

USERS: dict[str, dict[str, str]] = {
    "alex": {"password": "demo123", "display_name": "Alexandru Cojocari"},
    "guest": {"password": "demo123", "display_name": "Guest Shopper"},
}


class StoreError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def format_money(cents: int) -> str:
    return f"${cents // 100}.{cents % 100:02d}"


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    price_cents: int
    stock: int
    blurb: str

    @property
    def price(self) -> str:
        return format_money(self.price_cents)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "price_cents": self.price_cents,
            "price": format_money(self.price_cents),
            "stock": self.stock,
            "blurb": self.blurb,
        }


PRODUCTS: tuple[Product, ...] = (
    Product("ceramic-mug", "Ceramic Mug", 1200, 20, "Speckled stoneware, 300 ml."),
    Product("linen-notebook", "Linen Notebook", 950, 15, "Plain pages and a stitched spine."),
    Product("desk-lamp", "Desk Lamp", 3400, 8, "Warm light on a brass arm."),
    Product("wool-throw", "Wool Throw", 4800, 5, "Charcoal herringbone, light enough for a chair."),
    Product("pour-over-kettle", "Pour-over Kettle", 4200, 6, "Gooseneck, one litre."),
    Product("oak-coasters", "Oak Coasters", 1600, 12, "Set of four, oiled oak."),
)


@dataclass
class Order:
    id: str
    username: str
    items: list[dict[str, object]]
    total_cents: int
    full_name: str
    email: str
    address: str
    city: str
    postal_code: str
    status: str = "placed"

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "status": self.status,
            "total_cents": self.total_cents,
            "total": format_money(self.total_cents),
            "full_name": self.full_name,
            "email": self.email,
            "address": self.address,
            "city": self.city,
            "postal_code": self.postal_code,
            "items": self.items,
        }


@dataclass
class Session:
    token: str
    username: str
    display_name: str
    cart: dict[str, int] = field(default_factory=dict)
    order_ids: list[str] = field(default_factory=list)

    @property
    def item_count(self) -> int:
        return sum(self.cart.values())


class Store:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._products = {product.id: product for product in PRODUCTS}
        self._sessions: dict[str, Session] = {}
        self._orders: dict[str, Order] = {}
        self._next_order = 1000

    def product_list(self) -> list[Product]:
        return list(PRODUCTS)

    def get_product(self, product_id: str) -> Product | None:
        return self._products.get(product_id)

    def authenticate(self, username: str, password: str) -> Session | None:
        user = USERS.get(username)
        if user is None or not secrets.compare_digest(user["password"], password):
            return None
        session = Session(
            token=secrets.token_urlsafe(24),
            username=username,
            display_name=user["display_name"],
        )
        with self._lock:
            self._sessions[session.token] = session
        return session

    def get_session(self, token: str | None) -> Session | None:
        if not token:
            return None
        with self._lock:
            return self._sessions.get(token)

    def logout(self, token: str | None) -> None:
        if not token:
            return
        with self._lock:
            self._sessions.pop(token, None)

    def cart_view(self, session: Session) -> dict[str, object]:
        with self._lock:
            return self._cart_payload(session)

    def add_item(self, session: Session, product_id: str, quantity: int) -> dict[str, object]:
        self._check_quantity(quantity)
        product = self._require_product(product_id)
        with self._lock:
            new_quantity = session.cart.get(product_id, 0) + quantity
            if new_quantity > min(MAX_QUANTITY, product.stock):
                raise StoreError("Not enough stock for that quantity.", 409)
            session.cart[product_id] = new_quantity
            return self._cart_payload(session)

    def set_quantity(self, session: Session, product_id: str, quantity: int) -> dict[str, object]:
        self._check_quantity(quantity)
        product = self._require_product(product_id)
        with self._lock:
            if product_id not in session.cart:
                raise StoreError("That product is not in the cart.", 404)
            if quantity > min(MAX_QUANTITY, product.stock):
                raise StoreError("Not enough stock for that quantity.", 409)
            session.cart[product_id] = quantity
            return self._cart_payload(session)

    def remove_item(self, session: Session, product_id: str) -> dict[str, object]:
        self._require_product(product_id)
        with self._lock:
            session.cart.pop(product_id, None)
            return self._cart_payload(session)

    def place_order(self, session: Session, shipping: dict[str, str]) -> Order:
        with self._lock:
            if not session.cart:
                raise StoreError("Cart is empty.", 409)
            items: list[dict[str, object]] = []
            total = 0
            for product_id, quantity in session.cart.items():
                product = self._products[product_id]
                line_total = product.price_cents * quantity
                total += line_total
                items.append(
                    {
                        "product_id": product.id,
                        "name": product.name,
                        "quantity": quantity,
                        "unit_price_cents": product.price_cents,
                        "line_total_cents": line_total,
                        "line_total": format_money(line_total),
                    }
                )
            self._next_order += 1
            order = Order(
                id=f"HM-{self._next_order}",
                username=session.username,
                items=items,
                total_cents=total,
                full_name=shipping["full_name"].strip(),
                email=shipping["email"].strip(),
                address=shipping["address"].strip(),
                city=shipping["city"].strip(),
                postal_code=shipping["postal_code"].strip(),
            )
            self._orders[order.id] = order
            session.order_ids.append(order.id)
            session.cart.clear()
            return order

    def list_orders(self, session: Session) -> list[dict[str, object]]:
        with self._lock:
            return [self._orders[order_id].to_dict() for order_id in session.order_ids]

    def get_order(self, session: Session, order_id: str) -> Order | None:
        with self._lock:
            order = self._orders.get(order_id)
            if order is None or order.username != session.username:
                return None
            return order

    def _require_product(self, product_id: str) -> Product:
        product = self._products.get(product_id)
        if product is None:
            raise StoreError("Product not found.", 404)
        return product

    @staticmethod
    def _check_quantity(quantity: int) -> None:
        if quantity < 1 or quantity > MAX_QUANTITY:
            raise StoreError("Quantity must be between 1 and 10.", 422)

    def _cart_payload(self, session: Session) -> dict[str, object]:
        items: list[dict[str, object]] = []
        total = 0
        for product_id, quantity in session.cart.items():
            product = self._products[product_id]
            line_total = product.price_cents * quantity
            total += line_total
            items.append(
                {
                    "product_id": product.id,
                    "name": product.name,
                    "quantity": quantity,
                    "unit_price_cents": product.price_cents,
                    "unit_price": format_money(product.price_cents),
                    "line_total_cents": line_total,
                    "line_total": format_money(line_total),
                }
            )
        return {
            "items": items,
            "total_cents": total,
            "total": format_money(total),
            "item_count": sum(session.cart.values()),
        }

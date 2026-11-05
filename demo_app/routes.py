"""HTTP routes for the shop UI and the JSON API."""

from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import BaseModel

from demo_app.store import PRODUCTS, Session, Store, StoreError
from demo_app.validation import validate_checkout

router = APIRouter()
SESSION_COOKIE = "harbor_session"


class LoginBody(BaseModel):
    username: str
    password: str


class CartItemBody(BaseModel):
    product_id: str
    quantity: int


class QuantityBody(BaseModel):
    quantity: int


class CheckoutBody(BaseModel):
    full_name: str = ""
    email: str = ""
    address: str = ""
    city: str = ""
    postal_code: str = ""


def store_of(request: Request) -> Store:
    return request.app.state.store


def read_token(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        token = header[7:].strip()
        if token:
            return token
    return request.cookies.get(SESSION_COOKIE)


def current_session(request: Request) -> Session | None:
    return store_of(request).get_session(read_token(request))


def require_api_session(request: Request) -> Session:
    session = current_session(request)
    if session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session


def safe_next(value: str | None) -> str:
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return "/catalog"


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        path="/",
    )


def render(request: Request, name: str, status_code: int = 200, **context: object) -> Response:
    templates = request.app.state.templates
    session = current_session(request)
    cart_count = 0
    user = None
    if session is not None:
        cart_count = store_of(request).cart_view(session)["item_count"]
        user = {"username": session.username, "display_name": session.display_name}
    payload = {"user": user, "cart_count": cart_count, "title": "Harbor Market"}
    payload.update(context)
    return templates.TemplateResponse(
        request,
        name,
        payload,
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


def error_response(exc: StoreError) -> JSONResponse:
    return JSONResponse({"detail": exc.message}, status_code=exc.status_code)


def parse_quantity(raw: str) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise StoreError("Quantity must be between 1 and 10.", 422) from exc


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@router.get("/")
def root(request: Request) -> RedirectResponse:
    target = "/catalog" if current_session(request) else "/login"
    return RedirectResponse(target, status_code=303)


@router.get("/login")
def login_form(request: Request) -> Response:
    if current_session(request):
        return RedirectResponse("/catalog", status_code=303)
    return render(request, "login.html", title="Sign in", error=None, username="")


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    next: str = "",
) -> Response:
    if not username.strip() or not password:
        return render(
            request,
            "login.html",
            status_code=422,
            title="Sign in",
            error="Enter your username and password.",
            username=username,
        )
    session = store_of(request).authenticate(username.strip(), password)
    if session is None:
        return render(
            request,
            "login.html",
            status_code=401,
            title="Sign in",
            error="Those credentials do not match.",
            username=username,
        )
    target = safe_next(next or request.query_params.get("next"))
    response = RedirectResponse(target, status_code=303)
    set_session_cookie(response, session.token)
    return response


@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    store_of(request).logout(read_token(request))
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.get("/catalog")
def catalog(request: Request) -> Response:
    notice = request.query_params.get("notice")
    item = request.query_params.get("item", "")
    error_code = request.query_params.get("error")
    flash, flash_kind = _catalog_flash(notice, item, error_code)
    return render(
        request,
        "catalog.html",
        title="Catalog",
        products=PRODUCTS,
        flash=flash,
        flash_kind=flash_kind,
    )


@router.post("/cart/items")
def add_to_cart_form(
    request: Request,
    product_id: str = Form(...),
    quantity: str = Form("1"),
) -> Response:
    if current_session(request) is None:
        return RedirectResponse("/login?next=/catalog", status_code=303)
    session = current_session(request)
    assert session is not None
    try:
        store_of(request).add_item(session, product_id, parse_quantity(quantity))
    except StoreError as exc:
        return RedirectResponse(f"/catalog?error={_error_code(exc)}", status_code=303)
    product = store_of(request).get_product(product_id)
    item_name = quote(product.name if product else "item")
    return RedirectResponse(f"/catalog?notice=added&item={item_name}", status_code=303)


@router.get("/cart")
def cart_page(request: Request) -> Response:
    session = current_session(request)
    if session is None:
        return RedirectResponse("/login?next=/cart", status_code=303)
    flash, flash_kind = _cart_flash(
        request.query_params.get("notice"),
        request.query_params.get("error"),
    )
    return render(
        request,
        "cart.html",
        title="Cart",
        cart=store_of(request).cart_view(session),
        flash=flash,
        flash_kind=flash_kind,
    )


@router.post("/cart/items/{product_id}")
def update_cart_form(request: Request, product_id: str, quantity: str = Form("1")) -> Response:
    session = current_session(request)
    if session is None:
        return RedirectResponse("/login?next=/cart", status_code=303)
    try:
        store_of(request).set_quantity(session, product_id, parse_quantity(quantity))
    except StoreError as exc:
        return RedirectResponse(f"/cart?error={_error_code(exc)}", status_code=303)
    return RedirectResponse("/cart?notice=updated", status_code=303)


@router.post("/cart/items/{product_id}/delete")
def remove_cart_form(request: Request, product_id: str) -> Response:
    session = current_session(request)
    if session is None:
        return RedirectResponse("/login?next=/cart", status_code=303)
    try:
        store_of(request).remove_item(session, product_id)
    except StoreError as exc:
        return RedirectResponse(f"/cart?error={_error_code(exc)}", status_code=303)
    return RedirectResponse("/cart?notice=removed", status_code=303)


@router.get("/checkout")
def checkout_page(request: Request) -> Response:
    session = current_session(request)
    if session is None:
        return RedirectResponse("/login?next=/checkout", status_code=303)
    cart = store_of(request).cart_view(session)
    blocked = cart["item_count"] == 0
    return render(
        request,
        "checkout.html",
        status_code=409 if blocked else 200,
        title="Checkout",
        cart=cart,
        form=_empty_checkout(),
        errors={},
        blocked=blocked,
    )


@router.post("/checkout")
def checkout_submit(
    request: Request,
    full_name: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    city: str = Form(""),
    postal_code: str = Form(""),
) -> Response:
    session = current_session(request)
    if session is None:
        return RedirectResponse("/login?next=/checkout", status_code=303)
    form = {
        "full_name": full_name,
        "email": email,
        "address": address,
        "city": city,
        "postal_code": postal_code,
    }
    cart = store_of(request).cart_view(session)
    if cart["item_count"] == 0:
        return render(
            request,
            "checkout.html",
            status_code=409,
            title="Checkout",
            cart=cart,
            form=form,
            errors={},
            blocked=True,
        )
    errors = validate_checkout(form)
    if errors:
        return render(
            request,
            "checkout.html",
            status_code=422,
            title="Checkout",
            cart=cart,
            form=form,
            errors=errors,
            blocked=False,
        )
    order = store_of(request).place_order(session, form)
    return RedirectResponse(f"/orders/{order.id}", status_code=303)


@router.get("/orders/{order_id}")
def order_page(request: Request, order_id: str) -> Response:
    session = current_session(request)
    if session is None:
        return RedirectResponse(f"/login?next=/orders/{quote(order_id)}", status_code=303)
    order = store_of(request).get_order(session, order_id)
    return render(
        request,
        "order.html",
        status_code=200 if order else 404,
        title="Order" if order else "Order not found",
        order=order.to_dict() if order else None,
    )


@router.post("/api/login")
def api_login(request: Request, body: LoginBody) -> JSONResponse:
    if not body.username.strip() or not body.password:
        return JSONResponse({"detail": "Enter your username and password."}, status_code=422)
    session = store_of(request).authenticate(body.username.strip(), body.password)
    if session is None:
        return JSONResponse({"detail": "Those credentials do not match."}, status_code=401)
    response = JSONResponse(
        {
            "token": session.token,
            "username": session.username,
            "display_name": session.display_name,
        }
    )
    set_session_cookie(response, session.token)
    return response


@router.post("/api/logout")
def api_logout(request: Request) -> JSONResponse:
    store_of(request).logout(read_token(request))
    response = JSONResponse({"ok": True})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.get("/api/products")
def api_products() -> list[dict[str, object]]:
    return [product.to_dict() for product in PRODUCTS]


@router.get("/api/products/{product_id}")
def api_product(product_id: str, request: Request) -> dict[str, object]:
    product = store_of(request).get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product.to_dict()


@router.get("/api/cart")
def api_cart(request: Request) -> dict[str, object]:
    session = require_api_session(request)
    return store_of(request).cart_view(session)


@router.post("/api/cart/items")
def api_add_item(request: Request, body: CartItemBody) -> JSONResponse:
    session = require_api_session(request)
    try:
        cart = store_of(request).add_item(session, body.product_id, body.quantity)
    except StoreError as exc:
        return error_response(exc)
    return JSONResponse(cart)


@router.patch("/api/cart/items/{product_id}")
def api_update_item(request: Request, product_id: str, body: QuantityBody) -> JSONResponse:
    session = require_api_session(request)
    try:
        cart = store_of(request).set_quantity(session, product_id, body.quantity)
    except StoreError as exc:
        return error_response(exc)
    return JSONResponse(cart)


@router.delete("/api/cart/items/{product_id}")
def api_remove_item(request: Request, product_id: str) -> JSONResponse:
    session = require_api_session(request)
    try:
        cart = store_of(request).remove_item(session, product_id)
    except StoreError as exc:
        return error_response(exc)
    return JSONResponse(cart)


@router.post("/api/checkout")
def api_checkout(request: Request, body: CheckoutBody) -> JSONResponse:
    session = require_api_session(request)
    form = body.model_dump()
    errors = validate_checkout(form)
    if errors:
        return JSONResponse(
            {"detail": "Validation failed.", "errors": errors},
            status_code=422,
        )
    try:
        order = store_of(request).place_order(session, form)
    except StoreError as exc:
        return error_response(exc)
    return JSONResponse(order.to_dict(), status_code=201)


@router.get("/api/orders")
def api_orders(request: Request) -> list[dict[str, object]]:
    session = require_api_session(request)
    return store_of(request).list_orders(session)


@router.get("/api/orders/{order_id}")
def api_order(request: Request, order_id: str) -> dict[str, object]:
    session = require_api_session(request)
    order = store_of(request).get_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order.to_dict()


def _empty_checkout() -> dict[str, str]:
    return {
        "full_name": "",
        "email": "",
        "address": "",
        "city": "",
        "postal_code": "",
    }


def _error_code(exc: StoreError) -> str:
    if exc.status_code == 409:
        return "stock"
    if exc.status_code == 422:
        return "quantity"
    return "missing"


def _catalog_flash(
    notice: str | None,
    item: str,
    error_code: str | None,
) -> tuple[str | None, str | None]:
    if notice == "added" and item:
        return f"Added {item} to cart.", "ok"
    return _error_flash(error_code)


def _cart_flash(notice: str | None, error_code: str | None) -> tuple[str | None, str | None]:
    if notice == "updated":
        return "Cart updated.", "ok"
    if notice == "removed":
        return "Removed from cart.", "ok"
    return _error_flash(error_code)


def _error_flash(error_code: str | None) -> tuple[str | None, str | None]:
    messages = {
        "stock": "Not enough stock for that quantity.",
        "quantity": "Quantity must be between 1 and 10.",
        "missing": "Product not found.",
    }
    if error_code in messages:
        return messages[error_code], "err"
    return None, None

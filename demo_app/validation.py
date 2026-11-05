"""Shared checkout rules for the HTML form and the JSON API."""

from __future__ import annotations

import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

CHECKOUT_FIELDS = ("full_name", "email", "address", "city", "postal_code")


def validate_checkout(data: dict[str, str]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if len(data.get("full_name", "").strip()) < 2:
        errors["full_name"] = "Enter your full name."
    if not EMAIL_RE.fullmatch(data.get("email", "").strip()):
        errors["email"] = "Enter a valid email."
    if len(data.get("address", "").strip()) < 3:
        errors["address"] = "Enter a street address."
    if len(data.get("city", "").strip()) < 2:
        errors["city"] = "Enter a city."
    postal_code = data.get("postal_code", "").strip()
    if not 3 <= len(postal_code) <= 12:
        errors["postal_code"] = "Enter a postal code."
    return errors

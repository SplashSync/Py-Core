#
#  This file is part of SplashSync Project.
#
#  Copyright (C) Splash Sync  <www.splashsync.com>
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  For the full copyright and license information, please view the LICENSE
#  file that was distributed with this source code.
#

"""Price values (mirror of Php-Core ``PricesHelper``)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class Prices:
    """Encode, validate, compare and read Splash prices."""

    @staticmethod
    def encode(
        tax_excl: float | None,
        vat: float,
        tax_incl: float | None = None,
        code: str = "",
        symbol: str = "",
        name: str = "",
    ) -> dict[str, Any] | None:
        """Build a price from its tax excluded OR tax included amount.

        :return: the price, None when both or none amounts are given, VAT is negative or code is empty.
        """
        if (tax_excl is None) == (tax_incl is None) or vat < 0 or not code:
            return None
        price: dict[str, Any] = {"vat": vat, "code": code, "symbol": symbol, "name": name}
        if tax_excl is not None:
            price.update(base=0, ht=tax_excl, tax=tax_excl * vat / 100, ttc=tax_excl * (1 + vat / 100))
        elif tax_incl is not None:
            ht = tax_incl / (1 + vat / 100)
            price.update(base=1, ht=ht, tax=tax_incl - ht, ttc=tax_incl)
        return price

    @staticmethod
    def is_valid(price: Any) -> bool:
        """Check a (decoded) price structure."""
        if not isinstance(price, Mapping):
            return False
        if any(key not in price or price[key] is None for key in ("base", "ht", "ttc", "vat")):
            return False
        for key in ("ht", "ttc", "vat"):
            if price[key] not in ("", None) and Prices._number(price[key]) is None:
                return False
        return all(key in price for key in ("tax", "symbol", "code", "name"))

    @staticmethod
    def compare(price1: Any, price2: Any, precision: int = 6) -> bool:
        """Check if two prices are equal (base, amount, VAT and currency when both known)."""
        if not Prices.is_valid(price1) or not Prices.is_valid(price2):
            return False
        if Prices._truthy(price1["base"]) != Prices._truthy(price2["base"]):
            return False
        delta = float(f"1E-{precision}")
        amount = "ttc" if Prices._truthy(price1["base"]) else "ht"
        for key in (amount, "vat"):
            if abs((Prices._number(price1[key]) or 0) - (Prices._number(price2[key]) or 0)) > delta:
                return False
        if not price1.get("code") or not price2.get("code"):
            return True
        return bool(price1["code"] == price2["code"])

    @staticmethod
    def extract(price: Any, key: str = "ht") -> float | None:
        """Read one amount of a price."""
        if not isinstance(price, Mapping) or key not in price:
            return None
        return Prices._number(price[key])

    @staticmethod
    def _number(value: Any) -> float | None:
        """Convert a (decoded) value to a float."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _truthy(value: Any) -> bool:
        """PHP truthiness of a decoded value."""
        return value not in (None, "", "0", 0, False, 0.0)

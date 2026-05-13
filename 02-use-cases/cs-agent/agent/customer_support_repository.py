from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class LocalCustomerSupportRepository:
    def __init__(self, customers_path: Path, warranties_path: Path):
        self.customers_path = customers_path
        self.warranties_path = warranties_path

    def _read_json(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def list_customers(self) -> list[dict[str, Any]]:
        return self._read_json(self.customers_path)

    def list_warranties(self) -> list[dict[str, Any]]:
        return self._read_json(self.warranties_path)

    def find_customer(
        self,
        customer_id: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> dict[str, Any] | None:
        customers = self.list_customers()
        normalized_phone = normalize_phone(phone) if phone else None

        for customer in customers:
            if customer_id and customer["customer_id"] == customer_id.upper():
                return customer
            if email and customer["email"].lower() == email.lower():
                return customer
            if normalized_phone and normalize_phone(customer["phone"]) == normalized_phone:
                return customer
        return None

    def find_warranty(self, serial_number: str) -> dict[str, Any] | None:
        serial_number = serial_number.upper()
        for warranty in self.list_warranties():
            if warranty["serial_number"] == serial_number:
                return warranty
        return None


def normalize_phone(phone: str) -> str:
    return re.sub(r"[^\d+]", "", phone)

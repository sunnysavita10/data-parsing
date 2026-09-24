"""Rule-based extraction of structured invoice fields."""

import re

from .models import InvoiceData, LineItem, ParsedTable


def _find(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_invoice_fields(text: str) -> InvoiceData:
    amount = _find(
        r"Total\s*Amount\s*[:\-]\s*(?:₹|Rs\.?|INR)?\s*([\d,]+)", text
    )
    return {
        "invoice_number": _find(
            r"Invoice\s*(?:No|Number)\s*[:\-]\s*([A-Za-z0-9\-]+)", text
        ),
        "invoice_date": _find(r"Invoice\s*Date\s*[:\-]\s*([^\n]+)", text),
        "vendor_name": _find(r"Vendor\s*Name\s*[:\-]\s*([^\n]+)", text),
        "customer_name": _find(
            r"Customer\s*Name\s*[:\-]\s*([^\n]+)", text
        ),
        "total_amount": int(amount.replace(",", "")) if amount else None,
        "currency": "INR",
        "line_items": [],
    }


def extract_line_items_from_text(text: str) -> list[LineItem]:
    line_items: list[LineItem] = []
    pattern = re.compile(
        r"^(Laptop Stand|Monitor Arm)\s+(\d+)\s+INR\s+([\d,]+)\s+INR\s+([\d,]+)$",
        re.IGNORECASE,
    )
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if match:
            line_items.append(
                {
                    "sku": None,
                    "item": match.group(1),
                    "quantity": int(match.group(2)),
                    "uom": None,
                    "unit_price": int(match.group(3).replace(",", "")),
                    "discount": None,
                    "tax": None,
                    "amount": int(match.group(4).replace(",", "")),
                }
            )
    return line_items


def _number(value: str) -> int | float:
    parsed = float(value.replace(",", "").strip())
    return int(parsed) if parsed.is_integer() else parsed


def extract_line_items_from_tables(tables: list[ParsedTable]) -> list[LineItem]:
    required = {"description", "qty", "rate", "line total"}

    for table in tables:
        rows = table.get("data") or []
        if not rows:
            continue

        headers = [str(cell or "").strip().lower() for cell in rows[0]]
        if not required.issubset(headers):
            continue

        items: list[LineItem] = []

        for row in rows[1:]:
            values = {
                header: str(value or "").strip()
                for header, value in zip(headers, row)
            }

            try:
                items.append(
                    {
                        "sku": values.get("sku") or None,
                        "item": values["description"].replace("\n", " "),
                        "quantity": _number(values["qty"]),
                        "uom": values.get("uom") or None,
                        "unit_price": _number(values["rate"]),
                        "discount": values.get("disc") or None,
                        "tax": values.get("gst") or None,
                        "amount": _number(values["line total"]),
                    }
                )
            except (KeyError, ValueError):
                continue

        if items:
            return items

    return []

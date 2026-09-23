"""Shared data contracts for the invoice pipeline."""

from __future__ import annotations

from typing import Any, TypedDict


class ParsedPage(TypedDict):
    page_number: int
    text: str


class ParsedTable(TypedDict):
    page_number: int
    data: list[list[str | None]]


class ParsedDocument(TypedDict):
    pages: list[ParsedPage]
    tables: list[ParsedTable]
    metadata: dict[str, Any]


class LineItem(TypedDict):
    sku: str | None
    item: str
    quantity: int | float
    uom: str | None
    unit_price: int | float
    discount: str | None
    tax: str | None
    amount: int | float


class InvoiceData(TypedDict):
    invoice_number: str | None
    invoice_date: str | None
    vendor_name: str | None
    customer_name: str | None
    total_amount: int | None
    currency: str
    line_items: list[LineItem]


class PipelineResult(TypedDict):
    metadata: dict[str, Any]
    invoice: InvoiceData
    parsed_pages: list[ParsedPage]
    parsed_tables: list[ParsedTable]

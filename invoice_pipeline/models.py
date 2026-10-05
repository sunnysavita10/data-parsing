"""Pydantic models used by the invoice pipeline."""

from typing import Any

from pydantic import BaseModel, Field


class ParsedPage(BaseModel):
    page_number: int
    text: str


class ParsedTable(BaseModel):
    page_number: int
    data: list[list[Any]]


class ParsedDocument(BaseModel):
    pages: list[ParsedPage] = Field(default_factory=list)
    tables: list[ParsedTable] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LineItem(BaseModel):
    sku: str | None = None
    item: str
    quantity: int | float
    uom: str | None = None
    unit_price: int | float
    discount: str | None = None
    tax: str | None = None
    amount: int | float


class InvoiceData(BaseModel):
    invoice_number: str | None = None
    invoice_date: str | None = None
    vendor_name: str | None = None
    customer_name: str | None = None
    total_amount: int | float | None = None
    currency: str = "INR"
    line_items: list[LineItem] = Field(default_factory=list)


class PipelineResult(BaseModel):
    metadata: dict[str, Any]
    invoice: InvoiceData
    parsed_pages: list[ParsedPage] = Field(default_factory=list)
    parsed_tables: list[ParsedTable] = Field(default_factory=list)
    saved_output: dict[str, Any] | None = None

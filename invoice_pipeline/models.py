"""Simple Pydantic models used to validate invoice pipeline data."""

# Any is used when a value can have different data types.
from typing import Any

# BaseModel validates data when a model object is created.
# Field(default_factory=...) creates a new empty list or dictionary each time.
from pydantic import BaseModel, Field


class ParsedPage(BaseModel):
    """Stores the text extracted from one PDF page."""

    # Page position in the PDF, starting from 1.
    page_number: int

    # Raw or cleaned text extracted by PyMuPDF from this page.
    text: str


class ParsedTable(BaseModel):
    """Stores one table extracted by pdfplumber."""

    # PDF page on which the table was found.
    page_number: int

    # Table rows and cells. Cells may contain text, numbers, or empty values.
    data: list[list[Any]]


class ParsedDocument(BaseModel):
    """Groups all parsed pages, tables, and PDF metadata."""

    # All pages extracted from the PDF.
    pages: list[ParsedPage] = Field(default_factory=list)

    # All meaningful tables extracted from the PDF.
    tables: list[ParsedTable] = Field(default_factory=list)

    # PDF properties such as title, author, creator, and creation date.
    metadata: dict[str, Any] = Field(default_factory=dict)


class LineItem(BaseModel):
    """Stores one product or service row from the invoice."""

    # Product code. It is None when the invoice does not provide one.
    sku: str | None = None

    # Product or service description.
    item: str

    # Number of units. A decimal value is allowed when required.
    quantity: int | float

    # Unit of measurement, such as Nos, Kg, Hrs, or Lot.
    uom: str | None = None

    # Price of one unit before the final line calculation.
    unit_price: int | float

    # Discount shown on the line, such as 5%. It may be missing.
    discount: str | None = None

    # Tax shown on the line, such as 18% GST. It may be missing.
    tax: str | None = None

    # Final amount for this invoice line.
    amount: int | float


class InvoiceData(BaseModel):
    """Stores the main invoice fields and all extracted line items."""

    # Unique invoice number. It is None when extraction cannot find it.
    invoice_number: str | None = None

    # Invoice date exactly as extracted from the PDF.
    invoice_date: str | None = None

    # Name of the company that created the invoice.
    vendor_name: str | None = None

    # Name of the customer receiving the invoice.
    customer_name: str | None = None

    # Complete invoice amount. It is None when extraction cannot find it.
    total_amount: int | float | None = None

    # Currency used by the invoice. This project uses INR by default.
    currency: str = "INR"

    # Validated products or services extracted from invoice text or tables.
    line_items: list[LineItem] = Field(default_factory=list)


class PipelineResult(BaseModel):
    """Stores the complete result returned by the invoice pipeline."""

    # Source and storage details, such as document ID and storage location.
    metadata: dict[str, Any]

    # Validated invoice details and line items.
    invoice: InvoiceData

    # Page-wise text used by the Streamlit document-text tab.
    parsed_pages: list[ParsedPage] = Field(default_factory=list)

    # Extracted tables used by the Streamlit tables tab and CSV output.
    parsed_tables: list[ParsedTable] = Field(default_factory=list)

    # Paths of saved JSON and CSV files. It is None before output is saved.
    saved_output: dict[str, Any] | None = None

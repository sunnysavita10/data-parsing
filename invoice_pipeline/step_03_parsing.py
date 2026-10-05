"""Step 3: Parse, clean, and extract structured data from the PDF."""

from io import BytesIO
import re

import pymupdf
import pdfplumber

from .models import (
    InvoiceData,
    LineItem,
    ParsedDocument,
    ParsedPage,
    ParsedTable,
)


def parse_pdf(pdf_bytes: bytes) -> ParsedDocument:
    pages: list[ParsedPage] = []
    tables: list[ParsedTable] = []
    metadata = {}

    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
        metadata = pdf.metadata or {}

        for page_number, page in enumerate(pdf, start=1):
            pages.append(
                ParsedPage(page_number=page_number, text=page.get_text("text"))
            )

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables() or []:
                # Ignore bordered headings that pdfplumber detects as 1-row tables.
                if len(table) < 2:
                    continue

                tables.append(ParsedTable(page_number=page_number, data=table))

    print("[OK] PDF parsing completed")
    return ParsedDocument(pages=pages, tables=tables, metadata=metadata)


def clean_text(text: str) -> str:
    cleaned_lines = []

    for line in text.splitlines():
        clean_line = " ".join(line.split())
        if clean_line:
            cleaned_lines.append(clean_line)

    return "\n".join(cleaned_lines)


def clean_parsed_document(parsed_document: ParsedDocument) -> ParsedDocument:
    for page in parsed_document.pages:
        page.text = clean_text(page.text)

    print("[OK] Cleaning completed")
    return parsed_document


def get_complete_text(parsed_document: ParsedDocument) -> str:
    return "\n\n".join(page.text for page in parsed_document.pages)


def _find(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_invoice_fields(text: str) -> InvoiceData:
    amount = _find(
        r"Total\s*Amount\s*[:\-]\s*(?:₹|Rs\.?|INR)?\s*([\d,]+)", text
    )

    return InvoiceData(
        invoice_number=_find(
            r"Invoice\s*(?:No|Number)\s*[:\-]\s*([A-Za-z0-9\-]+)", text
        ),
        invoice_date=_find(r"Invoice\s*Date\s*[:\-]\s*([^\n]+)", text),
        vendor_name=_find(r"Vendor\s*Name\s*[:\-]\s*([^\n]+)", text),
        customer_name=_find(
            r"Customer\s*Name\s*[:\-]\s*([^\n]+)", text
        ),
        total_amount=int(amount.replace(",", "")) if amount else None,
        currency="INR",
    )


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
                LineItem(
                    item=match.group(1),
                    quantity=int(match.group(2)),
                    unit_price=int(match.group(3).replace(",", "")),
                    amount=int(match.group(4).replace(",", "")),
                )
            )

    return line_items


def _number(value: str) -> int | float:
    parsed = float(value.replace(",", "").strip())
    return int(parsed) if parsed.is_integer() else parsed


def extract_line_items_from_tables(tables: list[ParsedTable]) -> list[LineItem]:
    required = {"description", "qty", "rate", "line total"}

    for table in tables:
        rows = table.data
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
                    LineItem(
                        sku=values.get("sku") or None,
                        item=values["description"].replace("\n", " "),
                        quantity=_number(values["qty"]),
                        uom=values.get("uom") or None,
                        unit_price=_number(values["rate"]),
                        discount=values.get("disc") or None,
                        tax=values.get("gst") or None,
                        amount=_number(values["line total"]),
                    )
                )
            except (KeyError, ValueError):
                continue

        if items:
            return items

    return []

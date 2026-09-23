"""PDF parsing functions."""

from __future__ import annotations

import io

import fitz
import pdfplumber

from .models import ParsedDocument


def parse_pdf(pdf_bytes: bytes) -> ParsedDocument:
    """Extract page text, tables, and native PDF metadata."""
    parsed: ParsedDocument = {"pages": [], "tables": [], "metadata": {}}

    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        parsed["metadata"] = document.metadata or {}
        for page_number, page in enumerate(document, start=1):
            parsed["pages"].append(
                {"page_number": page_number, "text": page.get_text("text")}
            )

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as document:
        for page_number, page in enumerate(document.pages, start=1):
            for table in page.extract_tables() or []:
                parsed["tables"].append(
                    {"page_number": page_number, "data": table}
                )

    print("[OK] PDF parsing completed")
    return parsed

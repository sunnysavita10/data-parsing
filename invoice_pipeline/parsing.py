"""PDF parsing functions."""

from io import BytesIO

import fitz
import pdfplumber


def parse_pdf(pdf_bytes):
    parsed_document = {"pages": [], "tables": [], "metadata": {}}

    with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
        parsed_document["metadata"] = pdf.metadata or {}

        for page_number, page in enumerate(pdf, start=1):
            parsed_document["pages"].append(
                {"page_number": page_number, "text": page.get_text("text")}
            )

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables() or []:
                # Ignore bordered headings that pdfplumber detects as 1-row tables.
                if len(table) < 2:
                    continue

                parsed_document["tables"].append(
                    {"page_number": page_number, "data": table}
                )

    print("[OK] PDF parsing completed")
    return parsed_document

"""Text normalization for parsed PDF documents."""

from __future__ import annotations

import re

from .models import ParsedDocument


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(
        line.strip() for line in text.splitlines() if line.strip()
    )


def clean_parsed_document(parsed_document: ParsedDocument) -> ParsedDocument:
    """Normalize page text in place and return the document for composition."""
    for page in parsed_document["pages"]:
        page["text"] = clean_text(page["text"])
    print("[OK] Cleaning completed")
    return parsed_document


def get_complete_text(parsed_document: ParsedDocument) -> str:
    return "\n\n".join(page["text"] for page in parsed_document["pages"])

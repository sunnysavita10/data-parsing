"""Text normalization for parsed PDF documents."""

from .models import ParsedDocument


def clean_text(text: str) -> str:
    cleaned_lines = []

    for line in text.splitlines():
        clean_line = " ".join(line.split())
        if clean_line:
            cleaned_lines.append(clean_line)

    return "\n".join(cleaned_lines)


def clean_parsed_document(parsed_document: ParsedDocument) -> ParsedDocument:
    """Normalize page text in place and return the document for composition."""
    for page in parsed_document["pages"]:
        page["text"] = clean_text(page["text"])
    print("[OK] Cleaning completed")
    return parsed_document


def get_complete_text(parsed_document: ParsedDocument) -> str:
    return "\n\n".join(page["text"] for page in parsed_document["pages"])

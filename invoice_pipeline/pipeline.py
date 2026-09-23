"""End-to-end invoice workflow orchestration."""

from __future__ import annotations

import json

from .cleaning import clean_parsed_document, get_complete_text
from .config import Settings
from .extraction import (
    extract_invoice_fields,
    extract_line_items_from_tables,
    extract_line_items_from_text,
)
from .models import PipelineResult
from .parsing import parse_pdf
from .sources import DocumentSource, create_document_source
from .storage import DocumentStorage, create_document_storage


class InvoicePipeline:
    """Compose independently replaceable source, storage, and processing steps."""

    def __init__(
        self,
        settings: Settings,
        source: DocumentSource | None = None,
        storage: DocumentStorage | None = None,
    ) -> None:
        settings.validate()
        self.settings = settings
        self.source = source or create_document_source(settings)
        self.storage = storage or create_document_storage(settings)

    def run(self) -> PipelineResult:
        print("\n1. DATA SOURCE")
        print(
            f"Local Demo -> {self.settings.sample_pdf}"
            if self.settings.demo_mode
            else f"SharePoint -> {self.settings.sharepoint_file_path}"
        )

        print("\n2. DATA FETCHING")
        pdf_bytes = self.source.fetch()

        print("\n3. DATA INGESTION")
        metadata = self.storage.ingest(pdf_bytes)

        print("\n4. READ FILE FROM STORAGE")
        pdf_bytes = self.storage.read(pdf_bytes)

        print("\n5. DATA PARSING")
        parsed_document = parse_pdf(pdf_bytes)

        print("\n6. CLEANING / PREPROCESSING")
        clean_parsed_document(parsed_document)

        print("\n7. DATA EXTRACTION")
        complete_text = get_complete_text(parsed_document)
        invoice_data = extract_invoice_fields(complete_text)
        invoice_data["line_items"] = extract_line_items_from_tables(
            parsed_document["tables"]
        ) or extract_line_items_from_text(complete_text)

        result: PipelineResult = {
            "metadata": metadata,
            "invoice": invoice_data,
            "parsed_pages": parsed_document["pages"],
            "parsed_tables": parsed_document["tables"],
        }
        print("\n========== FINAL STRUCTURED OUTPUT ==========\n")
        print(json.dumps(invoice_data, indent=2, ensure_ascii=False))
        return result


def process_invoice(settings: Settings | None = None) -> PipelineResult:
    """Convenience entry point for scripts and notebooks."""
    return InvoicePipeline(settings or Settings.from_env()).run()

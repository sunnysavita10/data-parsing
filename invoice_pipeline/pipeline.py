"""End-to-end invoice workflow orchestration."""

import json

from .cleaning import clean_parsed_document, get_complete_text
from .config import Settings
from .extraction import (
    extract_invoice_fields,
    extract_line_items_from_tables,
    extract_line_items_from_text,
)
from .output import save_result
from .parsing import parse_pdf
from .sources import create_document_source
from .storage import create_document_storage


class InvoicePipeline:
    def __init__(self, settings, source=None, storage=None):
        settings.validate()
        self.settings = settings
        self.source = source or create_document_source(settings)
        self.storage = storage or create_document_storage(settings)

    def run(self):
        print("\n1. DATA SOURCE")
        source_name = (
            f"Local Demo -> {self.settings.sample_pdf}"
            if self.settings.demo_mode
            else f"SharePoint -> {self.settings.sharepoint_file_path}"
        )
        print(source_name)

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
        invoice = extract_invoice_fields(complete_text)
        invoice["line_items"] = extract_line_items_from_tables(
            parsed_document["tables"]
        ) or extract_line_items_from_text(complete_text)

        result = {
            "metadata": metadata,
            "invoice": invoice,
            "parsed_pages": parsed_document["pages"],
            "parsed_tables": parsed_document["tables"],
        }

        result["saved_output"] = save_result(result)

        print("\n========== FINAL STRUCTURED OUTPUT ==========\n")
        print(json.dumps(invoice, indent=2, ensure_ascii=False))
        return result


def process_invoice(settings=None):
    return InvoicePipeline(settings or Settings.from_env()).run()

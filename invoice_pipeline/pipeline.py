"""Run the complete invoice workflow in order."""

from .config import InvoiceConfig
from .models import PipelineResult
from .step_03_parsing import (
    clean_parsed_document,
    extract_invoice_fields,
    extract_line_items_from_tables,
    extract_line_items_from_text,
    get_complete_text,
    parse_pdf,
)
from .step_04_output import save_result
from .step_01_sources import create_document_source
from .step_02_storage import create_document_storage


class InvoicePipeline:
    def __init__(self, config, source=None, storage=None):
        self.config = config
        self.source = source or create_document_source(config)
        self.storage = storage or create_document_storage(config)

    def run(self):
        print("\n1. DATA SOURCE")
        print(getattr(self.source, "description", self.source.__class__.__name__))

        print("\n2. DATA FETCHING")
        pdf_bytes = self.source.fetch()

        print("\n3. DATA INGESTION")
        metadata = self.storage.ingest(pdf_bytes)

        print("\n4. READ FILE FROM STORAGE")
        pdf_bytes = self.storage.read()

        print("\n5. DATA PARSING")
        parsed_document = parse_pdf(pdf_bytes)

        print("\n6. CLEANING / PREPROCESSING")
        clean_parsed_document(parsed_document)

        print("\n7. DATA EXTRACTION")
        complete_text = get_complete_text(parsed_document)
        invoice = extract_invoice_fields(complete_text)
        invoice.line_items = extract_line_items_from_tables(
            parsed_document.tables
        ) or extract_line_items_from_text(complete_text)

        result = PipelineResult(
            metadata=metadata,
            invoice=invoice,
            parsed_pages=parsed_document.pages,
            parsed_tables=parsed_document.tables,
        )

        result.saved_output = save_result(result)

        print("\n========== FINAL STRUCTURED OUTPUT ==========\n")
        print(invoice.model_dump_json(indent=2))
        return result


def process_invoice(config=None):
    return InvoicePipeline(config or InvoiceConfig()).run()

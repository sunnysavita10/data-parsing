"""Connect all invoice-processing steps and run them in the correct order."""

# InvoiceConfig reads local, SharePoint, and S3 settings from the environment.
from .config import InvoiceConfig

# PipelineResult validates and stores the complete structured result.
from .models import PipelineResult

# These factory functions select the correct document source and storage type.
from .step_01_sources import create_document_source
from .step_02_storage import create_document_storage

# These functions parse the PDF, clean its text, and extract invoice data.
from .step_03_parsing import (
    clean_parsed_document,
    extract_invoice_fields,
    extract_line_items_from_tables,
    extract_line_items_from_text,
    get_complete_text,
    parse_pdf,
)

# save_result writes the structured result to JSON and CSV files.
from .step_04_output import save_result


class InvoicePipeline:
    """Runs the complete invoice workflow from source to saved output."""

    def __init__(self, config, source=None, storage=None):
        """Prepare the configuration, document source, and storage service."""

        # Store the configuration so every pipeline step uses the same settings.
        self.config = config

        # Use a supplied source when Streamlit uploads a file.
        # Otherwise, create the source from the environment configuration.
        self.source = source or create_document_source(config)

        # Use supplied storage for an upload, or select memory/S3 from config.
        self.storage = storage or create_document_storage(config)

    def run(self):
        """Run every processing step and return one PipelineResult object."""

        # Step 1: Show which source will provide the invoice PDF.
        print("\n1. DATA SOURCE")
        print(getattr(self.source, "description", self.source.__class__.__name__))

        # Step 2: Fetch PDF bytes from the demo file, upload, or SharePoint.
        print("\n2. DATA FETCHING")
        pdf_bytes = self.source.fetch()

        # Step 3: Store the fetched PDF in memory or Amazon S3.
        # The storage service also returns information about the document.
        print("\n3. DATA INGESTION")
        metadata = self.storage.ingest(pdf_bytes)

        # Step 4: Read the PDF back from the selected storage service.
        print("\n4. READ FILE FROM STORAGE")
        pdf_bytes = self.storage.read()

        # Step 5: Extract page text, PDF metadata, and tables.
        print("\n5. DATA PARSING")
        parsed_document = parse_pdf(pdf_bytes)

        # Step 6: Remove extra spaces and empty lines from extracted text.
        print("\n6. CLEANING / PREPROCESSING")
        clean_parsed_document(parsed_document)

        # Step 7: Join all page text and extract the main invoice fields.
        print("\n7. DATA EXTRACTION")
        complete_text = get_complete_text(parsed_document)
        invoice = extract_invoice_fields(complete_text)

        # First try to extract line items from tables.
        # Use text extraction as a fallback when no table items are found.
        invoice.line_items = extract_line_items_from_tables(
            parsed_document.tables
        ) or extract_line_items_from_text(complete_text)

        # Combine source metadata, invoice data, pages, and tables.
        # Pydantic validates these values while creating PipelineResult.
        result = PipelineResult(
            metadata=metadata,
            invoice=invoice,
            parsed_pages=parsed_document.pages,
            parsed_tables=parsed_document.tables,
        )

        # Save JSON and CSV files, then attach their paths to the result.
        result.saved_output = save_result(result)

        # Print readable invoice JSON in the terminal for debugging.
        print("\n========== FINAL STRUCTURED OUTPUT ==========\n")
        print(invoice.model_dump_json(indent=2))

        # Streamlit receives this object and displays its structured data.
        return result


def process_invoice(config=None):
    """Run the pipeline with supplied config or the default environment config."""

    return InvoicePipeline(config or InvoiceConfig()).run()

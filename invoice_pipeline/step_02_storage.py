"""Step 2: Temporarily keep the PDF in application memory."""


class MemoryStorage:
    def __init__(self, filename, source_name="Streamlit Upload"):
        self.filename = str(filename)
        self.source_name = source_name
        self.pdf_bytes = None

    def ingest(self, pdf_bytes):
        """Store the PDF bytes until the pipeline finishes."""
        self.pdf_bytes = pdf_bytes
        print("[OK] PDF stored temporarily in memory")

        return {
            "doc_id": "invoice_document",
            "original_source": self.source_name,
            "original_path": self.filename,
            "storage_path": "memory",
            "file_type": "pdf",
            "department": "finance",
            "status": "stored_in_memory",
        }

    def read(self):
        """Read the stored PDF bytes for parsing."""
        if self.pdf_bytes is None:
            raise ValueError("No PDF is available in memory")

        print("[OK] PDF read from memory")
        return self.pdf_bytes


def create_document_storage(config):
    if config.demo_mode:
        return MemoryStorage(config.sample_pdf, "Local Demo File")

    return MemoryStorage(config.sharepoint_file_path, "SharePoint")

"""Load invoice configuration from the .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


class InvoiceConfig:
    def __init__(self):
        self.demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
        self.sample_pdf = Path(os.getenv("SAMPLE_PDF", "sample_invoice.pdf"))

        self.tenant_id = os.getenv("TENANT_ID", "")
        self.client_id = os.getenv("CLIENT_ID", "")
        self.client_secret = os.getenv("CLIENT_SECRET", "")
        self.drive_id = os.getenv("DRIVE_ID", "")
        self.sharepoint_file_path = os.getenv(
            "SHAREPOINT_FILE_PATH", "Finance Documents/invoice_101.pdf"
        )

        self.s3_bucket_name = os.getenv("S3_BUCKET_NAME", "")
        self.s3_object_key = os.getenv(
            "S3_OBJECT_KEY", "invoices/invoice_101.pdf"
        )

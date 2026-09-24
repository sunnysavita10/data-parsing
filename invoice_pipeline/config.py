"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    demo_mode: bool = True
    sample_pdf: Path = Path("sample_invoice.pdf")
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    drive_id: str = ""
    sharepoint_file_path: str = "Finance Documents/invoice_101.pdf"
    s3_bucket: str = "company-rag-data"
    s3_key: str = "raw/invoices/invoice_101.pdf"
    metadata_key: str = "metadata/invoices/invoice_101.json"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        return cls(
            demo_mode=os.getenv("DEMO_MODE", "true").strip().lower()
            in {"true", "1", "yes", "on"},
            sample_pdf=Path(os.getenv("SAMPLE_PDF", "sample_invoice.pdf")),
            tenant_id=os.getenv("TENANT_ID", ""),
            client_id=os.getenv("CLIENT_ID", ""),
            client_secret=os.getenv("CLIENT_SECRET", ""),
            drive_id=os.getenv("DRIVE_ID", ""),
            sharepoint_file_path=os.getenv(
                "SHAREPOINT_FILE_PATH", "Finance Documents/invoice_101.pdf"
            ),
            s3_bucket=os.getenv("S3_BUCKET", "company-rag-data"),
            s3_key=os.getenv("S3_KEY", "raw/invoices/invoice_101.pdf"),
            metadata_key=os.getenv(
                "METADATA_KEY", "metadata/invoices/invoice_101.json"
            ),
        )

    def validate(self) -> None:
        if self.demo_mode:
            if not self.sample_pdf.is_file():
                raise FileNotFoundError(f"Demo PDF not found: {self.sample_pdf}")
            return

        required = {
            "TENANT_ID": self.tenant_id,
            "CLIENT_ID": self.client_id,
            "CLIENT_SECRET": self.client_secret,
            "DRIVE_ID": self.drive_id,
            "S3_BUCKET": self.s3_bucket,
            "S3_KEY": self.s3_key,
            "METADATA_KEY": self.metadata_key,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(
                "Missing production configuration: " + ", ".join(missing)
            )

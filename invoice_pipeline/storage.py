"""Raw-document storage adapters."""

from __future__ import annotations

import json
from typing import Any, Protocol

from .config import Settings


class DocumentStorage(Protocol):
    def ingest(self, pdf_bytes: bytes) -> dict[str, Any]: ...

    def read(self, existing_pdf_bytes: bytes | None = None) -> bytes: ...


def build_metadata(settings: Settings) -> dict[str, Any]:
    return {
        "doc_id": "doc_101",
        "original_source": (
            "Local Demo File" if settings.demo_mode else "SharePoint"
        ),
        "original_path": (
            str(settings.sample_pdf)
            if settings.demo_mode
            else settings.sharepoint_file_path
        ),
        "storage_path": (
            str(settings.sample_pdf)
            if settings.demo_mode
            else f"s3://{settings.s3_bucket}/{settings.s3_key}"
        ),
        "file_type": "pdf",
        "department": "finance",
        "status": "demo_loaded" if settings.demo_mode else "ingested",
    }


class LocalStorage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def ingest(self, pdf_bytes: bytes) -> dict[str, Any]:
        print("[OK] Demo Mode: S3 ingestion skipped")
        return build_metadata(self.settings)

    def read(self, existing_pdf_bytes: bytes | None = None) -> bytes:
        if existing_pdf_bytes is not None:
            print("[OK] Demo PDF bytes ready for parsing")
            return existing_pdf_bytes
        return self.settings.sample_pdf.read_bytes()


class MemoryStorage:
    """Pass uploaded bytes through without writing them to disk or cloud."""

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def ingest(self, pdf_bytes: bytes) -> dict[str, Any]:
        print("[OK] Uploaded PDF kept in memory")
        return {
            "doc_id": "uploaded_document",
            "original_source": "Streamlit Upload",
            "original_path": self.filename,
            "storage_path": "memory",
            "file_type": "pdf",
            "department": "unknown",
            "status": "uploaded",
        }

    def read(self, existing_pdf_bytes: bytes | None = None) -> bytes:
        if existing_pdf_bytes is None:
            raise ValueError("Uploaded PDF bytes are unavailable")
        print("[OK] Uploaded PDF bytes ready for parsing")
        return existing_pdf_bytes


class S3Storage:
    def __init__(self, settings: Settings, client: Any = None) -> None:
        self.settings = settings
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            import boto3

            self._client = boto3.client("s3")
        return self._client

    def ingest(self, pdf_bytes: bytes) -> dict[str, Any]:
        metadata = build_metadata(self.settings)
        self.client.put_object(
            Bucket=self.settings.s3_bucket,
            Key=self.settings.s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        self.client.put_object(
            Bucket=self.settings.s3_bucket,
            Key=self.settings.metadata_key,
            Body=json.dumps(metadata, indent=2),
            ContentType="application/json",
        )
        print(
            f"[OK] Raw PDF stored in "
            f"s3://{self.settings.s3_bucket}/{self.settings.s3_key}"
        )
        print(
            f"[OK] Metadata stored in "
            f"s3://{self.settings.s3_bucket}/{self.settings.metadata_key}"
        )
        return metadata

    def read(self, existing_pdf_bytes: bytes | None = None) -> bytes:
        response = self.client.get_object(
            Bucket=self.settings.s3_bucket,
            Key=self.settings.s3_key,
        )
        pdf_bytes = response["Body"].read()
        print("[OK] PDF loaded from S3")
        return pdf_bytes


def create_document_storage(settings: Settings) -> DocumentStorage:
    if settings.demo_mode:
        return LocalStorage(settings)
    return S3Storage(settings)

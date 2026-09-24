"""Raw-document storage adapters."""

import json

import boto3


def build_metadata(settings):
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
    def __init__(self, settings):
        self.settings = settings

    def ingest(self, pdf_bytes):
        print("[OK] Demo Mode: S3 ingestion skipped")
        return build_metadata(self.settings)

    def read(self, pdf_bytes=None):
        if pdf_bytes is not None:
            print("[OK] Demo PDF bytes ready for parsing")
            return pdf_bytes

        return self.settings.sample_pdf.read_bytes()


class MemoryStorage:
    def __init__(self, filename):
        self.filename = filename

    def ingest(self, pdf_bytes):
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

    def read(self, pdf_bytes=None):
        if pdf_bytes is None:
            raise ValueError("Uploaded PDF bytes are unavailable")

        print("[OK] Uploaded PDF bytes ready for parsing")
        return pdf_bytes


class S3Storage:
    def __init__(self, settings):
        self.settings = settings
        self.s3 = boto3.client("s3")

    def ingest(self, pdf_bytes):
        metadata = build_metadata(self.settings)

        self.s3.put_object(
            Bucket=self.settings.s3_bucket,
            Key=self.settings.s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        self.s3.put_object(
            Bucket=self.settings.s3_bucket,
            Key=self.settings.metadata_key,
            Body=json.dumps(metadata, indent=2),
            ContentType="application/json",
        )

        print(f"[OK] PDF stored in s3://{self.settings.s3_bucket}/{self.settings.s3_key}")
        print(f"[OK] Metadata stored in s3://{self.settings.s3_bucket}/{self.settings.metadata_key}")
        return metadata

    def read(self, pdf_bytes=None):
        response = self.s3.get_object(
            Bucket=self.settings.s3_bucket,
            Key=self.settings.s3_key,
        )

        print("[OK] PDF loaded from S3")
        return response["Body"].read()


def create_document_storage(settings):
    if settings.demo_mode:
        return LocalStorage(settings)

    return S3Storage(settings)

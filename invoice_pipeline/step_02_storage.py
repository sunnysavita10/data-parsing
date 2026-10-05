"""Step 2: Store the PDF in memory for demos or in S3 for production."""


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


class S3Storage:
    def __init__(self, bucket_name, object_key, original_path, s3_client=None):
        if not bucket_name:
            raise ValueError("S3_BUCKET_NAME is required when DEMO_MODE=false")

        if not object_key:
            raise ValueError("S3_OBJECT_KEY is required when DEMO_MODE=false")

        if s3_client is None:
            import boto3

            s3_client = boto3.client("s3")

        self.bucket_name = bucket_name
        self.object_key = object_key
        self.original_path = original_path
        self.s3_client = s3_client

    def ingest(self, pdf_bytes):
        """Upload the PDF to S3."""
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=self.object_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        print(f"[OK] PDF stored in S3: s3://{self.bucket_name}/{self.object_key}")

        return {
            "doc_id": self.object_key,
            "original_source": "SharePoint",
            "original_path": self.original_path,
            "storage_path": f"s3://{self.bucket_name}/{self.object_key}",
            "file_type": "pdf",
            "department": "finance",
            "status": "stored_in_s3",
        }

    def read(self):
        """Download the stored PDF from S3."""
        response = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=self.object_key,
        )
        pdf_bytes = response["Body"].read()
        print("[OK] PDF read from S3")
        return pdf_bytes


def create_document_storage(config):
    if config.demo_mode:
        return MemoryStorage(config.sample_pdf, "Local Demo File")

    return S3Storage(
        bucket_name=config.s3_bucket_name,
        object_key=config.s3_object_key,
        original_path=config.sharepoint_file_path,
    )

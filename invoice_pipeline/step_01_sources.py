"""Step 1: Read a PDF from local storage, upload, or SharePoint."""

from pathlib import Path
from urllib.parse import quote

import msal
import requests


class PdfSource:
    """Read a local PDF or return PDF bytes received from Streamlit."""

    def __init__(self, filename, pdf_bytes=None, source_name="Local Demo"):
        self.filename = str(filename)
        self.pdf_bytes = pdf_bytes
        self.description = f"{source_name} -> {filename}"

    def fetch(self):
        if self.pdf_bytes is not None:
            print(f"[OK] Uploaded file loaded: {self.filename}")
            return self.pdf_bytes

        pdf_bytes = Path(self.filename).read_bytes()
        print(f"[OK] Demo file loaded: {self.filename}")
        return pdf_bytes


class SharePointSource:
    def __init__(self, config):
        self.config = config
        self.description = f"SharePoint -> {config.sharepoint_file_path}"

    def get_access_token(self):
        app = msal.ConfidentialClientApplication(
            client_id=self.config.client_id,
            client_credential=self.config.client_secret,
            authority=f"https://login.microsoftonline.com/{self.config.tenant_id}",
        )

        token_response = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )

        if "access_token" not in token_response:
            error = token_response.get("error_description", token_response)
            raise RuntimeError(f"Unable to get Microsoft Graph token: {error}")

        return str(token_response["access_token"])

    def fetch(self):
        encoded_path = quote(self.config.sharepoint_file_path, safe="/")
        url = (
            "https://graph.microsoft.com/v1.0/"
            f"drives/{self.config.drive_id}/root:/{encoded_path}:/content"
        )

        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self.get_access_token()}"},
            timeout=60,
        )
        response.raise_for_status()

        print("[OK] File fetched from SharePoint")
        return response.content


def create_document_source(config):
    if config.demo_mode:
        return PdfSource(config.sample_pdf)

    return SharePointSource(config)

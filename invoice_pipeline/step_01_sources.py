"""Step 1: Read a PDF from local storage, upload, or SharePoint."""

from urllib.parse import quote

import msal
import requests


class LocalPdfSource:
    def __init__(self, config):
        self.config = config
        self.description = f"Local Demo -> {config.sample_pdf}"

    def fetch(self):
        pdf_bytes = self.config.sample_pdf.read_bytes()
        print(f"[OK] Demo file loaded: {self.config.sample_pdf}")
        return pdf_bytes


class BytesPdfSource:
    def __init__(self, pdf_bytes, filename):
        self.pdf_bytes = pdf_bytes
        self.filename = filename
        self.description = f"Streamlit Upload -> {filename}"

    def fetch(self):
        print(f"[OK] Uploaded file loaded: {self.filename}")
        return self.pdf_bytes


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
        return LocalPdfSource(config)

    return SharePointSource(config)

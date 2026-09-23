"""Document sources for local demo and Microsoft SharePoint."""

from __future__ import annotations

from typing import Protocol
from urllib.parse import quote

from .config import Settings


class DocumentSource(Protocol):
    """Anything capable of returning a document as bytes."""

    def fetch(self) -> bytes: ...


class LocalPdfSource:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch(self) -> bytes:
        pdf_bytes = self.settings.sample_pdf.read_bytes()
        print(f"[OK] Demo file loaded: {self.settings.sample_pdf}")
        return pdf_bytes


class BytesPdfSource:
    """A PDF already available in memory, such as a Streamlit upload."""

    def __init__(self, pdf_bytes: bytes, filename: str) -> None:
        self.pdf_bytes = pdf_bytes
        self.filename = filename

    def fetch(self) -> bytes:
        print(f"[OK] Uploaded file loaded: {self.filename}")
        return self.pdf_bytes


class SharePointSource:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _get_access_token(self) -> str:
        import msal

        app = msal.ConfidentialClientApplication(
            client_id=self.settings.client_id,
            client_credential=self.settings.client_secret,
            authority=(
                "https://login.microsoftonline.com/"
                f"{self.settings.tenant_id}"
            ),
        )
        token_response = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        if "access_token" not in token_response:
            error = token_response.get("error_description", token_response)
            raise RuntimeError(f"Unable to get Microsoft Graph token: {error}")
        return str(token_response["access_token"])

    def fetch(self) -> bytes:
        import requests

        encoded_path = quote(self.settings.sharepoint_file_path, safe="/")
        url = (
            "https://graph.microsoft.com/v1.0/"
            f"drives/{self.settings.drive_id}/root:/{encoded_path}:/content"
        )
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self._get_access_token()}"},
            timeout=60,
        )
        response.raise_for_status()
        print("[OK] File fetched from SharePoint")
        return response.content


def create_document_source(settings: Settings) -> DocumentSource:
    if settings.demo_mode:
        return LocalPdfSource(settings)
    return SharePointSource(settings)

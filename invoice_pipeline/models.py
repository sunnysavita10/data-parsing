"""Simple type names used by the invoice pipeline."""

from typing import Any


ParsedPage = dict[str, Any]
ParsedTable = dict[str, Any]
ParsedDocument = dict[str, Any]
LineItem = dict[str, Any]
InvoiceData = dict[str, Any]
PipelineResult = dict[str, Any]

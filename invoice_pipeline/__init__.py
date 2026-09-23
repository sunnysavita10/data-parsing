"""Reusable invoice ingestion and parsing pipeline.

The public pipeline objects are loaded lazily, so lightweight modules such as
configuration and extraction can be used without importing PDF dependencies.
"""

from typing import Any

from .config import Settings

__all__ = ["InvoicePipeline", "Settings", "process_invoice"]


def __getattr__(name: str) -> Any:
    if name in {"InvoicePipeline", "process_invoice"}:
        from .pipeline import InvoicePipeline, process_invoice

        return {
            "InvoicePipeline": InvoicePipeline,
            "process_invoice": process_invoice,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

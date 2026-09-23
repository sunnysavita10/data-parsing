"""Streamlit interface for the modular invoice parsing pipeline."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import streamlit as st

from invoice_pipeline import InvoicePipeline, Settings
from invoice_pipeline.sources import BytesPdfSource
from invoice_pipeline.storage import MemoryStorage


st.set_page_config(
    page_title="Invoice Parser",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(145deg, #07111f 0%, #0c1729 55%, #101b31 100%);
        color: #eef4ff;
    }
    [data-testid="stSidebar"] {
        background: #091426;
        border-right: 1px solid #263550;
    }
    .hero {
        padding: 1.5rem 1.7rem;
        border: 1px solid rgba(104, 181, 255, .22);
        border-radius: 20px;
        background: linear-gradient(120deg, rgba(28, 78, 121, .55), rgba(37, 37, 82, .45));
        box-shadow: 0 18px 50px rgba(0, 0, 0, .22);
        margin-bottom: 1rem;
    }
    .hero h1 { margin: 0; font-size: 2.15rem; color: #f7fbff; }
    .hero p { margin: .55rem 0 0; color: #bfd0e7; }
    .stage {
        border: 1px solid #263a59;
        background: rgba(13, 27, 48, .82);
        border-radius: 14px;
        padding: .85rem 1rem;
        color: #dceaff;
        min-height: 82px;
    }
    .stage strong { color: #73c8ff; }
    div[data-testid="stMetric"] {
        background: rgba(13, 27, 48, .86);
        border: 1px solid #263a59;
        border-radius: 14px;
        padding: 1rem;
    }
    div[data-testid="stFileUploader"] {
        border: 1px dashed #3c75a8;
        border-radius: 14px;
        padding: .4rem;
    }
    .stButton > button {
        width: 100%; border: 0; border-radius: 12px; font-weight: 700;
        background: linear-gradient(90deg, #1688e8, #7656df); color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_pipeline(source_mode: str, uploaded_file: Any) -> dict[str, Any]:
    # Both UI modes are local. Cloud mode remains available through the package.
    settings = replace(Settings.from_env(), demo_mode=True)
    if source_mode == "Upload PDF":
        if uploaded_file is None:
            raise ValueError("Please upload a PDF before running the pipeline.")
        pdf_bytes = uploaded_file.getvalue()
        if not pdf_bytes.startswith(b"%PDF"):
            raise ValueError("The uploaded file is not a valid PDF.")
        pipeline = InvoicePipeline(
            settings,
            source=BytesPdfSource(pdf_bytes, uploaded_file.name),
            storage=MemoryStorage(uploaded_file.name),
        )
        return pipeline.run()
    return InvoicePipeline(settings).run()


def show_overview(result: dict[str, Any]) -> None:
    invoice = result["invoice"]
    items = invoice.get("line_items", [])
    cols = st.columns(4)
    cols[0].metric("Invoice number", invoice.get("invoice_number") or "Not found")
    cols[1].metric("Total amount", f"INR {invoice.get('total_amount') or 0:,}")
    cols[2].metric("Line items", len(items))
    cols[3].metric("Pages parsed", len(result.get("parsed_pages", [])))

    left, right = st.columns(2)
    with left:
        st.subheader("Invoice details")
        st.json(
            {
                "invoice_number": invoice.get("invoice_number"),
                "invoice_date": invoice.get("invoice_date"),
                "vendor_name": invoice.get("vendor_name"),
                "customer_name": invoice.get("customer_name"),
                "total_amount": invoice.get("total_amount"),
                "currency": invoice.get("currency"),
            }
        )
    with right:
        st.subheader("Line items")
        if items:
            st.dataframe(items, width="stretch", hide_index=True)
        else:
            st.info("No matching line items were found.")


def show_document(result: dict[str, Any]) -> None:
    pages = result.get("parsed_pages", [])
    if not pages:
        st.info("No page text was extracted.")
        return
    page_labels = [f"Page {page['page_number']}" for page in pages]
    selected = st.selectbox("Choose a page", page_labels)
    page = pages[page_labels.index(selected)]
    st.text_area("Extracted text", page["text"], height=360)


def show_tables(result: dict[str, Any]) -> None:
    tables = result.get("parsed_tables", [])
    if not tables:
        st.info("No tables were detected in this PDF.")
        return
    for index, table in enumerate(tables, start=1):
        with st.expander(f"Table {index} · Page {table['page_number']}", expanded=index == 1):
            st.dataframe(table["data"], width="stretch")


with st.sidebar:
    st.title("Invoice Parser")
    st.caption("Modular PDF extraction workspace")
    source_mode = st.radio("Document source", ["Demo invoice", "Upload PDF"])
    uploaded_file = None
    if source_mode == "Upload PDF":
        uploaded_file = st.file_uploader(
            "Choose invoice", type=["pdf"], accept_multiple_files=False
        )
    else:
        st.info("Using `sample_invoice.pdf` from this project.")
    run_clicked = st.button("Run parsing pipeline", type="primary")
    st.divider()
    st.caption("PDF → Parse → Clean → Extract → Review")

st.markdown(
    """
    <section class="hero">
      <h1>Invoice Intelligence Workspace</h1>
      <p>Upload an invoice, run the modular parsing pipeline, and inspect every extracted result.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

stage_cols = st.columns(4)
for column, title, detail in zip(
    stage_cols,
    ["01 · Source", "02 · Parse", "03 · Clean", "04 · Extract"],
    ["Demo or upload", "Text and tables", "Normalize content", "Structured invoice"],
):
    column.markdown(
        f'<div class="stage"><strong>{title}</strong><br>{detail}</div>',
        unsafe_allow_html=True,
    )

if run_clicked:
    try:
        with st.spinner("Processing invoice through the pipeline..."):
            st.session_state["pipeline_result"] = run_pipeline(
                source_mode, uploaded_file
            )
        st.success("Invoice processed successfully.")
    except Exception as exc:
        st.session_state.pop("pipeline_result", None)
        st.error(str(exc))

result = st.session_state.get("pipeline_result")
if result:
    overview, document, tables, metadata = st.tabs(
        ["Overview", "Document text", "Detected tables", "Metadata & JSON"]
    )
    with overview:
        show_overview(result)
    with document:
        show_document(result)
    with tables:
        show_tables(result)
    with metadata:
        left, right = st.columns(2)
        with left:
            st.subheader("Document metadata")
            st.json(result["metadata"])
        with right:
            st.subheader("Download result")
            payload = json.dumps(result, indent=2, ensure_ascii=False)
            st.download_button(
                "Download structured JSON",
                data=payload,
                file_name="invoice_result.json",
                mime="application/json",
                width="stretch",
            )
            with st.expander("Preview complete JSON"):
                st.json(result)
else:
    st.info("Select a source and click **Run parsing pipeline** to begin.")

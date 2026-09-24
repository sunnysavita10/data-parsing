"""Streamlit interface for the invoice parsing pipeline."""

import json

import streamlit as st

from invoice_pipeline import InvoicePipeline, Settings
from invoice_pipeline.sources import BytesPdfSource
from invoice_pipeline.storage import MemoryStorage


st.set_page_config(page_title="Invoice Parser", page_icon="📄", layout="wide")


def run_pipeline(source_mode, uploaded_file):
    settings = Settings.from_env()
    settings.demo_mode = True

    if source_mode == "Upload PDF":
        if uploaded_file is None:
            raise ValueError("Please upload a PDF first.")

        pdf_bytes = uploaded_file.getvalue()
        if not pdf_bytes.startswith(b"%PDF"):
            raise ValueError("Please upload a valid PDF file.")

        source = BytesPdfSource(pdf_bytes, uploaded_file.name)
        storage = MemoryStorage(uploaded_file.name)
        return InvoicePipeline(settings, source, storage).run()

    return InvoicePipeline(settings).run()


st.title("📄 Invoice Intelligence Workspace")
st.write("Upload an invoice or use the demo PDF to extract structured data.")

with st.sidebar:
    st.header("Invoice Parser")
    source_mode = st.radio("Document source", ["Demo invoice", "Upload PDF"])

    uploaded_file = None
    if source_mode == "Upload PDF":
        uploaded_file = st.file_uploader("Choose a PDF", type="pdf")
    else:
        st.info("Using sample_invoice.pdf")

    run_clicked = st.button("Run parsing pipeline", type="primary")


if run_clicked:
    try:
        with st.spinner("Processing invoice..."):
            st.session_state["result"] = run_pipeline(source_mode, uploaded_file)
        st.success("Invoice processed successfully.")
    except Exception as error:
        st.session_state.pop("result", None)
        st.error(str(error))


result = st.session_state.get("result")

if not result:
    st.info("Select a document source and run the pipeline.")
else:
    invoice = result["invoice"]
    line_items = invoice["line_items"]

    st.success(f"Output saved in: `{result['saved_output']['folder']}`")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Invoice number", invoice.get("invoice_number") or "Not found")
    col2.metric("Total amount", f"INR {invoice.get('total_amount') or 0:,}")
    col3.metric("Line items", len(line_items))
    col4.metric("Pages", len(result["parsed_pages"]))

    overview_tab, text_tab, tables_tab, json_tab = st.tabs(
        ["Overview", "Document text", "Tables", "Metadata & JSON"]
    )

    with overview_tab:
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
            if line_items:
                st.dataframe(line_items, width="stretch", hide_index=True)
            else:
                st.info("No line items found.")

    with text_tab:
        pages = result["parsed_pages"]
        page_number = st.selectbox("Select page", range(1, len(pages) + 1))
        st.text_area("Extracted text", pages[page_number - 1]["text"], height=400)

    with tables_tab:
        tables = result["parsed_tables"]
        if not tables:
            st.info("No tables detected.")

        for number, table in enumerate(tables, start=1):
            title = f"Table {number} - Page {table['page_number']}"
            with st.expander(title, expanded=number == 1):
                st.dataframe(table["data"], width="stretch")

    with json_tab:
        st.subheader("Saved files")
        st.json(result["saved_output"])

        st.subheader("Document metadata")
        st.json(result["metadata"])

        json_data = json.dumps(result, indent=2, ensure_ascii=False)
        st.download_button(
            "Download structured JSON",
            data=json_data,
            file_name="invoice_result.json",
            mime="application/json",
        )

        with st.expander("Preview complete JSON"):
            st.json(result)

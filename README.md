# Invoice Data Parsing Pipeline

A modular, classroom-ready pipeline for:

**Document Source -> Fetching -> Optional Ingestion -> PDF Parsing -> Cleaning -> Structured Extraction -> Streamlit Review**

## Complete project flow

```mermaid
flowchart TD
    USER([User]) --> UI[Streamlit UI<br/>app.py]

    UI --> MODE{Document source}
    MODE -->|Demo invoice| LOCAL[LocalPdfSource<br/>sample_invoice.pdf]
    MODE -->|Uploaded PDF| UPLOAD[BytesPdfSource<br/>in-memory upload]

    INTEGRATION[Python integration] --> SETTINGS[Settings.from_env]
    SETTINGS --> ENV[.env configuration]
    SETTINGS --> CLOUD_MODE{DEMO_MODE}
    CLOUD_MODE -->|true| LOCAL
    CLOUD_MODE -->|false| SHAREPOINT[SharePointSource]

    SHAREPOINT --> GRAPH[Microsoft Graph API]
    GRAPH --> RAW[Raw PDF bytes]
    LOCAL --> RAW
    UPLOAD --> RAW

    RAW --> STORAGE{Storage adapter}
    STORAGE -->|Demo| LOCAL_STORE[LocalStorage<br/>pass-through]
    STORAGE -->|Upload| MEMORY[MemoryStorage<br/>no disk write]
    STORAGE -->|Production| S3[S3Storage<br/>PDF + metadata]

    LOCAL_STORE --> STORED[PDF bytes ready]
    MEMORY --> STORED
    S3 --> STORED

    STORED --> PARSER[parsing.py<br/>PyMuPDF + pdfplumber]
    PARSER --> PAGES[Page-wise text]
    PARSER --> TABLES[Detected tables]
    PARSER --> PDF_META[PDF metadata]

    PAGES --> CLEANER[cleaning.py<br/>whitespace normalization]
    CLEANER --> CLEAN_TEXT[Clean complete text]

    CLEAN_TEXT --> FIELD_EXTRACT[Regex field extraction]
    TABLES --> ITEM_EXTRACT[Table line-item extraction]

    FIELD_EXTRACT --> RESULT[PipelineResult]
    ITEM_EXTRACT --> RESULT
    PDF_META --> RESULT
    RESULT --> INVOICE[Invoice header fields]
    RESULT --> ITEMS[Structured line items]
    RESULT --> PARSED[Parsed pages and tables]
    RESULT --> META[Source metadata]

    RESULT --> OUTPUT[output/run folder]
    OUTPUT --> FULL_JSON[structured_data.json]
    OUTPUT --> TABLES_JSON[tables.json]
    OUTPUT --> TABLE_CSV[Individual table CSV files]

    INVOICE --> DASHBOARD[Streamlit result dashboard]
    ITEMS --> DASHBOARD
    PARSED --> DASHBOARD
    META --> DASHBOARD

    DASHBOARD --> OVERVIEW[Overview and metrics]
    DASHBOARD --> DOC_TAB[Document text]
    DASHBOARD --> TABLE_TAB[Detected tables]
    DASHBOARD --> JSON[JSON preview and download]
```

## Architecture by module

```mermaid
flowchart LR
    APP[app.py] --> PIPELINE[pipeline.py]
    PIPELINE --> CONFIG[config.py]
    PIPELINE --> SOURCES[sources.py]
    PIPELINE --> STORAGE[storage.py]
    PIPELINE --> PARSING[parsing.py]
    PIPELINE --> CLEANING[cleaning.py]
    PIPELINE --> EXTRACTION[extraction.py]

    PARSING --> MODELS[models.py]
    CLEANING --> MODELS
    EXTRACTION --> MODELS
    PIPELINE --> MODELS

    GENERATOR[scripts/generate_sample_invoice.py] --> SAMPLE[sample_invoice.pdf]
    SAMPLE --> SOURCES
```

## Processing sequence

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit UI
    participant P as InvoicePipeline
    participant S as DocumentSource
    participant ST as DocumentStorage
    participant PDF as PDF Parser
    participant C as Cleaner
    participant E as Extractor

    User->>UI: Select demo or upload PDF
    User->>UI: Click Run parsing pipeline
    UI->>P: run()
    P->>S: fetch()
    S-->>P: PDF bytes
    P->>ST: ingest(PDF bytes)
    ST-->>P: Source metadata
    P->>ST: read()
    ST-->>P: Stored PDF bytes
    P->>PDF: parse_pdf()
    PDF-->>P: Pages, tables, PDF metadata
    P->>C: clean_parsed_document()
    C-->>P: Cleaned page text
    P->>E: Extract header fields and line items
    E-->>P: Structured invoice data
    P-->>UI: PipelineResult
    UI-->>User: Metrics, tables, text and JSON download
```

## Project structure

```text
data-parsing/
|-- app.py                              # Streamlit interface
|-- sample_invoice.pdf                  # five-page synthetic invoice
|-- requirements.txt                    # Python dependencies
|-- output/                             # generated JSON and table CSV files
|-- .env                                # local configuration and secrets
|-- .env.example                        # safe configuration template
|-- invoice_pipeline/
|   |-- __init__.py                     # public package exports
|   |-- config.py                       # environment settings and validation
|   |-- sources.py                      # local, upload and SharePoint sources
|   |-- storage.py                      # memory, local and S3 storage
|   |-- parsing.py                      # PDF text, table and metadata parsing
|   |-- cleaning.py                     # text preprocessing
|   |-- extraction.py                   # invoice fields and line items
|   |-- models.py                       # shared typed data contracts
|   `-- pipeline.py                     # end-to-end orchestration
`-- scripts/
    `-- generate_sample_invoice.py      # reproducible sample generator
```

Each stage has one responsibility. Source and storage protocols make it possible
to replace infrastructure without modifying parsing, cleaning, or extraction.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The Streamlit UI supports:

- The bundled five-page demo invoice
- PDF upload processed entirely in memory
- Invoice overview and key metrics
- Structured line-item table
- Extracted page text and detected tables
- Metadata inspection and JSON download
- Automatic structured JSON and table CSV persistence

## Saved output

Every successful pipeline run creates a timestamped folder:

```text
output/
`-- INV-2026-1048_YYYYMMDD_HHMMSS_microseconds/
    |-- structured_data.json
    |-- tables.json
    `-- tables/
        |-- table_01_page_1.csv
        |-- table_02_page_1.csv
        `-- ...
```

`structured_data.json` contains metadata, invoice fields, line items, parsed
page text, detected tables, and saved-file paths. `tables.json` contains all
tables together, while the `tables` directory contains one CSV per table.

## Configuration

Local UI usage works with:

```dotenv
DEMO_MODE=true
SAMPLE_PDF=sample_invoice.pdf
```

For SharePoint and S3 processing, populate the Microsoft Entra ID, SharePoint,
AWS, and S3 values in `.env`, set `DEMO_MODE=false`, and initialize
`InvoicePipeline` from a Python integration.

Secrets stay in `.env`, which is excluded through `.gitignore`. Only
`.env.example` should be committed.

## Sample document coverage

The bundled invoice contains five pages of synthetic enterprise data:

- Supplier and customer identity, addresses, GSTIN and PAN
- Purchase order, contract, challan and e-invoice references
- Ten products and services with SKU, quantity, UOM, rate and discount
- HSN/SAC-wise CGST and SGST reconciliation
- Shipping, GRN, delivery and installation events
- Payment milestones and masked remittance information
- Commercial terms, approvals, compliance controls and audit metadata

Regenerate it when needed:

```powershell
python scripts/generate_sample_invoice.py
```

## Teaching scope

The project intentionally stops at structured extracted data. Chunking,
embeddings, vector search and downstream LLM processing are not implemented.

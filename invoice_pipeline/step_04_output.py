"""Step 4: Save parsed invoice results as JSON and CSV files."""

import csv
import json
import re
from datetime import datetime
from pathlib import Path

from .models import PipelineResult


def save_result(result: PipelineResult, output_folder="output") -> dict:
    invoice_number = result.invoice.invoice_number or "invoice"
    safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", invoice_number)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    run_folder = Path(output_folder) / f"{safe_name}_{timestamp}"
    tables_folder = run_folder / "tables"
    tables_folder.mkdir(parents=True, exist_ok=True)

    table_files = []

    for number, table in enumerate(result.parsed_tables, start=1):
        filename = f"table_{number:02d}_page_{table.page_number}.csv"
        filepath = tables_folder / filename

        with filepath.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerows(table.data)

        table_files.append(str(filepath))

    tables_json = run_folder / "tables.json"
    tables_json.write_text(
        json.dumps(
            [table.model_dump(mode="json") for table in result.parsed_tables],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    output_info = {
        "folder": str(run_folder),
        "structured_json": str(run_folder / "structured_data.json"),
        "tables_json": str(tables_json),
        "table_csv_files": table_files,
    }

    complete_result = result.model_copy(update={"saved_output": output_info})
    Path(output_info["structured_json"]).write_text(
        complete_result.model_dump_json(indent=2),
        encoding="utf-8",
    )

    print(f"[OK] Output saved in: {run_folder}")
    return output_info

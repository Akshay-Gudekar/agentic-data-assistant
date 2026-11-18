from pathlib import Path
import json
import sqlite3
from typing import Any

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".db", ".sqlite", ".sqlite3"}


def load_dataframe(path: str) -> pd.DataFrame:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Dataset not found: {source}")
    if source.suffix.lower() == ".csv":
        return pd.read_csv(source)
    if source.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(source)
    if source.suffix.lower() == ".json":
        return pd.read_json(source)
    if source.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        with sqlite3.connect(source) as connection:
            tables = pd.read_sql_query(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
                connection,
            )
            if tables.empty:
                raise ValueError(f"No tables found in SQLite database: {source}")
            table = tables.iloc[0]["name"]
            return pd.read_sql_query(f'SELECT * FROM "{table}"', connection)
    raise ValueError(
        f"Unsupported dataset type '{source.suffix}'. "
        f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )


def dataset_metadata(path: str, sample_size: int = 5) -> dict[str, Any]:
    frame = load_dataframe(path)
    return {
        "columns": list(frame.columns),
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "row_count": len(frame),
        "sample_rows": frame.head(sample_size).to_dict(orient="records"),
    }


def sample_rows_text(path: str, sample_size: int = 5) -> str:
    return json.dumps(dataset_metadata(path, sample_size)["sample_rows"], default=str)

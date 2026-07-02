"""ADK tool wrappers for dataset parsing and quality checks."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from services.dataset_store import get_current_dataset, require_dataframe, set_current_dataset
from utils.data_quality import detect_anomalies, evaluate_dataset_quality


def parse_uploaded_dataset(filename: str, username: str = "agent") -> str:
    """Parse a CSV or Excel file already saved in the project's uploads folder.

    Args:
        filename: Upload filename, not an arbitrary filesystem path.
        username: User associated with the active dataset context.

    Returns:
        JSON string with parsed shape, columns, and filename.
    """
    uploads_dir = (Path(__file__).resolve().parents[1] / "uploads").resolve()
    safe_name = Path(filename).name
    file_path = (uploads_dir / safe_name).resolve()
    if file_path.parent != uploads_dir or not file_path.is_file():
        return json.dumps({"error": f"Uploaded file not found: {safe_name}"})

    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(file_path)
    elif suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(file_path)
    else:
        return json.dumps({"error": "Only CSV and Excel uploads are supported."})

    if df.empty:
        return json.dumps({"error": "The uploaded dataset contains no rows."})

    df.columns = [str(column).strip() or f"column_{index + 1}" for index, column in enumerate(df.columns)]
    set_current_dataset(df, safe_name, username)
    return json.dumps(
        {
            "filename": safe_name,
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "column_names": df.columns.tolist(),
            "status": "loaded",
        },
        indent=2,
    )


def get_dataset_overview() -> str:
    """Return high-level metadata for the currently loaded business dataset.

    Returns:
        JSON string with filename, shape, columns, and quality grade.
    """
    ctx = get_current_dataset()
    if ctx.df is None:
        return json.dumps({"error": "No dataset loaded."})

    quality = evaluate_dataset_quality(ctx.df)
    payload = {
        "filename": ctx.filename,
        "rows": int(ctx.df.shape[0]),
        "columns": int(ctx.df.shape[1]),
        "column_names": ctx.df.columns.tolist(),
        "quality_score": quality["score"],
        "quality_grade": quality["grade"],
        "issues": quality["issues"],
    }
    return json.dumps(payload, indent=2)


def evaluate_data_quality() -> str:
    """Score the active dataset for missing values, duplicates, and KPI readiness.

    Returns:
        JSON string with score, grade, and issue list.
    """
    df, filename = require_dataframe()
    report = evaluate_dataset_quality(df)
    report["filename"] = filename
    return json.dumps(report, indent=2)


def detect_anomaly_records(max_rows: int = 20) -> str:
    """Detect unusual numeric rows in the active dataset using Isolation Forest.

    Args:
        max_rows: Maximum number of anomalous rows to return.

    Returns:
        JSON string with anomaly count and sample rows.
    """
    df, filename = require_dataframe()
    anomalies, error = detect_anomalies(df, max_rows=max_rows)
    payload = {
        "filename": filename,
        "anomaly_count": int(len(anomalies)),
        "message": error or "Anomaly scan completed.",
        "sample_rows": anomalies.head(max_rows).to_dict(orient="records") if not anomalies.empty else [],
    }
    return json.dumps(payload, indent=2, default=str)

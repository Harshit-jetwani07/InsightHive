"""ADK tool wrappers for analytics and forecasting."""

from __future__ import annotations

import json

from services.dataset_store import require_dataframe
from utils.data_analyzer import DataAnalyzer
from utils.forecaster import Forecaster


def get_summary_statistics() -> str:
    """Compute descriptive statistics for numeric columns in the active dataset.

    Returns:
        JSON string with summary stats and column metadata.
    """
    df, filename = require_dataframe()
    analyzer = DataAnalyzer(df)
    stats = analyzer.get_summary_stats()
    payload = {
        "filename": filename,
        "numeric_columns": analyzer.get_numeric_columns(),
        "categorical_columns": analyzer.get_categorical_columns(),
        "date_columns": [str(c) for c in analyzer.get_date_columns()],
        "summary_stats": stats.round(2).to_dict() if not stats.empty else {},
        "text_summary": analyzer.get_text_summary(),
    }
    return json.dumps(payload, indent=2, default=str)


def get_correlation_insights() -> str:
    """Return correlation matrix highlights for numeric KPI columns.

    Returns:
        JSON string with top positive and negative correlations.
    """
    df, filename = require_dataframe()
    analyzer = DataAnalyzer(df)
    corr = analyzer.get_correlation()
    if corr.empty:
        return json.dumps({"filename": filename, "message": "Not enough numeric columns for correlation."})

    pairs = []
    cols = corr.columns.tolist()
    for i, col_a in enumerate(cols):
        for col_b in cols[i + 1 :]:
            value = corr.loc[col_a, col_b]
            if value == value:
                pairs.append({"feature_a": col_a, "feature_b": col_b, "correlation": round(float(value), 3)})

    pairs.sort(key=lambda item: abs(item["correlation"]), reverse=True)
    payload = {
        "filename": filename,
        "top_correlations": pairs[:8],
        "matrix": corr.round(3).to_dict(),
    }
    return json.dumps(payload, indent=2, default=str)


def run_forecast(date_col: str, value_col: str, periods: int = 12) -> str:
    """Forecast a numeric KPI over time using the active dataset.

    Args:
        date_col: Date or period column name.
        value_col: Numeric KPI column to forecast.
        periods: Number of future periods to project.

    Returns:
        JSON string with MAE, RMSE, trend direction, and forecast summary.
    """
    df, filename = require_dataframe()
    forecaster = Forecaster(df, date_col, value_col)
    _, metrics = forecaster.forecast(periods)
    if metrics.get("error"):
        return json.dumps({"filename": filename, "error": metrics["error"]})

    payload = {
        "filename": filename,
        "date_col": date_col,
        "value_col": value_col,
        "periods": periods,
        "mae": metrics.get("mae"),
        "rmse": metrics.get("rmse"),
        "trend": metrics.get("trend"),
        "historical_points": metrics.get("historical_points", []),
        "forecast_points": metrics.get("forecast_points", []),
    }
    return json.dumps(payload, indent=2, default=str)

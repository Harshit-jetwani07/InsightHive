"""Shared in-process dataset context for ADK tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

import pandas as pd


@dataclass
class DatasetContext:
    df: Optional[pd.DataFrame] = None
    filename: str = ""
    username: str = ""
    dataset_id: Optional[int] = None


_lock = Lock()
_context = DatasetContext()


def set_current_dataset(
    df: pd.DataFrame,
    filename: str,
    username: str,
    dataset_id: Optional[int] = None,
) -> None:
    with _lock:
        _context.df = df.copy()
        _context.filename = filename
        _context.username = username
        _context.dataset_id = dataset_id


def clear_current_dataset() -> None:
    with _lock:
        _context.df = None
        _context.filename = ""
        _context.username = ""
        _context.dataset_id = None


def get_current_dataset() -> DatasetContext:
    with _lock:
        return DatasetContext(
            df=_context.df.copy() if _context.df is not None else None,
            filename=_context.filename,
            username=_context.username,
            dataset_id=_context.dataset_id,
        )


def require_dataframe() -> tuple[pd.DataFrame, str]:
    ctx = get_current_dataset()
    if ctx.df is None or ctx.df.empty:
        raise ValueError(
            "No dataset is loaded in the active session. Upload or load sample data first."
        )
    return ctx.df, ctx.filename

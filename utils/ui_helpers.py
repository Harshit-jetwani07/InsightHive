"""Streamlit UI fallbacks for Windows environments that block PyArrow DLLs."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def safe_dataframe(data, **kwargs) -> None:
    """Render an interactive table, falling back to dependency-free HTML."""
    try:
        st.dataframe(data, **kwargs)
        return
    except (ImportError, OSError):
        pass

    frame = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    if frame.empty:
        st.info("No records available.")
        return

    max_rows = min(len(frame), 100)
    st.caption(
        f"Compatibility table mode: showing {max_rows:,} of {len(frame):,} rows "
        "(PyArrow is blocked by Windows Application Control)."
    )
    html_table = frame.head(max_rows).to_html(
        index=not bool(kwargs.get("hide_index", False)),
        border=0,
        escape=True,
        classes="safe-dataframe",
    )
    st.markdown(
        """
        <style>
        .safe-dataframe {width:100%; border-collapse:collapse; font-size:0.82rem;}
        .safe-dataframe th,.safe-dataframe td {
            border:1px solid #2a2a5a; padding:6px 8px; text-align:left;
        }
        .safe-dataframe th {background:#191933; color:#b8adff;}
        .safe-dataframe tr:nth-child(even) {background:#101022;}
        </style>
        """ + html_table,
        unsafe_allow_html=True,
    )

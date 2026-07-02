"""Output validators for grounded business narratives."""

from __future__ import annotations

import json
import re

import numpy as np

from services.dataset_store import require_dataframe


def validate_numeric_grounding(text: str, relative_tolerance: float = 0.02) -> str:
    """Check whether numeric claims can be found in the active dataset or its summary.

    Args:
        text: Draft narrative containing numeric claims.
        relative_tolerance: Allowed relative difference when matching a claim.

    Returns:
        JSON with supported and unsupported numeric claims.
    """
    df, filename = require_dataframe()
    claims = [
        float(value.replace(",", ""))
        for value in re.findall(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?", text or "")
    ]
    numeric = df.select_dtypes(include=[np.number])
    evidence: list[float] = []
    if not numeric.empty:
        evidence.extend(numeric.to_numpy().ravel().tolist())
        description = numeric.describe()
        evidence.extend(description.to_numpy().ravel().tolist())
    evidence = [float(value) for value in evidence if np.isfinite(value)]

    supported, unsupported = [], []
    for claim in claims:
        tolerance = max(abs(claim) * relative_tolerance, 0.01)
        target = supported if any(abs(claim - value) <= tolerance for value in evidence) else unsupported
        target.append(claim)

    return json.dumps(
        {
            "filename": filename,
            "claim_count": len(claims),
            "supported_claims": supported,
            "unsupported_claims": unsupported,
            "grounding_rate": round(100 * len(supported) / max(len(claims), 1), 1),
            "valid": not unsupported,
        },
        indent=2,
    )

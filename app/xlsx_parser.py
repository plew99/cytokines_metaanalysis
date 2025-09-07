from __future__ import annotations

"""Utilities for parsing the project's primary XLSX data file.

The workbook contains a single sheet named ``Arkusz1`` with 49 columns.
This module exposes :func:`load_metaanalysis_xlsx` which loads the file
and returns a list of dictionaries with properly typed values.

Parsing rules implemented according to the specification provided:

* Leading/trailing whitespace in header names is stripped.
* Empty strings/``NaN`` values are normalised to ``None``.
* Yes/No fields are converted to booleans.
"""

from pathlib import Path
from typing import Any, Iterable

import pandas as pd

# ---------------------------------------------------------------------------
# Column metadata
# ---------------------------------------------------------------------------

# Columns that should be interpreted as integers
INT_FIELDS: set[str] = {
    "Year",
    "n",
    "NYHA Scale",
}

# Columns that should be interpreted as floats
FLOAT_FIELDS: set[str] = {
    "Age (mean / median)",
    "Age (SD / IQR)",
    "% Males",
    "Cytokine contrentration mean / median",
    "Cytokine concentration SD / IQR",
    "LVEF %",
    "CRP",
    "NT-proBNP",
    "cTnT",
    "cTnI",
    "Follow-up time (months)",
}

# Columns that should be mapped from Yes/No to boolean values
BOOL_FIELDS: set[str] = {
    "Inflammation excluded by EMB",
    "CAD excluded",
    "EMB performed?",
    "cMRI performed",
}

BOOL_MAP = {"yes": True, "no": False}


def _normalise_empty(frame: pd.DataFrame) -> pd.DataFrame:
    """Replace empty strings with ``pd.NA`` for uniform processing."""

    return frame.replace({"": pd.NA})


def _coerce_dtypes(frame: pd.DataFrame) -> pd.DataFrame:
    """Coerce columns to their target dtypes as defined above."""

    for col in BOOL_FIELDS:
        if col in frame.columns:
            frame[col] = (
                frame[col]
                .astype(str)
                .str.strip()
                .str.lower()
                .map(BOOL_MAP)
            )
    for col in INT_FIELDS:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").astype("Int64")
    for col in FLOAT_FIELDS:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").astype(float)
    return frame


def _replace_nan_with_none(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert any ``NaN`` values in records into ``None``."""

    cleaned: list[dict[str, Any]] = []
    for rec in records:
        row: dict[str, Any] = {}
        for key, value in rec.items():
            if isinstance(value, pd._libs.missing.NAType) or pd.isna(value):
                row[key] = None
            else:
                row[key] = value
        cleaned.append(row)
    return cleaned


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_metaanalysis_xlsx(path: str | Path) -> list[dict[str, Any]]:
    """Load the given XLSX file and return a list of row dictionaries.

    Parameters
    ----------
    path:
        Path to the workbook. Only the ``Arkusz1`` sheet is processed.

    Returns
    -------
    list[dict[str, Any]]
        A list of dictionaries with columns mapped to Python native types.
    """

    sheet_name = "Arkusz1"
    frame = pd.read_excel(path, sheet_name=sheet_name, header=0)
    # Normalise header names by stripping whitespace
    frame.columns = [c.strip() for c in frame.columns]
    frame = _normalise_empty(frame)
    frame = _coerce_dtypes(frame)
    # Convert to list of dictionaries and replace NaN with None
    records = frame.to_dict(orient="records")
    return _replace_nan_with_none(records)

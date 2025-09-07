"""Utilities for parsing the project's primary XLSX data file.

from __future__ import annotations

The workbook contains a single sheet named ``Arkusz1`` with 49 columns.
This module exposes :func:`load_metaanalysis_xlsx` which loads the file
and returns a list of dictionaries with properly typed values, as well as
``import_metaanalysis_xlsx`` which persists the parsed rows to the database.

Parsing rules implemented according to the specification provided:

* Leading/trailing whitespace in header names is stripped.
* Empty strings/``NaN`` values are normalised to ``None``.
* Yes/No fields are converted to booleans.
"""

from pathlib import Path
from typing import Any, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .models import RawRecord

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
            frame[col] = frame[col].astype(str).str.strip().str.lower().map(BOOL_MAP)
    for col in INT_FIELDS:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").astype("Int64")
    for col in FLOAT_FIELDS:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").astype(float)
    return frame


def _frame_to_records(
    frame: pd.DataFrame, original: pd.DataFrame
) -> list[dict[str, Any]]:
    """Convert ``frame`` to records and flag invalidly typed values.

    ``original`` should contain the raw, uncoerced values so that any fields
    which failed type coercion can be preserved as strings and marked as
    invalid. The returned dictionaries include an ``"_invalid"`` key listing the
    column names where coercion was unsuccessful.
    """

    records: list[dict[str, Any]] = []
    typed_cols = BOOL_FIELDS | INT_FIELDS | FLOAT_FIELDS
    for idx in range(len(frame)):
        rec: dict[str, Any] = {}
        invalid: list[str] = []
        for col in frame.columns:
            val = frame.iloc[idx][col]
            orig_val = original.iloc[idx][col]
            if col in typed_cols:
                if pd.isna(val) and pd.notna(orig_val):
                    rec[col] = str(orig_val)
                    invalid.append(col)
                else:
                    if pd.isna(val):
                        rec[col] = None
                    elif hasattr(val, "item"):
                        rec[col] = val.item()
                    else:
                        rec[col] = val
            else:
                if pd.isna(val):
                    rec[col] = None
                elif hasattr(val, "item"):
                    rec[col] = val.item()
                else:
                    rec[col] = val
        if invalid:
            rec["_invalid"] = invalid
        records.append(rec)
    return records


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
    original = frame.copy()
    frame = _coerce_dtypes(frame)
    return _frame_to_records(frame, original)


def import_metaanalysis_xlsx(path: str | Path) -> list["RawRecord"]:
    """Parse the XLSX file and store rows in the database.

    Parameters
    ----------
    path:
        Path to the workbook.

    Returns
    -------
    list[RawRecord]
        Database objects created from the parsed rows.
    """

    from .extensions import db
    from .models import RawRecord

    records = load_metaanalysis_xlsx(path)
    objects = [RawRecord(data=rec) for rec in records]
    db.session.add_all(objects)
    db.session.commit()
    return objects

from __future__ import annotations

"""Command line utilities for importing data from spreadsheets."""

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import click
import pandas as pd

from .extensions import db
from .models import Arm, Covariate, Effect, Outcome, Study, Tag

# Mapping of sheet names to models and required fields
SHEET_MAP: dict[str, tuple[type, list[str]]] = {
    "Study": (Study, ["title"]),
    "Arms": (Arm, ["study_id"]),
    "Outcomes": (Outcome, ["study_id", "name"]),
    "Effects": (Effect, ["study_id", "outcome_id", "effect_type"]),
    "Covariates": (Covariate, ["study_id", "name"]),
    "Tags": (Tag, ["study_id", "name"]),
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _clean_record(rec: dict[str, Any]) -> dict[str, Any]:
    """Replace NaN with None for database compatibility."""
    return {k: (None if pd.isna(v) else v) for k, v in rec.items()}


def _validate_record(rec: dict[str, Any], required: list[str]) -> list[tuple[str, str]]:
    """Validate presence of required fields."""
    errors: list[tuple[str, str]] = []
    for field in required:
        if rec.get(field) in (None, ""):
            errors.append((field, "missing required field"))
    return errors


def _load_sheet(df: pd.DataFrame, required: list[str], sheet: str, idx_offset: int = 0):
    records = []
    errors = []
    for i, rec in enumerate(df.to_dict(orient="records")):
        rec = _clean_record(rec)
        row_errs = _validate_record(rec, required)
        if row_errs:
            for field, msg in row_errs:
                errors.append(
                    {
                        "record": rec.get("id", i + idx_offset),
                        "error": msg,
                        "sheet": sheet,
                        "column": field,
                    }
                )
        else:
            records.append(rec)
    return records, errors


def _write_error_report(errors: Iterable[dict[str, Any]]) -> Path:
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = reports_dir / f"import_{ts}.csv"
    pd.DataFrame(list(errors)).to_csv(path, index=False)
    return path


def _clear_database() -> None:
    """Remove existing study related data."""
    db.session.query(Tag).delete()
    db.session.query(Covariate).delete()
    db.session.query(Effect).delete()
    db.session.query(Outcome).delete()
    db.session.query(Arm).delete()
    db.session.query(Study).delete()


# ---------------------------------------------------------------------------
# Import logic
# ---------------------------------------------------------------------------


def _import_data(frames: dict[str, pd.DataFrame], dry_run: bool, replace: bool) -> None:
    if replace:
        _clear_database()

    cache: dict[type, dict[int, Any]] = defaultdict(dict)
    errors: list[dict[str, Any]] = []
    objects: list[Any] = []

    for sheet, (model, required) in SHEET_MAP.items():
        if sheet not in frames:
            continue
        records, errs = _load_sheet(frames[sheet], required, sheet)
        errors.extend(errs)
        if errs:
            continue
        if model is Tag:
            for rec in records:
                study = cache[Study].get(rec["study_id"]) or Study.query.get(rec["study_id"])
                if not study:
                    errors.append(
                        {
                            "record": rec.get("study_id"),
                            "error": "Study not found",
                            "sheet": sheet,
                            "column": "study_id",
                        }
                    )
                    continue
                tag = Tag.query.filter_by(name=rec["name"]).first()
                if not tag:
                    tag = Tag(name=rec["name"])
                    objects.append(tag)
                study.tags.append(tag)
        else:
            for rec in records:
                obj = model(**rec)
                objects.append(obj)
                if "id" in rec:
                    cache[model][rec["id"]] = obj

    if errors:
        path = _write_error_report(errors)
        click.echo(f"Validation errors found. Report saved to {path}")
        db.session.rollback()
        return

    if not objects:
        click.echo("No data found to import. Check sheet names and required fields.")
        db.session.rollback()
        return

    if dry_run:
        click.echo("Dry run successful. No data committed.")
        db.session.rollback()
        return

    db.session.add_all(objects)
    db.session.commit()
    click.echo("Import completed successfully.")


# ---------------------------------------------------------------------------
# CLI entry points
# ---------------------------------------------------------------------------


def init_app(app) -> None:
    """Register CLI commands on the Flask app."""

    @app.cli.command("import-xlsx")
    @click.argument("path")
    @click.option("--dry-run", is_flag=True, help="Validate without committing")
    @click.option("--replace", is_flag=True, help="Clear existing data before import")
    def import_xlsx_cmd(path: str, dry_run: bool, replace: bool) -> None:
        """Import data from an XLSX workbook."""
        xls = pd.ExcelFile(path)
        # Match sheet names case-insensitively to be tolerant of user provided workbooks
        sheet_lookup = {name.strip().lower(): name for name in xls.sheet_names}
        frames: dict[str, pd.DataFrame] = {}
        for sheet in SHEET_MAP:
            key = sheet.strip().lower()
            if key in sheet_lookup:
                frames[sheet] = xls.parse(sheet_lookup[key])
        _import_data(frames, dry_run, replace)

    @app.cli.command("import-csv")
    @click.argument("folder")
    @click.option("--dry-run", is_flag=True, help="Validate without committing")
    @click.option("--replace", is_flag=True, help="Clear existing data before import")
    def import_csv_cmd(folder: str, dry_run: bool, replace: bool) -> None:
        """Import data from a folder of CSV files."""
        folder_path = Path(folder)
        frames: dict[str, pd.DataFrame] = {}
        for sheet in SHEET_MAP:
            csv_path = folder_path / f"{sheet}.csv"
            if csv_path.exists():
                frames[sheet] = pd.read_csv(csv_path)
        _import_data(frames, dry_run, replace)

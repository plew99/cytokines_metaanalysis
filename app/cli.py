"""Command line utilities for importing data from spreadsheets."""

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import click
import pandas as pd
import re
from sqlalchemy import inspect, text

from .extensions import db
from .models import (
    Arm,
    Covariate,
    Effect,
    GroupOutcome,
    Outcome,
    RawRecord,
    Study,
    StudyGroup,
    Tag,
)
from .xlsx_parser import load_metaanalysis_xlsx

# Mapping of sheet names to models and required fields
SHEET_MAP: dict[str, tuple[type, list[str]]] = {
    "Study": (Study, ["title"]),
    "Arms": (Arm, ["study_id"]),
    "Outcomes": (Outcome, ["study_id", "name"]),
    "Effects": (Effect, ["study_id", "outcome_id", "effect_type"]),
    "Covariates": (Covariate, ["study_id", "name"]),
    "Tags": (Tag, ["study_id", "name"]),
}

GROUP_FIELDS: list[str] = [
    "n",
    "Age (mean / median)",
    "Age (SD / IQR)",
    "Age mean-SD / median-IQR",
    "% Males",
    "Ethicity",
    "Group description (MCI / DCM / Healthy / …)",
    "Other important group infomation",
    "Inflammation excluded by EMB",
    "CAD excluded",
    "Other possible causes of MCI / DCM (drugs, SARS-CoV-2…)",
    "Description of disease comfirmation",
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _clean_record(rec: dict[str, Any]) -> dict[str, Any]:
    """Replace NaN with None for database compatibility."""
    return {k: (None if pd.isna(v) else v) for k, v in rec.items()}


def _parse_measurement_desc(desc: Any) -> tuple[str, str]:
    """Return central tendency and dispersion types from a descriptor string.

    Parameters
    ----------
    desc:
        The descriptor string, e.g. ``"Mean±SD"`` or ``"Median (IQR)"``.

    Returns
    -------
    tuple[str, str]
        ``(central_type, dispersion_type)`` where each element is one of
        ``"mean"``, ``"median"``, ``"sd"``, ``"iqr"``, ``"p25-75"``,
        ``"min-max"`` or ``"unknown"``.
    """

    if not isinstance(desc, str):
        return "unknown", "unknown"
    text = desc.lower()
    if "mean" in text:
        central = "mean"
    elif "median" in text:
        central = "median"
    else:
        central = "unknown"

    if "sd" in text:
        dispersion = "sd"
    elif "iqr" in text:
        dispersion = "iqr"
    elif "25" in text and "75" in text:
        dispersion = "p25-75"
    elif "min" in text and "max" in text:
        dispersion = "min-max"
    else:
        dispersion = "unknown"
    return central, dispersion


def _parse_float(value: Any, *, take: str = "last") -> float | None:
    """Parse a float from ``value`` handling commas and ranges.

    If ``value`` contains multiple numbers (e.g. ``"0,49-28,50"``), the
    first or last number can be selected via ``take``.
    """

    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", ".")
        numbers = re.findall(r"\d+(?:\.\d+)?", cleaned)
        if not numbers:
            return None
        return float(numbers[0]) if take == "first" else float(numbers[-1])
    return None


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
            click.echo(f"Skipping missing sheet: {sheet}")
            continue
        click.echo(f"Processing sheet '{sheet}' ({len(frames[sheet])} rows)")
        records, errs = _load_sheet(frames[sheet], required, sheet)
        click.echo(f" -> {len(records)} valid rows, {len(errs)} errors")
        errors.extend(errs)
        if errs:
            continue
        if model is Tag:
            for rec in records:
                study = cache[Study].get(rec["study_id"]) or Study.query.get(
                    rec["study_id"]
                )
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
        click.echo(f"{len(errors)} validation errors found. Report saved to {path}")
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
    click.echo(f"Import completed successfully. Imported {len(objects)} objects.")


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
        # Ensure all tables exist before attempting to import any data
        db.create_all()

        xls = pd.ExcelFile(path)
        click.echo(f"Workbook contains sheets: {', '.join(xls.sheet_names)}")
        # Match sheet names case-insensitively to be tolerant of user provided workbooks
        sheet_lookup = {name.strip().lower(): name for name in xls.sheet_names}
        # Special handling for metaanalysis workbook with single "Arkusz1" sheet
        arkusz_key = "arkusz1"
        if arkusz_key in sheet_lookup and not any(
            s.lower() in sheet_lookup for s in SHEET_MAP
        ):
            records = load_metaanalysis_xlsx(path)
            click.echo(
                f"Loaded sheet '{sheet_lookup[arkusz_key]}' with {len(records)} rows"
            )
            if dry_run:
                click.echo("Dry run complete. No data persisted.")
                return
            if replace:
                db.session.query(RawRecord).delete()
            objects = [RawRecord(data=rec) for rec in records]
            db.session.add_all(objects)
            db.session.commit()
            click.echo(
                f"Import completed successfully. Imported {len(objects)} objects."
            )
            return
        frames: dict[str, pd.DataFrame] = {}
        for sheet in SHEET_MAP:
            key = sheet.strip().lower()
            if key in sheet_lookup:
                frame = xls.parse(sheet_lookup[key])
                frames[sheet] = frame
                click.echo(
                    f"Loaded sheet '{sheet_lookup[key]}' as '{sheet}' with {len(frame)} rows"
                )
            else:
                click.echo(f"Expected sheet '{sheet}' not found in workbook")
        if not frames:
            click.echo(
                "No recognized sheets found. Expected one of: "
                + ", ".join(SHEET_MAP.keys())
            )
            return
        _import_data(frames, dry_run, replace)

    @app.cli.command("import-csv")
    @click.argument("folder")
    @click.option("--dry-run", is_flag=True, help="Validate without committing")
    @click.option("--replace", is_flag=True, help="Clear existing data before import")
    def import_csv_cmd(folder: str, dry_run: bool, replace: bool) -> None:
        """Import data from a folder of CSV files."""
        # Ensure tables exist before reading CSV files
        db.create_all()

        folder_path = Path(folder)
        frames: dict[str, pd.DataFrame] = {}
        for sheet in SHEET_MAP:
            csv_path = folder_path / f"{sheet}.csv"
            if csv_path.exists():
                frames[sheet] = pd.read_csv(csv_path)
        _import_data(frames, dry_run, replace)

    @app.cli.command("raw-to-studies")
    @click.option(
        "--replace", is_flag=True, help="Clear existing studies before creation"
    )
    def raw_to_studies_cmd(replace: bool) -> None:
        """Create :class:`Study` objects from stored :class:`RawRecord` data."""

        db.create_all()
        if replace:
            db.session.query(Study).delete()

        records = RawRecord.query.all()
        seen: set[str] = set()
        objects: list[Study] = []
        for rec in records:
            data = rec.data
            title = (
                data.get("ID")
                or f"{data.get('First author', 'Unknown')} {data.get('Year', '')}".strip()
            )
            if title in seen or Study.query.filter_by(title=title).first():
                continue
            seen.add(title)
            study = Study(
                title=title,
                year=data.get("Year"),
                country=data.get("Country"),
                design=data.get("Study type"),
                authors_text=data.get("First author"),
                notes=data.get("Important notes"),
            )
            objects.append(study)

        if not objects:
            click.echo("No studies created from raw records.")
            return

        db.session.add_all(objects)
        db.session.commit()
        click.echo(f"Created {len(objects)} studies from raw records.")

    @app.cli.command("raw-to-groups")
    @click.option(
        "--replace", is_flag=True, help="Clear existing study groups before creation"
    )
    def raw_to_groups_cmd(replace: bool) -> None:
        """Create :class:`StudyGroup` objects from raw records."""

        db.create_all()
        inspector = inspect(db.engine)
        outcome_cols = [col["name"] for col in inspector.get_columns("outcome")]
        if "method" not in outcome_cols:
            with db.engine.begin() as conn:
                conn.execute(text("ALTER TABLE outcome ADD COLUMN method VARCHAR(255)"))
        if replace:
            db.session.query(StudyGroup).delete()

        records = RawRecord.query.all()
        seen: set[tuple[int, tuple[tuple[str, Any], ...]]] = set()
        created = 0
        for rec in records:
            data = rec.data
            study = Study.query.filter_by(title=data.get("ID")).first()
            if not study:
                continue
            group_vals = {field: data.get(field) for field in GROUP_FIELDS}
            # Extract primary outcome information (cytokine concentrations)
            central, dispersion = _parse_measurement_desc(
                data.get("Cytokine conecentration mean-SD / median-IQR")
            )
            po_name = data.get("Cytokine")
            po_unit = data.get("Cytokine unit")
            po_method = data.get("Method of measurement")
            outcome = Outcome.query.filter_by(
                study_id=study.id, name=po_name, unit=po_unit, method=po_method
            ).first()
            if not outcome:
                outcome = Outcome(
                    study_id=study.id, name=po_name, unit=po_unit, method=po_method
                )
                db.session.add(outcome)
                db.session.flush()

            key = (study.id, tuple((f, group_vals.get(f)) for f in GROUP_FIELDS))
            if key in seen:
                continue
            seen.add(key)
            group = StudyGroup(
                study_id=study.id,
                n=group_vals.get("n"),
                age_mean_median=group_vals.get("Age (mean / median)"),
                age_sd_iqr=group_vals.get("Age (SD / IQR)"),
                age_mean_sd_median_iqr=group_vals.get("Age mean-SD / median-IQR"),
                percent_males=group_vals.get("% Males"),
                ethnicity=group_vals.get("Ethicity"),
                description=group_vals.get(
                    "Group description (MCI / DCM / Healthy / …)"
                ),
                other_info=group_vals.get("Other important group infomation"),
                inflammation_excluded_by_emb=group_vals.get(
                    "Inflammation excluded by EMB"
                ),
                cad_excluded=group_vals.get("CAD excluded"),
                other_causes=group_vals.get(
                    "Other possible causes of MCI / DCM (drugs, SARS-CoV-2…)"
                ),
                disease_confirmation=group_vals.get(
                    "Description of disease comfirmation"
                ),
            )
            db.session.add(group)
            db.session.flush()

            db.session.add(
                GroupOutcome(
                    group_id=group.id,
                    outcome_id=outcome.id,
                    value=_parse_float(
                        data.get("Cytokine contrentration mean / median"), take="first"
                    ),
                    value_type=central,
                    dispersion=_parse_float(
                        data.get("Cytokine concentration SD / IQR"), take="last"
                    ),
                    dispersion_type=dispersion,
                )
            )
            created += 1

        if created == 0:
            db.session.commit()
            click.echo("No study groups created from raw records.")
            return

        db.session.commit()
        click.echo(f"Created {created} study groups from raw records.")

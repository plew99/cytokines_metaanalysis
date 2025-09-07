import os
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

from app import create_app
from app.extensions import db
from app.models import RawRecord
from app.xlsx_parser import import_metaanalysis_xlsx, load_metaanalysis_xlsx


def _create_sample_xlsx(path):
    data = {
        "ID": ["M00022", "M00221"],
        "First author": ["Bielecka-Dabrowa", "Guerra-de-Blas"],
        "Year": [2013, 2022],
        "Country": ["Poland", "Mexico"],
        "Study type": [
            "RCT - mean value after treatment",
            "Observational study",
        ],
        "Date": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")],
        "n": [30, 80],
        "Age (mean / median)": [58.4, 51],
        "Age (SD / IQR)": [11.85, 12.2],
        "% Males": [78, 62.9],
        "Age mean-SD / median-IQR": ["Mean±SD", "Median (IQR)"],
        "Ethicity ": ["ND", "ND"],
        "Inflammation excluded by EMB": ["Yes", "No"],
        "CAD excluded": ["Yes", "Yes"],
        "Other possible causes of MCI / DCM (drugs, SARS-CoV-2…)": [
            "Yes (excluded)",
            "Yes (excluded)",
        ],
        "Description of disease comfirmation": [
            "HF symptoms + Echo + ECG",
            "Echo + EMB",
        ],
        "Method of measurement": ["ELISA", ""],  # second row blank to test null
        "Cytokine contrentration mean / median": [2.4, 9.5],
        "Cytokine concentration SD / IQR": [1.6, 12.6],
        "Cytokine unit": ["pg/mL", "ng/mL"],
        "Cytokine conecentration mean-SD / median-IQR": [
            "Mean±SD",
            "Median (IQR)",
        ],
        "NYHA Scale": [0, 0],
        "LVEF Mean SD / Median SQR": ["Mean±SD", "Median (IQR)"],
        "LVEF % ": [48.0, 33.0],
        "LVEDD mean SD / MEDIAN IQR": ["Mean±SD", "Median (IQR)"],
        "LVEDD SD": ["±3.2", "±4.5"],
        "EMB performed?": ["No", "Yes"],
        "EMB Criteria": ["Dallas", "Immunohistochemistry"],
        "lymphocytes per mm2": [">14", "<7"],
        "Other EMB Data": ["CD68+", "HLA upregulation"],
        "Viruses presence": ["Enterovirus", "Parvovirus B19"],
        "cMRI performed": ["No", "Yes"],
        "CRP mean-SD / median-IQR": ["Mean±SD", "Median (IQR)"],
        "CRP": [6.7, 2.25],
        "CRP unit": ["mg/dL", "mg/L"],
        "NT-proBNP mean-SD / median-IQR": ["Mean±SD", "Median (IQR)"],
        "NT-proBNP": [277.0, 2418.0],
        "NT-proBNP unit": ["pg/mL", "ng/L"],
        "cTnT mean-SD / median-IQR": ["Mean±SD", "Median (IQR)"],
        "cTnT": [0.008, 0.09],
        "cTnT unit": ["ng/mL", "pg/mL"],
        "cTnI mean-SD / median-IQR": ["Mean±SD", "Median (IQR)"],
        "cTnI": [0.02, 0.01],
        "cTnI unit": ["ng/mL", "pg/mL"],
        "Outcome": ["Mortality", "HF hospitalization"],
        "Follow-up time (months)": [12.0, 24.0],
        "Subgroups": ["MCI", "DCM"],
        "Pathology": ["Myocarditis", "DCM"],
        "Cohort": ["HF", "MCI"],
        "Important notes": [
            "Data extracted from plot using plotdigitizer",
            "peak values taken",
        ],
    }
    df = pd.DataFrame(data)
    with pd.ExcelWriter(path) as writer:
        df.to_excel(writer, sheet_name="Arkusz1", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="Arkusz2", index=False)


def _create_invalid_xlsx(path):
    data = {
        "ID": ["M00022"],
        "Year": ["20X3"],
        "cMRI performed": ["maybe"],
    }
    df = pd.DataFrame(data)
    with pd.ExcelWriter(path) as writer:
        df.to_excel(writer, sheet_name="Arkusz1", index=False)


def test_parser_handles_types_and_nulls(tmp_path):
    xlsx_path = tmp_path / "Metaanalysis data.xlsx"
    _create_sample_xlsx(xlsx_path)
    records = load_metaanalysis_xlsx(xlsx_path)
    assert len(records) == 2
    first, second = records

    assert isinstance(first["Year"], int) and first["Year"] == 2013
    assert first["Inflammation excluded by EMB"] is True
    assert second["Inflammation excluded by EMB"] is False
    # Column headers stripped of whitespace
    assert "Ethicity" in first and "LVEF %" in first
    # Empty string converted to None
    assert second["Method of measurement"] is None
    # Booleans handled
    assert first["cMRI performed"] is False and second["cMRI performed"] is True
    # Floats parsed
    assert isinstance(second["Follow-up time (months)"], float)
    # Datetimes converted to ISO strings
    assert first["Date"] == "2024-01-01T00:00:00"


def test_import_persists_rows(tmp_path):
    xlsx_path = tmp_path / "Metaanalysis data.xlsx"
    _create_sample_xlsx(xlsx_path)

    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()
        objects = import_metaanalysis_xlsx(xlsx_path)
        assert RawRecord.query.count() == 2
        assert objects[0].data["ID"] == "M00022"


def test_invalid_values_are_flagged(tmp_path):
    xlsx_path = tmp_path / "Invalid data.xlsx"
    _create_invalid_xlsx(xlsx_path)

    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()
        objects = import_metaanalysis_xlsx(xlsx_path)
        rec = objects[0].data
        assert rec["Year"] == "20X3"
        assert rec["cMRI performed"] == "maybe"
        assert set(rec["_invalid"]) == {"Year", "cMRI performed"}

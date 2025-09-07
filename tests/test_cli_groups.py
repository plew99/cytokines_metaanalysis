import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

from app import create_app
from app.extensions import db
from app.models import RawRecord, Study, StudyGroup
from test_xlsx_parser import _create_sample_xlsx


def test_cli_creates_study_groups(tmp_path):
    xlsx_path = tmp_path / "Metaanalysis data.xlsx"
    _create_sample_xlsx(xlsx_path)

    app = create_app()
    app.config.update(TESTING=True)
    runner = app.test_cli_runner()

    with app.app_context():
        runner.invoke(args=["import-xlsx", str(xlsx_path)])
        runner.invoke(args=["raw-to-studies"])

        first = RawRecord.query.first()
        data2 = dict(first.data)
        data2["n"] = 15
        db.session.add(RawRecord(data=data2))
        db.session.commit()

        result = runner.invoke(args=["raw-to-groups"])
        assert result.exit_code == 0
        assert StudyGroup.query.count() == 3
        study = Study.query.filter_by(title="M00022").first()
        assert len(study.groups) == 2

        # verify primary outcome data attached to groups
        group = study.groups[0]
        assert group.primary_outcome.name == "IL6"
        assert group.primary_outcome_value == 2.4
        assert group.primary_outcome_value_type == "mean"
        assert group.primary_outcome_dispersion == 1.6
        assert group.primary_outcome_dispersion_type == "sd"
        assert group.primary_outcome.unit == "pg/mL"
        assert group.primary_outcome.method == "ELISA"

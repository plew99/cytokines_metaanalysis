import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

from app import create_app
from app.extensions import db
from app.models import RawRecord
from test_xlsx_parser import _create_sample_xlsx


def test_cli_import_handles_arkusz1(tmp_path):
    xlsx_path = tmp_path / "Metaanalysis data.xlsx"
    _create_sample_xlsx(xlsx_path)

    app = create_app()
    app.config.update(TESTING=True)
    runner = app.test_cli_runner()
    with app.app_context():
        db.create_all()
        result = runner.invoke(args=["import-xlsx", str(xlsx_path)])
        assert result.exit_code == 0
        assert "Loaded sheet 'Arkusz1' with 2 rows" in result.output
        assert RawRecord.query.count() == 2
        assert RawRecord.query.first().data["Date"] == "2024-01-01T00:00:00"

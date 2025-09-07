import csv
import sys
from pathlib import Path
from flask import Flask

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.models import (
    db,
    Study,
    Cohort,
    import_studies_from_csv,
    import_cohorts_from_csv,
)

def setup_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def test_import_studies_and_cohorts(tmp_path):
    app = setup_app()
    with app.app_context():
        db.create_all()
        study_csv = tmp_path / 'studies.csv'
        with study_csv.open('w', newline='') as fh:
            writer = csv.writer(fh)
            writer.writerow(['study_id','first_author','publication_year','country','study_design','notes'])
            writer.writerow(['S1','Smith','2020','USA','RCT','note1'])
        import_studies_from_csv(str(study_csv))
        assert Study.query.count() == 1
        cohort_csv = tmp_path / 'cohorts.csv'
        with cohort_csv.open('w', newline='') as fh:
            writer = csv.writer(fh)
            writer.writerow(['study_id','cohort_label','sample_size'])
            writer.writerow(['S1','Control','10'])
        import_cohorts_from_csv(str(cohort_csv))
        assert Cohort.query.count() == 1
        cohort = Cohort.query.first()
        assert cohort.sample_size == 10

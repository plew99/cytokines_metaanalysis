import io
from app import create_app
from app.models import db, Study, Cohort


def create_test_app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
    return app


def test_import_studies_and_cohorts_via_page():
    app = create_test_app()
    client = app.test_client()

    studies_csv = (
        "study_id,first_author,publication_year,country,study_design,notes\n"
        "S1,Smith,2020,USA,RCT,note1\n"
    ).encode("utf-8")
    resp = client.post(
        "/import",
        data={
            "data_type": "studies",
            "file": (io.BytesIO(studies_csv), "studies.csv"),
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 302
    with app.app_context():
        assert Study.query.count() == 1

    cohorts_csv = ("study_id,cohort_label,sample_size\n" "S1,Control,10\n").encode(
        "utf-8"
    )
    resp = client.post(
        "/import",
        data={
            "data_type": "cohorts",
            "file": (io.BytesIO(cohorts_csv), "cohorts.csv"),
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 302
    with app.app_context():
        assert Cohort.query.count() == 1

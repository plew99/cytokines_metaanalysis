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
        db.drop_all()
        db.create_all()
    return app


def test_sorting_and_cohort_links():
    app = create_test_app()
    with app.app_context():
        s1 = Study(study_id="S1", first_author="Beta", publication_year=2019)
        s2 = Study(study_id="S2", first_author="Alpha", publication_year=2020)
        db.session.add_all([s1, s2])
        db.session.flush()
        c1 = Cohort(study_id="S1", cohort_label="Control")
        c2 = Cohort(study_id="S2", cohort_label="Treatment")
        db.session.add_all([c1, c2])
        db.session.commit()
        cohort_id = c1.cohort_id

    client = app.test_client()
    resp = client.get("/studies?sort=first_author&direction=asc")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert body.find("Alpha") < body.find("Beta")
    assert "Control" in body
    assert f"/cohorts/{cohort_id}" in body

    resp = client.get(f"/cohorts/{cohort_id}")
    assert resp.status_code == 200
    assert "Control" in resp.get_data(as_text=True)

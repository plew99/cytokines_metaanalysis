import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

from app import create_app
from app.extensions import db
from app.models import Study, StudyGroup


def test_study_group_detail_route():
    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()
        study = Study(title="Test study")
        db.session.add(study)
        db.session.commit()
        group = StudyGroup(
            study_id=study.id,
            data={"Group description (MCI / DCM / Healthy / …)": "Group A", "n": 10},
        )
        db.session.add(group)
        db.session.commit()
        client = app.test_client()
        resp = client.get(f"/studies/{study.id}/groups/{group.id}")
        assert resp.status_code == 200
        assert b"Group A" in resp.data
        assert b"n" in resp.data
        assert b"10" in resp.data

"""SQLAlchemy ORM models for meta-analysis database."""

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db


class Study(db.Model):
    """Primary study information."""

    __tablename__ = "study"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(db.String(255), nullable=False)
    year: Mapped[int | None] = mapped_column(db.Integer)
    journal: Mapped[str | None] = mapped_column(db.String(255))
    doi: Mapped[str | None] = mapped_column(db.String(255), unique=True)
    authors_text: Mapped[str | None] = mapped_column(db.Text)
    country: Mapped[str | None] = mapped_column(db.String(128))
    design: Mapped[str | None] = mapped_column(db.String(128))
    notes: Mapped[str | None] = mapped_column(db.Text)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    arms: Mapped[list["Arm"]] = relationship(back_populates="study")
    outcomes: Mapped[list["Outcome"]] = relationship(back_populates="study")
    effects: Mapped[list["Effect"]] = relationship(back_populates="study")
    covariates: Mapped[list["Covariate"]] = relationship(back_populates="study")
    tags: Mapped[list["Tag"]] = relationship(
        secondary="study_tag", back_populates="studies"
    )


class Arm(db.Model):
    """Participant arm within a study."""

    __tablename__ = "arm"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(db.ForeignKey("study.id"), index=True)
    name: Mapped[str | None] = mapped_column(db.String(128))
    n: Mapped[int | None] = mapped_column(db.Integer)
    desc: Mapped[str | None] = mapped_column(db.Text)

    study: Mapped[Study] = relationship(back_populates="arms")

    __table_args__ = (CheckConstraint("n >= 0", name="ck_arm_n_nonnegative"),)


class Outcome(db.Model):
    """Measured outcome within a study."""

    __tablename__ = "outcome"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(db.ForeignKey("study.id"), index=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    unit: Mapped[str | None] = mapped_column(db.String(64))
    direction: Mapped[str | None] = mapped_column(db.String(16))
    domain: Mapped[str | None] = mapped_column(db.String(64))

    study: Mapped[Study] = relationship(back_populates="outcomes")
    effects: Mapped[list["Effect"]] = relationship(back_populates="outcome")


class Effect(db.Model):
    """Effect size or arm-level statistics."""

    __tablename__ = "effect"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(db.ForeignKey("study.id"), nullable=False)
    outcome_id: Mapped[int] = mapped_column(db.ForeignKey("outcome.id"), nullable=False)
    arm_id: Mapped[int | None] = mapped_column(db.ForeignKey("arm.id"))
    arm_treat_id: Mapped[int | None] = mapped_column(db.ForeignKey("arm.id"))
    arm_ctrl_id: Mapped[int | None] = mapped_column(db.ForeignKey("arm.id"))
    effect_type: Mapped[str] = mapped_column(
        db.Enum("SMD", "MD", "logOR", "RR", name="effect_type_enum"),
        nullable=False,
    )
    effect: Mapped[float | None] = mapped_column(db.Float)
    se: Mapped[float | None] = mapped_column(db.Float)
    ci_low: Mapped[float | None] = mapped_column(db.Float)
    ci_high: Mapped[float | None] = mapped_column(db.Float)
    mean: Mapped[float | None] = mapped_column(db.Float)
    sd: Mapped[float | None] = mapped_column(db.Float)
    n: Mapped[int | None] = mapped_column(db.Integer)
    events: Mapped[int | None] = mapped_column(db.Integer)
    total: Mapped[int | None] = mapped_column(db.Integer)

    study: Mapped[Study] = relationship(back_populates="effects")
    outcome: Mapped[Outcome] = relationship(back_populates="effects")
    arm: Mapped[Arm | None] = relationship(foreign_keys=[arm_id])
    arm_treat: Mapped[Arm | None] = relationship(foreign_keys=[arm_treat_id])
    arm_ctrl: Mapped[Arm | None] = relationship(foreign_keys=[arm_ctrl_id])

    __table_args__ = (
        CheckConstraint("n >= 0", name="ck_effect_n_nonnegative"),
        CheckConstraint("sd >= 0", name="ck_effect_sd_nonnegative"),
        CheckConstraint("events <= total", name="ck_effect_events_total"),
        Index("ix_effect_outcome_study", "outcome_id", "study_id"),
    )


class Covariate(db.Model):
    """Covariate value for a study."""

    __tablename__ = "covariate"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(db.ForeignKey("study.id"))
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    value: Mapped[str | None] = mapped_column(db.String(255))

    study: Mapped[Study] = relationship(back_populates="covariates")


study_tag = db.Table(
    "study_tag",
    db.Column("study_id", db.Integer, db.ForeignKey("study.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class Tag(db.Model):
    """Tag assigned to studies."""

    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False)

    studies: Mapped[list[Study]] = relationship(
        secondary=study_tag, back_populates="tags"
    )


class User(db.Model):
    """Application user (not yet used)."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    role: Mapped[str] = mapped_column(db.String(64), nullable=False, default="user")


class RawRecord(db.Model):
    """Raw row data imported from the metaanalysis XLSX."""

    __tablename__ = "raw_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(db.JSON, nullable=False)

"""Add data_type and unit to group_outcome; trim study_group columns"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_group_outcome_unit_data_type"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        "group_outcome",
        sa.Column("data_type", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "group_outcome",
        sa.Column("unit", sa.String(length=64), nullable=True),
    )
    op.drop_column("study_group", "age_mean_median")
    op.drop_column("study_group", "age_sd_iqr")
    op.drop_column("study_group", "age_mean_sd_median_iqr")
    op.drop_column("study_group", "percent_males")
    op.drop_column("study_group", "ethnicity")
    op.drop_column("study_group", "other_info")
    op.drop_column("study_group", "inflammation_excluded_by_emb")
    op.drop_column("study_group", "cad_excluded")
    op.drop_column("study_group", "other_causes")
    op.drop_column("study_group", "disease_confirmation")


def downgrade() -> None:
    op.add_column(
        "study_group",
        sa.Column("disease_confirmation", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "study_group",
        sa.Column("other_causes", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "study_group",
        sa.Column("cad_excluded", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "study_group",
        sa.Column(
            "inflammation_excluded_by_emb", sa.String(length=255), nullable=True
        ),
    )
    op.add_column(
        "study_group",
        sa.Column("other_info", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "study_group",
        sa.Column("ethnicity", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "study_group",
        sa.Column("percent_males", sa.Float(), nullable=True),
    )
    op.add_column(
        "study_group",
        sa.Column("age_mean_sd_median_iqr", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "study_group",
        sa.Column("age_sd_iqr", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "study_group",
        sa.Column("age_mean_median", sa.String(length=255), nullable=True),
    )
    op.drop_column("group_outcome", "unit")
    op.drop_column("group_outcome", "data_type")

"""economy_daily_kpis

Revision ID: 20260331_0020
Revises: 20260331_0019
Create Date: 2026-03-31
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260331_0020"
down_revision: str | None = "20260331_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "economy_daily_kpis" not in tables:
        op.create_table(
            "economy_daily_kpis",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("experiment_name", sa.String(length=80), nullable=False),
            sa.Column("cohort", sa.String(length=32), nullable=False),
            sa.Column("active_users", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("new_users", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("first_purchase_users", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("second_purchase_48h_users", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("second_purchase_48h_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("d1_retention_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("d7_retention_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("lmn_earned", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("lmn_spent", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("lmn_spent_earned_ratio", sa.Float(), nullable=False, server_default="0"),
            sa.Column("avg_balance", sa.Float(), nullable=False, server_default="0"),
            sa.Column("median_balance", sa.Float(), nullable=False, server_default="0"),
            sa.Column("store_views", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("store_purchases", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("store_conversion_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("wallet_views", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("mission_completions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("avg_time_to_first_purchase_hours", sa.Float(), nullable=True),
            sa.Column("avg_time_to_second_purchase_hours", sa.Float(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.UniqueConstraint(
                "date",
                "experiment_name",
                "cohort",
                name="uq_economy_daily_kpis_day_experiment_cohort",
            ),
        )

    index_names = _index_names(inspector, "economy_daily_kpis")
    if "ix_economy_daily_kpis_date" not in index_names:
        op.create_index("ix_economy_daily_kpis_date", "economy_daily_kpis", ["date"])
    if "ix_economy_daily_kpis_experiment_name" not in index_names:
        op.create_index(
            "ix_economy_daily_kpis_experiment_name",
            "economy_daily_kpis",
            ["experiment_name"],
        )
    if "ix_economy_daily_kpis_cohort" not in index_names:
        op.create_index("ix_economy_daily_kpis_cohort", "economy_daily_kpis", ["cohort"])
    if "ix_economy_daily_kpis_date_experiment" not in index_names:
        op.create_index(
            "ix_economy_daily_kpis_date_experiment",
            "economy_daily_kpis",
            ["date", "experiment_name"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "economy_daily_kpis" not in tables:
        return

    index_names = _index_names(inspector, "economy_daily_kpis")
    if "ix_economy_daily_kpis_date_experiment" in index_names:
        op.drop_index("ix_economy_daily_kpis_date_experiment", table_name="economy_daily_kpis")
    if "ix_economy_daily_kpis_cohort" in index_names:
        op.drop_index("ix_economy_daily_kpis_cohort", table_name="economy_daily_kpis")
    if "ix_economy_daily_kpis_experiment_name" in index_names:
        op.drop_index("ix_economy_daily_kpis_experiment_name", table_name="economy_daily_kpis")
    if "ix_economy_daily_kpis_date" in index_names:
        op.drop_index("ix_economy_daily_kpis_date", table_name="economy_daily_kpis")
    op.drop_table("economy_daily_kpis")

"""guest_anti_abuse_signal_columns

Revision ID: 20260406_0025
Revises: 20260406_0024
Create Date: 2026-04-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260406_0025"
down_revision = "20260406_0024"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(column.get("name") == column_name for column in inspector.get_columns(table_name))


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if _has_table("guest_scenario_run_usage") and not _has_column(
        "guest_scenario_run_usage", "last_fingerprint_hash"
    ):
        op.add_column(
            "guest_scenario_run_usage",
            sa.Column("last_fingerprint_hash", sa.String(length=64), nullable=True),
        )
    if _has_table("guest_scenario_run_usage") and not _has_index(
        "guest_scenario_run_usage", "ix_guest_scenario_run_usage_last_fingerprint_hash"
    ):
        op.create_index(
            "ix_guest_scenario_run_usage_last_fingerprint_hash",
            "guest_scenario_run_usage",
            ["last_fingerprint_hash"],
        )

    if _has_table("scenario_game_token_events") and not _has_column(
        "scenario_game_token_events", "ip_hash"
    ):
        op.add_column(
            "scenario_game_token_events",
            sa.Column("ip_hash", sa.String(length=64), nullable=True),
        )
    if _has_table("scenario_game_token_events") and not _has_column(
        "scenario_game_token_events", "user_agent_hash"
    ):
        op.add_column(
            "scenario_game_token_events",
            sa.Column("user_agent_hash", sa.String(length=64), nullable=True),
        )
    if _has_table("scenario_game_token_events") and not _has_column(
        "scenario_game_token_events", "fingerprint_hash"
    ):
        op.add_column(
            "scenario_game_token_events",
            sa.Column("fingerprint_hash", sa.String(length=64), nullable=True),
        )

    if _has_table("scenario_game_token_events") and not _has_index(
        "scenario_game_token_events", "ix_scenario_game_token_events_ip_hash"
    ):
        op.create_index(
            "ix_scenario_game_token_events_ip_hash",
            "scenario_game_token_events",
            ["ip_hash"],
        )
    if _has_table("scenario_game_token_events") and not _has_index(
        "scenario_game_token_events", "ix_scenario_game_token_events_fingerprint_hash"
    ):
        op.create_index(
            "ix_scenario_game_token_events_fingerprint_hash",
            "scenario_game_token_events",
            ["fingerprint_hash"],
        )


def downgrade() -> None:
    if _has_table("scenario_game_token_events") and _has_index(
        "scenario_game_token_events", "ix_scenario_game_token_events_fingerprint_hash"
    ):
        op.drop_index("ix_scenario_game_token_events_fingerprint_hash", table_name="scenario_game_token_events")
    if _has_table("scenario_game_token_events") and _has_index(
        "scenario_game_token_events", "ix_scenario_game_token_events_ip_hash"
    ):
        op.drop_index("ix_scenario_game_token_events_ip_hash", table_name="scenario_game_token_events")

    if _has_table("scenario_game_token_events") and _has_column(
        "scenario_game_token_events", "fingerprint_hash"
    ):
        op.drop_column("scenario_game_token_events", "fingerprint_hash")
    if _has_table("scenario_game_token_events") and _has_column(
        "scenario_game_token_events", "user_agent_hash"
    ):
        op.drop_column("scenario_game_token_events", "user_agent_hash")
    if _has_table("scenario_game_token_events") and _has_column("scenario_game_token_events", "ip_hash"):
        op.drop_column("scenario_game_token_events", "ip_hash")

    if _has_table("guest_scenario_run_usage") and _has_index(
        "guest_scenario_run_usage", "ix_guest_scenario_run_usage_last_fingerprint_hash"
    ):
        op.drop_index(
            "ix_guest_scenario_run_usage_last_fingerprint_hash",
            table_name="guest_scenario_run_usage",
        )
    if _has_table("guest_scenario_run_usage") and _has_column(
        "guest_scenario_run_usage", "last_fingerprint_hash"
    ):
        op.drop_column("guest_scenario_run_usage", "last_fingerprint_hash")

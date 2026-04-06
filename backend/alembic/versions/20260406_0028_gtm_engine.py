"""gtm_engine

Revision ID: 20260406_0028
Revises: 20260406_0027
Create Date: 2026-04-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260406_0028"
down_revision = "20260406_0027"
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


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _has_column(table_name, str(column.name)):
        op.add_column(table_name, column)


def upgrade() -> None:
    if _has_table("analytics_events"):
        _add_column_if_missing("analytics_events", sa.Column("ad_id", sa.String(length=120), nullable=True))
        _add_column_if_missing("analytics_events", sa.Column("creative_id", sa.String(length=120), nullable=True))
        if not _has_index("analytics_events", "ix_analytics_events_ad_id"):
            op.create_index("ix_analytics_events_ad_id", "analytics_events", ["ad_id"])
        if not _has_index("analytics_events", "ix_analytics_events_creative_id"):
            op.create_index("ix_analytics_events_creative_id", "analytics_events", ["creative_id"])

    if _has_table("session_attributions"):
        _add_column_if_missing("session_attributions", sa.Column("first_ad_id", sa.String(length=120), nullable=True))
        _add_column_if_missing(
            "session_attributions",
            sa.Column("first_creative_id", sa.String(length=120), nullable=True),
        )
        _add_column_if_missing("session_attributions", sa.Column("last_ad_id", sa.String(length=120), nullable=True))
        _add_column_if_missing(
            "session_attributions",
            sa.Column("last_creative_id", sa.String(length=120), nullable=True),
        )
        if not _has_index("session_attributions", "ix_session_attributions_first_ad_id"):
            op.create_index("ix_session_attributions_first_ad_id", "session_attributions", ["first_ad_id"])
        if not _has_index("session_attributions", "ix_session_attributions_first_creative_id"):
            op.create_index(
                "ix_session_attributions_first_creative_id",
                "session_attributions",
                ["first_creative_id"],
            )
        if not _has_index("session_attributions", "ix_session_attributions_last_ad_id"):
            op.create_index("ix_session_attributions_last_ad_id", "session_attributions", ["last_ad_id"])
        if not _has_index("session_attributions", "ix_session_attributions_last_creative_id"):
            op.create_index(
                "ix_session_attributions_last_creative_id",
                "session_attributions",
                ["last_creative_id"],
            )

    if _has_table("user_attributions"):
        _add_column_if_missing("user_attributions", sa.Column("first_ad_id", sa.String(length=120), nullable=True))
        _add_column_if_missing(
            "user_attributions",
            sa.Column("first_creative_id", sa.String(length=120), nullable=True),
        )
        _add_column_if_missing("user_attributions", sa.Column("last_ad_id", sa.String(length=120), nullable=True))
        _add_column_if_missing("user_attributions", sa.Column("last_creative_id", sa.String(length=120), nullable=True))
        if not _has_index("user_attributions", "ix_user_attributions_first_ad_id"):
            op.create_index("ix_user_attributions_first_ad_id", "user_attributions", ["first_ad_id"])
        if not _has_index("user_attributions", "ix_user_attributions_first_creative_id"):
            op.create_index("ix_user_attributions_first_creative_id", "user_attributions", ["first_creative_id"])
        if not _has_index("user_attributions", "ix_user_attributions_last_ad_id"):
            op.create_index("ix_user_attributions_last_ad_id", "user_attributions", ["last_ad_id"])
        if not _has_index("user_attributions", "ix_user_attributions_last_creative_id"):
            op.create_index("ix_user_attributions_last_creative_id", "user_attributions", ["last_creative_id"])

    if not _has_table("channel_spend_entries"):
        op.create_table(
            "channel_spend_entries",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("spend_day", sa.Date(), nullable=False),
            sa.Column("source", sa.String(length=120), nullable=False),
            sa.Column("medium", sa.String(length=120), nullable=True),
            sa.Column("campaign", sa.String(length=160), nullable=True),
            sa.Column("ad_id", sa.String(length=120), nullable=True),
            sa.Column("creative_id", sa.String(length=120), nullable=True),
            sa.Column("cost_usd_cents", sa.Integer(), nullable=False),
            sa.Column("clicks", sa.Integer(), nullable=False),
            sa.Column("impressions", sa.Integer(), nullable=False),
            sa.Column("dedupe_key", sa.String(length=220), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("dedupe_key", name="uq_channel_spend_entries_dedupe_key"),
        )
        op.create_index("ix_channel_spend_entries_spend_day", "channel_spend_entries", ["spend_day"])
        op.create_index("ix_channel_spend_entries_source", "channel_spend_entries", ["source"])
        op.create_index("ix_channel_spend_entries_campaign", "channel_spend_entries", ["campaign"])
        op.create_index("ix_channel_spend_entries_ad_id", "channel_spend_entries", ["ad_id"])
        op.create_index("ix_channel_spend_entries_creative_id", "channel_spend_entries", ["creative_id"])
        op.create_index("ix_channel_spend_entries_dedupe_key", "channel_spend_entries", ["dedupe_key"], unique=True)


def downgrade() -> None:
    if _has_table("channel_spend_entries"):
        if _has_index("channel_spend_entries", "ix_channel_spend_entries_dedupe_key"):
            op.drop_index("ix_channel_spend_entries_dedupe_key", table_name="channel_spend_entries")
        if _has_index("channel_spend_entries", "ix_channel_spend_entries_creative_id"):
            op.drop_index("ix_channel_spend_entries_creative_id", table_name="channel_spend_entries")
        if _has_index("channel_spend_entries", "ix_channel_spend_entries_ad_id"):
            op.drop_index("ix_channel_spend_entries_ad_id", table_name="channel_spend_entries")
        if _has_index("channel_spend_entries", "ix_channel_spend_entries_campaign"):
            op.drop_index("ix_channel_spend_entries_campaign", table_name="channel_spend_entries")
        if _has_index("channel_spend_entries", "ix_channel_spend_entries_source"):
            op.drop_index("ix_channel_spend_entries_source", table_name="channel_spend_entries")
        if _has_index("channel_spend_entries", "ix_channel_spend_entries_spend_day"):
            op.drop_index("ix_channel_spend_entries_spend_day", table_name="channel_spend_entries")
        op.drop_table("channel_spend_entries")

    if _has_table("user_attributions"):
        if _has_index("user_attributions", "ix_user_attributions_last_creative_id"):
            op.drop_index("ix_user_attributions_last_creative_id", table_name="user_attributions")
        if _has_index("user_attributions", "ix_user_attributions_last_ad_id"):
            op.drop_index("ix_user_attributions_last_ad_id", table_name="user_attributions")
        if _has_index("user_attributions", "ix_user_attributions_first_creative_id"):
            op.drop_index("ix_user_attributions_first_creative_id", table_name="user_attributions")
        if _has_index("user_attributions", "ix_user_attributions_first_ad_id"):
            op.drop_index("ix_user_attributions_first_ad_id", table_name="user_attributions")
        if _has_column("user_attributions", "last_creative_id"):
            op.drop_column("user_attributions", "last_creative_id")
        if _has_column("user_attributions", "last_ad_id"):
            op.drop_column("user_attributions", "last_ad_id")
        if _has_column("user_attributions", "first_creative_id"):
            op.drop_column("user_attributions", "first_creative_id")
        if _has_column("user_attributions", "first_ad_id"):
            op.drop_column("user_attributions", "first_ad_id")

    if _has_table("session_attributions"):
        if _has_index("session_attributions", "ix_session_attributions_last_creative_id"):
            op.drop_index("ix_session_attributions_last_creative_id", table_name="session_attributions")
        if _has_index("session_attributions", "ix_session_attributions_last_ad_id"):
            op.drop_index("ix_session_attributions_last_ad_id", table_name="session_attributions")
        if _has_index("session_attributions", "ix_session_attributions_first_creative_id"):
            op.drop_index("ix_session_attributions_first_creative_id", table_name="session_attributions")
        if _has_index("session_attributions", "ix_session_attributions_first_ad_id"):
            op.drop_index("ix_session_attributions_first_ad_id", table_name="session_attributions")
        if _has_column("session_attributions", "last_creative_id"):
            op.drop_column("session_attributions", "last_creative_id")
        if _has_column("session_attributions", "last_ad_id"):
            op.drop_column("session_attributions", "last_ad_id")
        if _has_column("session_attributions", "first_creative_id"):
            op.drop_column("session_attributions", "first_creative_id")
        if _has_column("session_attributions", "first_ad_id"):
            op.drop_column("session_attributions", "first_ad_id")

    if _has_table("analytics_events"):
        if _has_index("analytics_events", "ix_analytics_events_creative_id"):
            op.drop_index("ix_analytics_events_creative_id", table_name="analytics_events")
        if _has_index("analytics_events", "ix_analytics_events_ad_id"):
            op.drop_index("ix_analytics_events_ad_id", table_name="analytics_events")
        if _has_column("analytics_events", "creative_id"):
            op.drop_column("analytics_events", "creative_id")
        if _has_column("analytics_events", "ad_id"):
            op.drop_column("analytics_events", "ad_id")


"""phase8 analytics events

Revision ID: 20260324_0009
Revises: 20260324_0008
Create Date: 2026-03-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260324_0009"
down_revision: str | None = "20260324_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "analytics_events" not in tables:
        op.create_table(
            "analytics_events",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("event_id", sa.String(length=80), nullable=False),
            sa.Column("event_name", sa.String(length=80), nullable=False),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("session_id", sa.String(length=120), nullable=False),
            sa.Column("source", sa.String(length=40), nullable=False, server_default="web"),
            sa.Column("context_page", sa.String(length=260), nullable=False),
            sa.Column("context_feature", sa.String(length=120), nullable=False),
            sa.Column("utm_source", sa.String(length=120), nullable=True),
            sa.Column("utm_medium", sa.String(length=120), nullable=True),
            sa.Column("utm_campaign", sa.String(length=160), nullable=True),
            sa.Column("utm_term", sa.String(length=160), nullable=True),
            sa.Column("utm_content", sa.String(length=160), nullable=True),
            sa.Column("referrer", sa.String(length=500), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("event_id", name="uq_analytics_events_event_id"),
        )
        op.create_index("ix_analytics_events_event_id", "analytics_events", ["event_id"], unique=True)
        op.create_index("ix_analytics_events_event_name", "analytics_events", ["event_name"], unique=False)
        op.create_index("ix_analytics_events_user_id", "analytics_events", ["user_id"], unique=False)
        op.create_index("ix_analytics_events_session_id", "analytics_events", ["session_id"], unique=False)
        op.create_index("ix_analytics_events_source", "analytics_events", ["source"], unique=False)
        op.create_index("ix_analytics_events_context_page", "analytics_events", ["context_page"], unique=False)
        op.create_index("ix_analytics_events_context_feature", "analytics_events", ["context_feature"], unique=False)
        op.create_index("ix_analytics_events_utm_source", "analytics_events", ["utm_source"], unique=False)
        op.create_index("ix_analytics_events_occurred_at", "analytics_events", ["occurred_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "analytics_events" in tables:
        op.drop_index("ix_analytics_events_occurred_at", table_name="analytics_events")
        op.drop_index("ix_analytics_events_utm_source", table_name="analytics_events")
        op.drop_index("ix_analytics_events_context_feature", table_name="analytics_events")
        op.drop_index("ix_analytics_events_context_page", table_name="analytics_events")
        op.drop_index("ix_analytics_events_source", table_name="analytics_events")
        op.drop_index("ix_analytics_events_session_id", table_name="analytics_events")
        op.drop_index("ix_analytics_events_user_id", table_name="analytics_events")
        op.drop_index("ix_analytics_events_event_name", table_name="analytics_events")
        op.drop_index("ix_analytics_events_event_id", table_name="analytics_events")
        op.drop_table("analytics_events")

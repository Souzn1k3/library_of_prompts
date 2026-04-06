"""revenue_operating_system

Revision ID: 20260406_0027
Revises: 20260406_0026
Create Date: 2026-04-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260406_0027"
down_revision = "20260406_0026"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if not _has_table("session_attributions"):
        op.create_table(
            "session_attributions",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("session_id", sa.String(length=120), nullable=False),
            sa.Column("linked_user_id", sa.Uuid(), nullable=True),
            sa.Column("first_utm_source", sa.String(length=120), nullable=True),
            sa.Column("first_utm_medium", sa.String(length=120), nullable=True),
            sa.Column("first_utm_campaign", sa.String(length=160), nullable=True),
            sa.Column("first_referrer", sa.String(length=500), nullable=True),
            sa.Column("last_utm_source", sa.String(length=120), nullable=True),
            sa.Column("last_utm_medium", sa.String(length=120), nullable=True),
            sa.Column("last_utm_campaign", sa.String(length=160), nullable=True),
            sa.Column("last_referrer", sa.String(length=500), nullable=True),
            sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["linked_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_id", name="uq_session_attributions_session_id"),
        )
        op.create_index("ix_session_attributions_session_id", "session_attributions", ["session_id"], unique=True)
        op.create_index("ix_session_attributions_linked_user_id", "session_attributions", ["linked_user_id"])
        op.create_index("ix_session_attributions_first_utm_source", "session_attributions", ["first_utm_source"])
        op.create_index("ix_session_attributions_last_utm_source", "session_attributions", ["last_utm_source"])

    if not _has_table("user_attributions"):
        op.create_table(
            "user_attributions",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("first_session_id", sa.String(length=120), nullable=True),
            sa.Column("last_session_id", sa.String(length=120), nullable=True),
            sa.Column("first_utm_source", sa.String(length=120), nullable=True),
            sa.Column("first_utm_medium", sa.String(length=120), nullable=True),
            sa.Column("first_utm_campaign", sa.String(length=160), nullable=True),
            sa.Column("first_referrer", sa.String(length=500), nullable=True),
            sa.Column("last_utm_source", sa.String(length=120), nullable=True),
            sa.Column("last_utm_medium", sa.String(length=120), nullable=True),
            sa.Column("last_utm_campaign", sa.String(length=160), nullable=True),
            sa.Column("last_referrer", sa.String(length=500), nullable=True),
            sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", name="uq_user_attributions_user_id"),
        )
        op.create_index("ix_user_attributions_user_id", "user_attributions", ["user_id"], unique=True)
        op.create_index("ix_user_attributions_first_utm_source", "user_attributions", ["first_utm_source"])
        op.create_index("ix_user_attributions_last_utm_source", "user_attributions", ["last_utm_source"])


def downgrade() -> None:
    if _has_table("user_attributions"):
        if _has_index("user_attributions", "ix_user_attributions_last_utm_source"):
            op.drop_index("ix_user_attributions_last_utm_source", table_name="user_attributions")
        if _has_index("user_attributions", "ix_user_attributions_first_utm_source"):
            op.drop_index("ix_user_attributions_first_utm_source", table_name="user_attributions")
        if _has_index("user_attributions", "ix_user_attributions_user_id"):
            op.drop_index("ix_user_attributions_user_id", table_name="user_attributions")
        op.drop_table("user_attributions")

    if _has_table("session_attributions"):
        if _has_index("session_attributions", "ix_session_attributions_last_utm_source"):
            op.drop_index("ix_session_attributions_last_utm_source", table_name="session_attributions")
        if _has_index("session_attributions", "ix_session_attributions_first_utm_source"):
            op.drop_index("ix_session_attributions_first_utm_source", table_name="session_attributions")
        if _has_index("session_attributions", "ix_session_attributions_linked_user_id"):
            op.drop_index("ix_session_attributions_linked_user_id", table_name="session_attributions")
        if _has_index("session_attributions", "ix_session_attributions_session_id"):
            op.drop_index("ix_session_attributions_session_id", table_name="session_attributions")
        op.drop_table("session_attributions")


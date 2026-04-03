"""phase3 onboarding profile and events

Revision ID: 20260324_0005
Revises: 20260324_0004
Create Date: 2026-03-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260324_0005"
down_revision: str | None = "20260324_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "onboarding_profiles" not in tables:
        op.create_table(
            "onboarding_profiles",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("role", sa.String(length=32), nullable=True),
            sa.Column("goal", sa.String(length=32), nullable=True),
            sa.Column("ai_context", sa.String(length=120), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("skipped_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "first_win_prompt_id",
                sa.Uuid(),
                sa.ForeignKey("prompts.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("first_win_completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_onboarding_profiles_user_id",
            "onboarding_profiles",
            ["user_id"],
            unique=True,
        )

    if "onboarding_events" not in tables:
        op.create_table(
            "onboarding_events",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("event_name", sa.String(length=120), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_onboarding_events_user_id", "onboarding_events", ["user_id"], unique=False)
        op.create_index(
            "ix_onboarding_events_event_name",
            "onboarding_events",
            ["event_name"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "onboarding_events" in tables:
        op.drop_index("ix_onboarding_events_event_name", table_name="onboarding_events")
        op.drop_index("ix_onboarding_events_user_id", table_name="onboarding_events")
        op.drop_table("onboarding_events")

    if "onboarding_profiles" in tables:
        op.drop_index("ix_onboarding_profiles_user_id", table_name="onboarding_profiles")
        op.drop_table("onboarding_profiles")

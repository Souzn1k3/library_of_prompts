"""phase5 tiers premium lessons

Revision ID: 20250321_0003
Revises: 20250321_0002
Create Date: 2025-03-21

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20250321_0003"
down_revision: str | None = "20250321_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 0001 create_all may already include phase-5 columns and lessons; skip if present.
    bind = op.get_bind()
    insp = sa.inspect(bind)
    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "plan_tier" not in user_cols:
        op.add_column(
            "users",
            sa.Column("plan_tier", sa.String(length=32), server_default="free", nullable=False),
        )
    prompt_cols = {c["name"] for c in insp.get_columns("prompts")}
    if "is_premium" not in prompt_cols:
        op.add_column(
            "prompts",
            sa.Column("is_premium", sa.Boolean(), server_default=sa.false(), nullable=False),
        )
    if "moderation_notes" not in prompt_cols:
        op.add_column("prompts", sa.Column("moderation_notes", sa.Text(), nullable=True))
    if "lessons" not in insp.get_table_names():
        op.create_table(
            "lessons",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("slug", sa.String(length=200), nullable=False),
            sa.Column("title", sa.String(length=300), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column(
                "min_tier",
                sa.String(length=32),
                server_default="free",
                nullable=False,
            ),
            sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_lessons_slug", "lessons", ["slug"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    prompt_cols = {c["name"] for c in insp.get_columns("prompts")}
    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "lessons" in insp.get_table_names():
        op.drop_index("ix_lessons_slug", table_name="lessons")
        op.drop_table("lessons")
    if "moderation_notes" in prompt_cols:
        op.drop_column("prompts", "moderation_notes")
    if "is_premium" in prompt_cols:
        op.drop_column("prompts", "is_premium")
    if "plan_tier" in user_cols:
        op.drop_column("users", "plan_tier")

"""saved_prompts table

Revision ID: 20250321_0002
Revises: 20250321_0001
Create Date: 2025-03-21

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20250321_0002"
down_revision: str | None = "20250321_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 0001 uses create_all() with current models, so saved_prompts may already exist.
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "saved_prompts" in insp.get_table_names():
        return
    op.create_table(
        "saved_prompts",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "prompt_id",
            sa.Uuid(),
            sa.ForeignKey("prompts.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("saved_prompts")

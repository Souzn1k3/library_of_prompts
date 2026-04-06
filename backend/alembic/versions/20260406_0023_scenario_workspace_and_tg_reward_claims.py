"""scenario_workspace_and_tg_reward_claims

Revision ID: 20260406_0023
Revises: 20260404_0022
Create Date: 2026-04-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260406_0023"
down_revision = "20260404_0022"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("user_scenario_workspace"):
        op.create_table(
            "user_scenario_workspace",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("prompt_id", sa.Uuid(), nullable=False),
            sa.Column("is_saved", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("unfinished_task", sa.Text(), nullable=True),
            sa.Column("run_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("copy_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("share_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_copied_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_shared_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "prompt_id", name="uq_user_scenario_workspace_user_prompt"),
        )
        op.create_index("ix_user_scenario_workspace_user_id", "user_scenario_workspace", ["user_id"])
        op.create_index("ix_user_scenario_workspace_prompt_id", "user_scenario_workspace", ["prompt_id"])
        op.create_index("ix_user_scenario_workspace_last_used_at", "user_scenario_workspace", ["last_used_at"])

    if not _has_table("telegram_reward_claims"):
        op.create_table(
            "telegram_reward_claims",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("claim_id", sa.String(length=120), nullable=False),
            sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=True),
            sa.Column("reward_tokens", sa.Integer(), nullable=False),
            sa.Column("reason", sa.String(length=200), nullable=False),
            sa.Column("challenge_key", sa.String(length=120), nullable=True),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("signature", sa.String(length=128), nullable=False),
            sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("verification_error", sa.String(length=300), nullable=True),
            sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_telegram_reward_claims_claim_id", "telegram_reward_claims", ["claim_id"], unique=True)
        op.create_index("ix_telegram_reward_claims_telegram_user_id", "telegram_reward_claims", ["telegram_user_id"])
        op.create_index("ix_telegram_reward_claims_user_id", "telegram_reward_claims", ["user_id"])
        op.create_index("ix_telegram_reward_claims_verified", "telegram_reward_claims", ["verified"])


def downgrade() -> None:
    if _has_table("telegram_reward_claims"):
        op.drop_index("ix_telegram_reward_claims_verified", table_name="telegram_reward_claims")
        op.drop_index("ix_telegram_reward_claims_user_id", table_name="telegram_reward_claims")
        op.drop_index("ix_telegram_reward_claims_telegram_user_id", table_name="telegram_reward_claims")
        op.drop_index("ix_telegram_reward_claims_claim_id", table_name="telegram_reward_claims")
        op.drop_table("telegram_reward_claims")

    if _has_table("user_scenario_workspace"):
        op.drop_index("ix_user_scenario_workspace_last_used_at", table_name="user_scenario_workspace")
        op.drop_index("ix_user_scenario_workspace_prompt_id", table_name="user_scenario_workspace")
        op.drop_index("ix_user_scenario_workspace_user_id", table_name="user_scenario_workspace")
        op.drop_table("user_scenario_workspace")

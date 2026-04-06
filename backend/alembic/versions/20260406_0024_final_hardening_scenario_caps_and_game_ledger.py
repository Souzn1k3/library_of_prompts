"""final_hardening_scenario_caps_and_game_ledger

Revision ID: 20260406_0024
Revises: 20260406_0023
Create Date: 2026-04-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260406_0024"
down_revision = "20260406_0023"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("guest_scenario_run_usage"):
        op.create_table(
            "guest_scenario_run_usage",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("guest_id", sa.String(length=80), nullable=False),
            sa.Column("prompt_id", sa.Uuid(), nullable=False),
            sa.Column("run_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_ip_hash", sa.String(length=64), nullable=True),
            sa.Column("last_user_agent_hash", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("guest_id", "prompt_id", name="uq_guest_scenario_run_usage_guest_prompt"),
        )
        op.create_index("ix_guest_scenario_run_usage_guest_id", "guest_scenario_run_usage", ["guest_id"])
        op.create_index("ix_guest_scenario_run_usage_prompt_id", "guest_scenario_run_usage", ["prompt_id"])
        op.create_index("ix_guest_scenario_run_usage_last_run_at", "guest_scenario_run_usage", ["last_run_at"])
        op.create_index("ix_guest_scenario_run_usage_last_ip_hash", "guest_scenario_run_usage", ["last_ip_hash"])

    if not _has_table("scenario_game_token_events"):
        op.create_table(
            "scenario_game_token_events",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("event_id", sa.String(length=120), nullable=False),
            sa.Column("source", sa.String(length=40), nullable=False, server_default="web_demo"),
            sa.Column("user_id", sa.Uuid(), nullable=True),
            sa.Column("guest_id", sa.String(length=80), nullable=True),
            sa.Column("challenge_id", sa.String(length=80), nullable=False),
            sa.Column("choice_index", sa.Integer(), nullable=False),
            sa.Column("reward_tokens", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
            sa.Column("rejection_reason", sa.String(length=120), nullable=True),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("claim_id", sa.String(length=120), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_scenario_game_token_events_event_id", "scenario_game_token_events", ["event_id"], unique=True)
        op.create_index("ix_scenario_game_token_events_source", "scenario_game_token_events", ["source"])
        op.create_index("ix_scenario_game_token_events_user_id", "scenario_game_token_events", ["user_id"])
        op.create_index("ix_scenario_game_token_events_guest_id", "scenario_game_token_events", ["guest_id"])
        op.create_index("ix_scenario_game_token_events_challenge_id", "scenario_game_token_events", ["challenge_id"])
        op.create_index("ix_scenario_game_token_events_status", "scenario_game_token_events", ["status"])
        op.create_index("ix_scenario_game_token_events_claim_id", "scenario_game_token_events", ["claim_id"])

    if not _has_table("scenario_game_token_claims"):
        op.create_table(
            "scenario_game_token_claims",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("claim_id", sa.String(length=120), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("guest_id", sa.String(length=80), nullable=True),
            sa.Column("source", sa.String(length=40), nullable=False, server_default="web_demo"),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="completed"),
            sa.Column("claimed_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("pending_tokens_after", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("balance_after", sa.Integer(), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_scenario_game_token_claims_claim_id", "scenario_game_token_claims", ["claim_id"], unique=True)
        op.create_index("ix_scenario_game_token_claims_user_id", "scenario_game_token_claims", ["user_id"])
        op.create_index("ix_scenario_game_token_claims_guest_id", "scenario_game_token_claims", ["guest_id"])
        op.create_index("ix_scenario_game_token_claims_source", "scenario_game_token_claims", ["source"])
        op.create_index("ix_scenario_game_token_claims_status", "scenario_game_token_claims", ["status"])


def downgrade() -> None:
    if _has_table("scenario_game_token_claims"):
        op.drop_index("ix_scenario_game_token_claims_status", table_name="scenario_game_token_claims")
        op.drop_index("ix_scenario_game_token_claims_source", table_name="scenario_game_token_claims")
        op.drop_index("ix_scenario_game_token_claims_guest_id", table_name="scenario_game_token_claims")
        op.drop_index("ix_scenario_game_token_claims_user_id", table_name="scenario_game_token_claims")
        op.drop_index("ix_scenario_game_token_claims_claim_id", table_name="scenario_game_token_claims")
        op.drop_table("scenario_game_token_claims")

    if _has_table("scenario_game_token_events"):
        op.drop_index("ix_scenario_game_token_events_claim_id", table_name="scenario_game_token_events")
        op.drop_index("ix_scenario_game_token_events_status", table_name="scenario_game_token_events")
        op.drop_index("ix_scenario_game_token_events_challenge_id", table_name="scenario_game_token_events")
        op.drop_index("ix_scenario_game_token_events_guest_id", table_name="scenario_game_token_events")
        op.drop_index("ix_scenario_game_token_events_user_id", table_name="scenario_game_token_events")
        op.drop_index("ix_scenario_game_token_events_source", table_name="scenario_game_token_events")
        op.drop_index("ix_scenario_game_token_events_event_id", table_name="scenario_game_token_events")
        op.drop_table("scenario_game_token_events")

    if _has_table("guest_scenario_run_usage"):
        op.drop_index("ix_guest_scenario_run_usage_last_ip_hash", table_name="guest_scenario_run_usage")
        op.drop_index("ix_guest_scenario_run_usage_last_run_at", table_name="guest_scenario_run_usage")
        op.drop_index("ix_guest_scenario_run_usage_prompt_id", table_name="guest_scenario_run_usage")
        op.drop_index("ix_guest_scenario_run_usage_guest_id", table_name="guest_scenario_run_usage")
        op.drop_table("guest_scenario_run_usage")

"""economy_loop_v2_guardrails

Revision ID: 20260331_0019
Revises: 20260331_0018
Create Date: 2026-03-31
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
import uuid

import sqlalchemy as sa
from alembic import op


revision: str = "20260331_0019"
down_revision: str | None = "20260331_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "user_currency_balances" in tables:
        cols = _column_names(inspector, "user_currency_balances")
        if "catchup_boost_pct" not in cols:
            op.add_column(
                "user_currency_balances",
                sa.Column("catchup_boost_pct", sa.Integer(), nullable=False, server_default="0"),
            )
            op.alter_column("user_currency_balances", "catchup_boost_pct", server_default=None)
        if "catchup_boost_expires_at" not in cols:
            op.add_column(
                "user_currency_balances",
                sa.Column("catchup_boost_expires_at", sa.DateTime(timezone=True), nullable=True),
            )

    if "lesson_missions" in tables:
        mission_exists = bind.execute(
            sa.text("SELECT id FROM lesson_missions WHERE slug = :slug"),
            {"slug": "streak-recovery-window"},
        ).scalar_one_or_none()
        if mission_exists is None:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO lesson_missions (
                        id,
                        slug,
                        title,
                        description,
                        objective,
                        completion_condition,
                        action_type,
                        difficulty,
                        mission_type,
                        required_count,
                        is_repeatable,
                        repeat_interval_days,
                        chain_id,
                        chain_step,
                        chain_total,
                        chain_bonus_credits,
                        adaptive_segment,
                        reward_badge,
                        reward_credits,
                        reward_premium_days,
                        is_active,
                        sort_order,
                        created_at,
                        updated_at
                    ) VALUES (
                        :id,
                        :slug,
                        :title,
                        :description,
                        :objective,
                        :completion_condition,
                        :action_type,
                        :difficulty,
                        :mission_type,
                        :required_count,
                        :is_repeatable,
                        :repeat_interval_days,
                        :chain_id,
                        :chain_step,
                        :chain_total,
                        :chain_bonus_credits,
                        :adaptive_segment,
                        :reward_badge,
                        :reward_credits,
                        :reward_premium_days,
                        :is_active,
                        :sort_order,
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "slug": "streak-recovery-window",
                    "title": "Streak recovery window",
                    "description": "Complete this high-value mission before reset to preserve your streak.",
                    "objective": "Recover today's streak before day end.",
                    "completion_condition": "Confirm one recovery action before reset.",
                    "action_type": "manual_confirmation",
                    "difficulty": "standard",
                    "mission_type": "habit",
                    "required_count": 1,
                    "is_repeatable": True,
                    "repeat_interval_days": 1,
                    "chain_id": "streak_recovery",
                    "chain_step": 1,
                    "chain_total": 1,
                    "chain_bonus_credits": 8,
                    "adaptive_segment": "balanced",
                    "reward_badge": "streak-saver",
                    "reward_credits": 12,
                    "reward_premium_days": 0,
                    "is_active": True,
                    "sort_order": 8,
                    "created_at": _utcnow(),
                    "updated_at": _utcnow(),
                },
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "lesson_missions" in tables:
        bind.execute(sa.text("DELETE FROM lesson_missions WHERE slug = 'streak-recovery-window'"))

    if "user_currency_balances" in tables:
        cols = _column_names(inspector, "user_currency_balances")
        for col in ("catchup_boost_expires_at", "catchup_boost_pct"):
            if col in cols:
                op.drop_column("user_currency_balances", col)


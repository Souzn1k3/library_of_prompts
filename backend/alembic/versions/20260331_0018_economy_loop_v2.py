"""economy_loop_v2

Revision ID: 20260331_0018
Revises: 20260330_0017
Create Date: 2026-03-31
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
import uuid

import sqlalchemy as sa
from alembic import op


revision: str = "20260331_0018"
down_revision: str | None = "20260330_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "user_currency_balances" in tables:
        wallet_cols = _column_names(inspector, "user_currency_balances")
        if "spend_streak_days" not in wallet_cols:
            op.add_column(
                "user_currency_balances",
                sa.Column("spend_streak_days", sa.Integer(), nullable=False, server_default="0"),
            )
            op.alter_column("user_currency_balances", "spend_streak_days", server_default=None)
        if "last_spend_at" not in wallet_cols:
            op.add_column(
                "user_currency_balances",
                sa.Column("last_spend_at", sa.DateTime(timezone=True), nullable=True),
            )
        if "streak_freeze_tokens" not in wallet_cols:
            op.add_column(
                "user_currency_balances",
                sa.Column("streak_freeze_tokens", sa.Integer(), nullable=False, server_default="0"),
            )
            op.alter_column("user_currency_balances", "streak_freeze_tokens", server_default=None)
        if "surprise_miss_streak" not in wallet_cols:
            op.add_column(
                "user_currency_balances",
                sa.Column("surprise_miss_streak", sa.Integer(), nullable=False, server_default="0"),
            )
            op.alter_column("user_currency_balances", "surprise_miss_streak", server_default=None)
        if "rank_points" not in wallet_cols:
            op.add_column(
                "user_currency_balances",
                sa.Column("rank_points", sa.Integer(), nullable=False, server_default="0"),
            )
            op.alter_column("user_currency_balances", "rank_points", server_default=None)
        if "rank_level" not in wallet_cols:
            op.add_column(
                "user_currency_balances",
                sa.Column("rank_level", sa.Integer(), nullable=False, server_default="1"),
            )
            op.alter_column("user_currency_balances", "rank_level", server_default=None)
        if "owned_value_generated" not in wallet_cols:
            op.add_column(
                "user_currency_balances",
                sa.Column("owned_value_generated", sa.Integer(), nullable=False, server_default="0"),
            )
            op.alter_column("user_currency_balances", "owned_value_generated", server_default=None)
        if "second_purchase_challenge_started_at" not in wallet_cols:
            op.add_column(
                "user_currency_balances",
                sa.Column("second_purchase_challenge_started_at", sa.DateTime(timezone=True), nullable=True),
            )
        if "second_purchase_challenge_expires_at" not in wallet_cols:
            op.add_column(
                "user_currency_balances",
                sa.Column("second_purchase_challenge_expires_at", sa.DateTime(timezone=True), nullable=True),
            )
        if "second_purchase_challenge_completed_at" not in wallet_cols:
            op.add_column(
                "user_currency_balances",
                sa.Column("second_purchase_challenge_completed_at", sa.DateTime(timezone=True), nullable=True),
            )

    if "user_locked_rewards" not in tables:
        op.create_table(
            "user_locked_rewards",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("source_purchase_id", sa.Uuid(as_uuid=True), sa.ForeignKey("user_purchases.id", ondelete="SET NULL"), nullable=True),
            sa.Column("amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("required_mission_count", sa.Integer(), nullable=False, server_default="2"),
            sa.Column("completed_mission_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
            sa.Column("unlock_by", sa.DateTime(timezone=True), nullable=True),
            sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_user_locked_rewards_user_id", "user_locked_rewards", ["user_id"])
        op.create_index("ix_user_locked_rewards_status", "user_locked_rewards", ["status"])
        op.create_index("ix_user_locked_rewards_unlock_by", "user_locked_rewards", ["unlock_by"])
        op.create_index("ix_user_locked_rewards_source_purchase_id", "user_locked_rewards", ["source_purchase_id"])

    if "user_active_boosts" not in tables:
        op.create_table(
            "user_active_boosts",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("source_purchase_id", sa.Uuid(as_uuid=True), sa.ForeignKey("user_purchases.id", ondelete="SET NULL"), nullable=True),
            sa.Column("boost_percent", sa.Integer(), nullable=False, server_default="20"),
            sa.Column("missions_total", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("missions_used", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_user_active_boosts_user_id", "user_active_boosts", ["user_id"])
        op.create_index("ix_user_active_boosts_status", "user_active_boosts", ["status"])
        op.create_index("ix_user_active_boosts_expires_at", "user_active_boosts", ["expires_at"])
        op.create_index("ix_user_active_boosts_source_purchase_id", "user_active_boosts", ["source_purchase_id"])

    if "lesson_missions" in tables:
        mission_cols = _column_names(inspector, "lesson_missions")
        mission_indexes = _index_names(inspector, "lesson_missions")

        if "chain_id" not in mission_cols:
            op.add_column("lesson_missions", sa.Column("chain_id", sa.String(length=120), nullable=True))
        if "chain_step" not in mission_cols:
            op.add_column(
                "lesson_missions",
                sa.Column("chain_step", sa.Integer(), nullable=False, server_default="0"),
            )
            op.alter_column("lesson_missions", "chain_step", server_default=None)
        if "chain_total" not in mission_cols:
            op.add_column(
                "lesson_missions",
                sa.Column("chain_total", sa.Integer(), nullable=False, server_default="0"),
            )
            op.alter_column("lesson_missions", "chain_total", server_default=None)
        if "chain_bonus_credits" not in mission_cols:
            op.add_column(
                "lesson_missions",
                sa.Column("chain_bonus_credits", sa.Integer(), nullable=False, server_default="0"),
            )
            op.alter_column("lesson_missions", "chain_bonus_credits", server_default=None)
        if "chain_unlock_on_slug" not in mission_cols:
            op.add_column("lesson_missions", sa.Column("chain_unlock_on_slug", sa.String(length=120), nullable=True))
        if "adaptive_segment" not in mission_cols:
            op.add_column("lesson_missions", sa.Column("adaptive_segment", sa.String(length=24), nullable=True))

        if "ix_lesson_missions_chain_id" not in mission_indexes:
            op.create_index("ix_lesson_missions_chain_id", "lesson_missions", ["chain_id"])
        if "ix_lesson_missions_adaptive_segment" not in mission_indexes:
            op.create_index("ix_lesson_missions_adaptive_segment", "lesson_missions", ["adaptive_segment"])

        bind.execute(
            sa.text(
                """
                UPDATE lesson_missions
                SET mission_type = CASE
                    WHEN action_type IN ('daily_checkin', 'streak_activity') THEN 'habit'
                    WHEN action_type = 'multi_step' THEN 'progress'
                    WHEN action_type = 'challenge_submission' THEN 'progress'
                    ELSE mission_type
                END
                """
            )
        )

        # Seed chain metadata for existing missions.
        bind.execute(
            sa.text(
                """
                UPDATE lesson_missions
                SET chain_id = 'habit_chain',
                    chain_step = 1,
                    chain_total = 2,
                    chain_bonus_credits = 2,
                    adaptive_segment = 'inactive'
                WHERE slug = 'daily-lumen-check-in'
                """
            )
        )
        bind.execute(
            sa.text(
                """
                UPDATE lesson_missions
                SET chain_id = 'habit_chain',
                    chain_step = 2,
                    chain_total = 2,
                    chain_bonus_credits = 5,
                    chain_unlock_on_slug = 'daily-lumen-check-in',
                    adaptive_segment = 'balanced'
                WHERE slug = 'three-day-practice-streak'
                """
            )
        )

        mission_exists = bind.execute(
            sa.text("SELECT id FROM lesson_missions WHERE slug = :slug"),
            {"slug": "second-purchase-sprint"},
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
                    "slug": "second-purchase-sprint",
                    "title": "Second purchase sprint",
                    "description": "Make a second store purchase in the same momentum window.",
                    "objective": "Complete two store purchases in 48 hours.",
                    "completion_condition": "Record one qualified store purchase event after your first buy.",
                    "action_type": "store_purchase",
                    "difficulty": "standard",
                    "mission_type": "spend_linked",
                    "required_count": 1,
                    "is_repeatable": True,
                    "repeat_interval_days": 7,
                    "chain_id": "spend_chain",
                    "chain_step": 1,
                    "chain_total": 1,
                    "chain_bonus_credits": 6,
                    "adaptive_segment": "hoarder",
                    "reward_badge": "spender-momentum",
                    "reward_credits": 8,
                    "reward_premium_days": 0,
                    "is_active": True,
                    "sort_order": 9,
                    "created_at": _utcnow(),
                    "updated_at": _utcnow(),
                },
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "lesson_missions" in tables:
        mission_cols = _column_names(inspector, "lesson_missions")
        mission_indexes = _index_names(inspector, "lesson_missions")
        bind.execute(sa.text("DELETE FROM lesson_missions WHERE slug = 'second-purchase-sprint'"))
        if "ix_lesson_missions_adaptive_segment" in mission_indexes:
            op.drop_index("ix_lesson_missions_adaptive_segment", table_name="lesson_missions")
        if "ix_lesson_missions_chain_id" in mission_indexes:
            op.drop_index("ix_lesson_missions_chain_id", table_name="lesson_missions")
        for column_name in [
            "adaptive_segment",
            "chain_unlock_on_slug",
            "chain_bonus_credits",
            "chain_total",
            "chain_step",
            "chain_id",
        ]:
            if column_name in mission_cols:
                op.drop_column("lesson_missions", column_name)

    if "user_active_boosts" in tables:
        op.drop_index("ix_user_active_boosts_source_purchase_id", table_name="user_active_boosts")
        op.drop_index("ix_user_active_boosts_expires_at", table_name="user_active_boosts")
        op.drop_index("ix_user_active_boosts_status", table_name="user_active_boosts")
        op.drop_index("ix_user_active_boosts_user_id", table_name="user_active_boosts")
        op.drop_table("user_active_boosts")

    if "user_locked_rewards" in tables:
        op.drop_index("ix_user_locked_rewards_source_purchase_id", table_name="user_locked_rewards")
        op.drop_index("ix_user_locked_rewards_unlock_by", table_name="user_locked_rewards")
        op.drop_index("ix_user_locked_rewards_status", table_name="user_locked_rewards")
        op.drop_index("ix_user_locked_rewards_user_id", table_name="user_locked_rewards")
        op.drop_table("user_locked_rewards")

    if "user_currency_balances" in tables:
        wallet_cols = _column_names(inspector, "user_currency_balances")
        for column_name in [
            "second_purchase_challenge_completed_at",
            "second_purchase_challenge_expires_at",
            "second_purchase_challenge_started_at",
            "owned_value_generated",
            "rank_level",
            "rank_points",
            "surprise_miss_streak",
            "streak_freeze_tokens",
            "last_spend_at",
            "spend_streak_days",
        ]:
            if column_name in wallet_cols:
                op.drop_column("user_currency_balances", column_name)

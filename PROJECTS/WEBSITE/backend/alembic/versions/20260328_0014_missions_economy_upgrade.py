"""missions_economy_upgrade

Revision ID: 20260328_0014
Revises: 20260328_0013
Create Date: 2026-03-28
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
import uuid

import sqlalchemy as sa
from alembic import op


revision: str = "20260328_0014"
down_revision: str | None = "20260328_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    lesson_cols = _column_names(inspector, "lesson_missions")
    lesson_indexes = _index_names(inspector, "lesson_missions")
    progress_cols = _column_names(inspector, "user_mission_progress")
    reward_cols = _column_names(inspector, "user_mission_reward_grants")
    wallet_cols = _column_names(inspector, "user_currency_balances")
    purchase_cols = _column_names(inspector, "user_purchases")
    purchase_indexes = _index_names(inspector, "user_purchases")
    reward_uniques = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("user_mission_reward_grants")
        if constraint.get("name")
    }

    if "mission_type" not in lesson_cols:
        op.add_column(
            "lesson_missions",
            sa.Column("mission_type", sa.String(length=24), nullable=False, server_default="action"),
        )
        op.alter_column("lesson_missions", "mission_type", server_default=None)
    if "ix_lesson_missions_mission_type" not in lesson_indexes:
        op.create_index("ix_lesson_missions_mission_type", "lesson_missions", ["mission_type"])

    if "is_repeatable" not in lesson_cols:
        op.add_column(
            "lesson_missions",
            sa.Column("is_repeatable", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        op.alter_column("lesson_missions", "is_repeatable", server_default=None)
    if "ix_lesson_missions_is_repeatable" not in lesson_indexes:
        op.create_index("ix_lesson_missions_is_repeatable", "lesson_missions", ["is_repeatable"])

    if "repeat_interval_days" not in lesson_cols:
        op.add_column(
            "lesson_missions",
            sa.Column("repeat_interval_days", sa.Integer(), nullable=False, server_default="0"),
        )
        op.alter_column("lesson_missions", "repeat_interval_days", server_default=None)

    if "completion_count" not in progress_cols:
        op.add_column(
            "user_mission_progress",
            sa.Column("completion_count", sa.Integer(), nullable=False, server_default="0"),
        )
        op.alter_column("user_mission_progress", "completion_count", server_default=None)

    if "reward_cycle" not in reward_cols:
        op.add_column(
            "user_mission_reward_grants",
            sa.Column("reward_cycle", sa.Integer(), nullable=False, server_default="1"),
        )
        op.alter_column("user_mission_reward_grants", "reward_cycle", server_default=None)

    if "current_streak" not in wallet_cols:
        op.add_column(
            "user_currency_balances",
            sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"),
        )
        op.alter_column("user_currency_balances", "current_streak", server_default=None)
    if "best_streak" not in wallet_cols:
        op.add_column(
            "user_currency_balances",
            sa.Column("best_streak", sa.Integer(), nullable=False, server_default="0"),
        )
        op.alter_column("user_currency_balances", "best_streak", server_default=None)
    if "last_check_in_at" not in wallet_cols:
        op.add_column(
            "user_currency_balances",
            sa.Column("last_check_in_at", sa.DateTime(timezone=True), nullable=True),
        )

    if "client_token" not in purchase_cols:
        op.add_column(
            "user_purchases",
            sa.Column("client_token", sa.String(length=80), nullable=True),
        )
    if "ix_user_purchases_client_token" not in purchase_indexes:
        op.create_index("ix_user_purchases_client_token", "user_purchases", ["client_token"], unique=True)

    bind.execute(
        sa.text(
            """
            UPDATE lesson_missions
            SET mission_type = CASE
                WHEN action_type = 'lesson_completed' THEN 'learning'
                WHEN action_type IN ('daily_checkin', 'streak_activity') THEN 'streak'
                WHEN action_type = 'challenge_submission' THEN 'challenge'
                WHEN action_type = 'multi_step' THEN 'progression'
                ELSE 'action'
            END
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE lesson_missions
            SET is_repeatable = CASE
                WHEN action_type IN ('daily_checkin', 'streak_activity', 'challenge_submission') THEN true
                ELSE coalesce(is_repeatable, false)
            END,
            repeat_interval_days = CASE
                WHEN action_type = 'daily_checkin' THEN 1
                WHEN action_type = 'streak_activity' THEN 3
                WHEN action_type = 'challenge_submission' THEN 7
                ELSE coalesce(repeat_interval_days, 0)
            END
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE user_mission_progress
            SET completion_count = CASE
                WHEN completed_at IS NOT NULL THEN 1
                ELSE coalesce(completion_count, 0)
            END
            """
        )
    )
    bind.execute(sa.text("UPDATE user_mission_reward_grants SET reward_cycle = coalesce(reward_cycle, 1)"))

    if "uq_user_mission_reward_grants_key" in reward_uniques:
        op.drop_constraint("uq_user_mission_reward_grants_key", "user_mission_reward_grants", type_="unique")
    reward_uniques = {
        constraint["name"]
        for constraint in sa.inspect(bind).get_unique_constraints("user_mission_reward_grants")
        if constraint.get("name")
    }
    if "uq_user_mission_reward_grants_key" not in reward_uniques:
        op.create_unique_constraint(
            "uq_user_mission_reward_grants_key",
            "user_mission_reward_grants",
            ["user_id", "mission_id", "reward_type", "reward_cycle"],
        )

    now = _utcnow()
    mission_rows = {
        row.slug: row.id
        for row in bind.execute(sa.text("SELECT id, slug FROM lesson_missions")).fetchall()
    }
    first_lesson_id = bind.execute(sa.text("SELECT id FROM lessons ORDER BY sort_order, title LIMIT 1")).scalar()
    first_prompt_id = bind.execute(
        sa.text(
            """
            SELECT id
            FROM prompts
            WHERE status = 'published'
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
    ).scalar()
    premium_prompts = bind.execute(
        sa.text(
            """
            SELECT id, slug, title
            FROM prompts
            WHERE status = 'published' AND is_premium = true
            ORDER BY created_at DESC
            LIMIT 3
            """
        )
    ).fetchall()

    mission_table = sa.table(
        "lesson_missions",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String(length=120)),
        sa.column("title", sa.String(length=220)),
        sa.column("description", sa.String(length=500)),
        sa.column("objective", sa.String(length=320)),
        sa.column("completion_condition", sa.String(length=320)),
        sa.column("action_type", sa.String(length=40)),
        sa.column("difficulty", sa.String(length=24)),
        sa.column("mission_type", sa.String(length=24)),
        sa.column("required_count", sa.Integer()),
        sa.column("is_repeatable", sa.Boolean()),
        sa.column("repeat_interval_days", sa.Integer()),
        sa.column("persona_role", sa.String(length=32)),
        sa.column("persona_goal", sa.String(length=32)),
        sa.column("lesson_id", sa.Uuid()),
        sa.column("reward_badge", sa.String(length=120)),
        sa.column("reward_credits", sa.Integer()),
        sa.column("reward_premium_days", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    defaults: list[dict[str, object]] = [
        {
            "slug": "daily-lumen-check-in",
            "title": "Daily AI check-in",
            "description": "Open the product, claim your daily check-in, and keep your learning loop alive.",
            "objective": "Return today and keep momentum going.",
            "completion_condition": "Claim one daily check-in.",
            "action_type": "daily_checkin",
            "difficulty": "easy",
            "mission_type": "streak",
            "required_count": 1,
            "is_repeatable": True,
            "repeat_interval_days": 1,
            "persona_role": None,
            "persona_goal": None,
            "lesson_id": None,
            "reward_badge": None,
            "reward_credits": 4,
            "reward_premium_days": 0,
            "is_active": True,
            "sort_order": 5,
        },
        {
            "slug": "three-day-practice-streak",
            "title": "Three-day practice streak",
            "description": "Use prompts, lessons, or missions across three days to build a real habit.",
            "objective": "Stay active for three separate days.",
            "completion_condition": "Trigger daily streak activity three times.",
            "action_type": "streak_activity",
            "difficulty": "standard",
            "mission_type": "streak",
            "required_count": 3,
            "is_repeatable": True,
            "repeat_interval_days": 3,
            "persona_role": None,
            "persona_goal": None,
            "lesson_id": None,
            "reward_badge": "practice-streak",
            "reward_credits": 12,
            "reward_premium_days": 0,
            "is_active": True,
            "sort_order": 6,
        },
        {
            "slug": "ship-a-real-ai-workflow",
            "title": "Ship a real AI workflow",
            "description": "Submit a practical prompt to turn your learning into reusable product value.",
            "objective": "Contribute one real prompt workflow.",
            "completion_condition": "Submit one prompt for review.",
            "action_type": "challenge_submission",
            "difficulty": "advanced",
            "mission_type": "challenge",
            "required_count": 1,
            "is_repeatable": True,
            "repeat_interval_days": 7,
            "persona_role": None,
            "persona_goal": "solving_tasks",
            "lesson_id": None,
            "reward_badge": "workflow-shipper",
            "reward_credits": 30,
            "reward_premium_days": 2,
            "is_active": True,
            "sort_order": 7,
        },
        {
            "slug": "build-your-ai-routine",
            "title": "Build your AI routine",
            "description": "Save, apply, and learn in one multi-step loop so the product becomes part of your workflow.",
            "objective": "Complete one full learning-to-usage cycle.",
            "completion_condition": "Finish all routine steps.",
            "action_type": "multi_step",
            "difficulty": "standard",
            "mission_type": "progression",
            "required_count": 3,
            "is_repeatable": False,
            "repeat_interval_days": 0,
            "persona_role": None,
            "persona_goal": None,
            "lesson_id": first_lesson_id,
            "reward_badge": "routine-builder",
            "reward_credits": 20,
            "reward_premium_days": 0,
            "is_active": True,
            "sort_order": 8,
        },
    ]

    rows_to_insert: list[dict[str, object]] = []
    for item in defaults:
        if item["slug"] in mission_rows:
            bind.execute(
                sa.text(
                    """
                    UPDATE lesson_missions
                    SET title = :title,
                        description = :description,
                        objective = :objective,
                        completion_condition = :completion_condition,
                        action_type = :action_type,
                        difficulty = :difficulty,
                        mission_type = :mission_type,
                        required_count = :required_count,
                        is_repeatable = :is_repeatable,
                        repeat_interval_days = :repeat_interval_days,
                        persona_role = :persona_role,
                        persona_goal = :persona_goal,
                        lesson_id = :lesson_id,
                        reward_badge = :reward_badge,
                        reward_credits = :reward_credits,
                        reward_premium_days = :reward_premium_days,
                        is_active = :is_active,
                        sort_order = :sort_order,
                        updated_at = :updated_at
                    WHERE slug = :slug
                    """
                ),
                {**item, "updated_at": now},
            )
            continue
        row_id = uuid.uuid4()
        mission_rows[str(item["slug"])] = row_id
        rows_to_insert.append(
            {
                "id": row_id,
                **item,
                "created_at": now,
                "updated_at": now,
            }
        )

    if rows_to_insert:
        op.bulk_insert(mission_table, rows_to_insert)

    routine_id = mission_rows.get("build-your-ai-routine")
    if routine_id is not None:
        step_count = bind.execute(
            sa.text("SELECT count(*) FROM mission_steps WHERE mission_id = :mission_id"),
            {"mission_id": routine_id},
        ).scalar()
        if int(step_count or 0) == 0:
            mission_steps = sa.table(
                "mission_steps",
                sa.column("id", sa.Uuid()),
                sa.column("mission_id", sa.Uuid()),
                sa.column("title", sa.String(length=200)),
                sa.column("description", sa.String(length=500)),
                sa.column("action_type", sa.String(length=40)),
                sa.column("required_count", sa.Integer()),
                sa.column("target_prompt_id", sa.Uuid()),
                sa.column("target_lesson_id", sa.Uuid()),
                sa.column("reward_credits", sa.Integer()),
                sa.column("sort_order", sa.Integer()),
                sa.column("created_at", sa.DateTime(timezone=True)),
            )
            op.bulk_insert(
                mission_steps,
                [
                    {
                        "id": uuid.uuid4(),
                        "mission_id": routine_id,
                        "title": "Save one prompt for later",
                        "description": "Pick a prompt you want to reuse and save it to your workspace.",
                        "action_type": "save_prompt",
                        "required_count": 1,
                        "target_prompt_id": first_prompt_id,
                        "target_lesson_id": None,
                        "reward_credits": 4,
                        "sort_order": 1,
                        "created_at": now,
                    },
                    {
                        "id": uuid.uuid4(),
                        "mission_id": routine_id,
                        "title": "Apply a prompt in a real task",
                        "description": "Use a prompt and confirm it produced a practical output.",
                        "action_type": "apply_prompt",
                        "required_count": 1,
                        "target_prompt_id": first_prompt_id,
                        "target_lesson_id": None,
                        "reward_credits": 6,
                        "sort_order": 2,
                        "created_at": now,
                    },
                    {
                        "id": uuid.uuid4(),
                        "mission_id": routine_id,
                        "title": "Complete one lesson",
                        "description": "Close the loop by learning why this workflow works.",
                        "action_type": "lesson_completed",
                        "required_count": 1,
                        "target_prompt_id": None,
                        "target_lesson_id": first_lesson_id,
                        "reward_credits": 8,
                        "sort_order": 3,
                        "created_at": now,
                    },
                ],
            )

    if routine_id is not None and first_prompt_id is not None:
        prompt_link_count = bind.execute(
            sa.text(
                """
                SELECT count(*)
                FROM lesson_mission_prompts
                WHERE mission_id = :mission_id AND prompt_id = :prompt_id
                """
            ),
            {"mission_id": routine_id, "prompt_id": first_prompt_id},
        ).scalar()
        if int(prompt_link_count or 0) == 0:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO lesson_mission_prompts (mission_id, prompt_id, sort_order)
                    VALUES (:mission_id, :prompt_id, 0)
                    """
                ),
                {"mission_id": routine_id, "prompt_id": first_prompt_id},
            )

def downgrade() -> None:
    op.drop_index("ix_user_purchases_client_token", table_name="user_purchases")
    op.drop_column("user_purchases", "client_token")

    op.drop_column("user_currency_balances", "last_check_in_at")
    op.drop_column("user_currency_balances", "best_streak")
    op.drop_column("user_currency_balances", "current_streak")

    op.drop_constraint("uq_user_mission_reward_grants_key", "user_mission_reward_grants", type_="unique")
    op.create_unique_constraint(
        "uq_user_mission_reward_grants_key",
        "user_mission_reward_grants",
        ["user_id", "mission_id", "reward_type"],
    )
    op.drop_column("user_mission_reward_grants", "reward_cycle")

    op.drop_column("user_mission_progress", "completion_count")

    op.drop_index("ix_lesson_missions_is_repeatable", table_name="lesson_missions")
    op.drop_column("lesson_missions", "repeat_interval_days")
    op.drop_column("lesson_missions", "is_repeatable")
    op.drop_index("ix_lesson_missions_mission_type", table_name="lesson_missions")
    op.drop_column("lesson_missions", "mission_type")

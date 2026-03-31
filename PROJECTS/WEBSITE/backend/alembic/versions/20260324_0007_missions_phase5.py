"""phase5 missions engagement loop

Revision ID: 20260324_0007
Revises: 20260324_0006
Create Date: 2026-03-24

"""

from collections.abc import Sequence
from datetime import datetime, timezone
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "20260324_0007"
down_revision: str | None = "20260324_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())
    user_cols = {c["name"] for c in insp.get_columns("users")}
    lesson_mission_cols = {c["name"] for c in insp.get_columns("lesson_missions")} if "lesson_missions" in tables else set()

    if "mission_credits" not in user_cols:
        op.add_column("users", sa.Column("mission_credits", sa.Integer(), nullable=False, server_default="0"))
    if "premium_unlock_until" not in user_cols:
        op.add_column("users", sa.Column("premium_unlock_until", sa.DateTime(timezone=True), nullable=True))
        op.create_index("ix_users_premium_unlock_until", "users", ["premium_unlock_until"], unique=False)

    if "lesson_missions" not in tables:
        op.create_table(
            "lesson_missions",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("slug", sa.String(length=120), nullable=False, unique=True),
            sa.Column("title", sa.String(length=220), nullable=False),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column("objective", sa.String(length=320), nullable=False),
            sa.Column("completion_condition", sa.String(length=320), nullable=False),
            sa.Column("action_type", sa.String(length=40), nullable=False),
            sa.Column("difficulty", sa.String(length=24), nullable=False),
            sa.Column("required_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("persona_role", sa.String(length=32), nullable=True),
            sa.Column("persona_goal", sa.String(length=32), nullable=True),
            sa.Column(
                "lesson_id",
                sa.Uuid(),
                sa.ForeignKey("lessons.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("reward_badge", sa.String(length=120), nullable=True),
            sa.Column("reward_credits", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("reward_premium_days", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_lesson_missions_slug", "lesson_missions", ["slug"], unique=True)
        op.create_index("ix_lesson_missions_lesson_id", "lesson_missions", ["lesson_id"], unique=False)
        op.create_index("ix_lesson_missions_persona_role", "lesson_missions", ["persona_role"], unique=False)
        op.create_index("ix_lesson_missions_persona_goal", "lesson_missions", ["persona_goal"], unique=False)
        op.create_index("ix_lesson_missions_is_active", "lesson_missions", ["is_active"], unique=False)
        op.create_index("ix_lesson_missions_difficulty", "lesson_missions", ["difficulty"], unique=False)

    if "lesson_mission_prompts" not in tables:
        op.create_table(
            "lesson_mission_prompts",
            sa.Column(
                "mission_id",
                sa.Uuid(),
                sa.ForeignKey("lesson_missions.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "prompt_id",
                sa.Uuid(),
                sa.ForeignKey("prompts.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        )
        op.create_index(
            "ix_lesson_mission_prompts_prompt_id",
            "lesson_mission_prompts",
            ["prompt_id"],
            unique=False,
        )

    if "user_mission_progress" not in tables:
        op.create_table(
            "user_mission_progress",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "mission_id",
                sa.Uuid(),
                sa.ForeignKey("lesson_missions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="not_started"),
            sa.Column("progress_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("required_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reward_granted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("user_id", "mission_id", name="uq_user_mission_progress_user_mission"),
        )
        op.create_index("ix_user_mission_progress_user_id", "user_mission_progress", ["user_id"], unique=False)
        op.create_index(
            "ix_user_mission_progress_mission_id",
            "user_mission_progress",
            ["mission_id"],
            unique=False,
        )
        op.create_index("ix_user_mission_progress_status", "user_mission_progress", ["status"], unique=False)

    if "mission_completion_events" not in tables:
        op.create_table(
            "mission_completion_events",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column(
                "progress_id",
                sa.Uuid(),
                sa.ForeignKey("user_mission_progress.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "mission_id",
                sa.Uuid(),
                sa.ForeignKey("lesson_missions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("event_type", sa.String(length=80), nullable=False),
            sa.Column("source_event_key", sa.String(length=180), nullable=False, unique=True),
            sa.Column(
                "prompt_id",
                sa.Uuid(),
                sa.ForeignKey("prompts.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "lesson_id",
                sa.Uuid(),
                sa.ForeignKey("lessons.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_mission_completion_events_progress_id",
            "mission_completion_events",
            ["progress_id"],
            unique=False,
        )
        op.create_index(
            "ix_mission_completion_events_user_id",
            "mission_completion_events",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            "ix_mission_completion_events_mission_id",
            "mission_completion_events",
            ["mission_id"],
            unique=False,
        )
        op.create_index(
            "ix_mission_completion_events_event_type",
            "mission_completion_events",
            ["event_type"],
            unique=False,
        )
        op.create_index(
            "ix_mission_completion_events_source_event_key",
            "mission_completion_events",
            ["source_event_key"],
            unique=True,
        )

    if "user_mission_reward_grants" not in tables:
        op.create_table(
            "user_mission_reward_grants",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "mission_id",
                sa.Uuid(),
                sa.ForeignKey("lesson_missions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("reward_type", sa.String(length=32), nullable=False),
            sa.Column("badge_code", sa.String(length=120), nullable=True),
            sa.Column("credits", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("premium_access_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("user_id", "mission_id", "reward_type", name="uq_user_mission_reward_grants_key"),
        )
        op.create_index(
            "ix_user_mission_reward_grants_user_id",
            "user_mission_reward_grants",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            "ix_user_mission_reward_grants_mission_id",
            "user_mission_reward_grants",
            ["mission_id"],
            unique=False,
        )
        op.create_index(
            "ix_user_mission_reward_grants_reward_type",
            "user_mission_reward_grants",
            ["reward_type"],
            unique=False,
        )

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
        sa.column("required_count", sa.Integer()),
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
        *((
            sa.column("mission_type", sa.String(length=24)),
        ) if "mission_type" in lesson_mission_cols else ()),
        *((
            sa.column("is_repeatable", sa.Boolean()),
        ) if "is_repeatable" in lesson_mission_cols else ()),
        *((
            sa.column("repeat_interval_days", sa.Integer()),
        ) if "repeat_interval_days" in lesson_mission_cols else ()),
        *((sa.column("chain_id", sa.String(length=120)),) if "chain_id" in lesson_mission_cols else ()),
        *((sa.column("chain_step", sa.Integer()),) if "chain_step" in lesson_mission_cols else ()),
        *((sa.column("chain_total", sa.Integer()),) if "chain_total" in lesson_mission_cols else ()),
        *((sa.column("chain_bonus_credits", sa.Integer()),) if "chain_bonus_credits" in lesson_mission_cols else ()),
        *((sa.column("chain_unlock_on_slug", sa.String(length=120)),) if "chain_unlock_on_slug" in lesson_mission_cols else ()),
        *((sa.column("adaptive_segment", sa.String(length=24)),) if "adaptive_segment" in lesson_mission_cols else ()),
    )
    existing_slugs = {row[0] for row in bind.execute(sa.text("SELECT slug FROM lesson_missions")).fetchall()}
    first_lesson_id = bind.execute(sa.text("SELECT id FROM lessons ORDER BY sort_order, title LIMIT 1")).scalar()

    now = _utcnow()
    defaults = [
        {
            "slug": "onboarding-first-win",
            "title": "Complete your first AI win",
            "description": "Finish onboarding and apply your first recommended prompt.",
            "objective": "Get your first practical AI result.",
            "completion_condition": "Complete onboarding first win action.",
            "action_type": "onboarding_first_win",
            "difficulty": "easy",
            "required_count": 1,
            "persona_role": None,
            "persona_goal": None,
            "lesson_id": None,
            "reward_badge": "first-win",
            "reward_credits": 10,
            "reward_premium_days": 0,
            "is_active": True,
            "sort_order": 1,
        },
        {
            "slug": "copy-a-prompt-and-run-it",
            "title": "Apply one prompt from your feed",
            "description": "Use a recommended prompt in your AI tool and inspect the output.",
            "objective": "Turn learning into a real result in under 2 minutes.",
            "completion_condition": "Copy one linked prompt.",
            "action_type": "copy_prompt",
            "difficulty": "standard",
            "required_count": 1,
            "persona_role": None,
            "persona_goal": "solving_tasks",
            "lesson_id": None,
            "reward_badge": "quick-applier",
            "reward_credits": 15,
            "reward_premium_days": 0,
            "is_active": True,
            "sort_order": 2,
        },
        {
            "slug": "save-your-first-workflow",
            "title": "Build your reusable prompt stack",
            "description": "Save prompts you plan to reuse and build a personal workflow library.",
            "objective": "Create a reusable set of prompts for future tasks.",
            "completion_condition": "Save one linked prompt.",
            "action_type": "save_prompt",
            "difficulty": "standard",
            "required_count": 1,
            "persona_role": None,
            "persona_goal": "productivity",
            "lesson_id": None,
            "reward_badge": "workflow-builder",
            "reward_credits": 20,
            "reward_premium_days": 0,
            "is_active": True,
            "sort_order": 3,
        },
        {
            "slug": "complete-and-apply-lesson",
            "title": "Finish one lesson and apply it",
            "description": "Complete the lesson and immediately apply the linked prompt.",
            "objective": "Convert a lesson into practical output.",
            "completion_condition": "Mark linked lesson as completed.",
            "action_type": "lesson_completed",
            "difficulty": "standard",
            "required_count": 1,
            "persona_role": "student",
            "persona_goal": "learning",
            "lesson_id": first_lesson_id,
            "reward_badge": "lesson-practitioner",
            "reward_credits": 30,
            "reward_premium_days": 1,
            "is_active": True,
            "sort_order": 4,
        },
    ]

    rows: list[dict[str, object]] = []
    for item in defaults:
        if item["slug"] in existing_slugs:
            continue
        rows.append(
            {
                "id": uuid.uuid4(),
                "slug": item["slug"],
                "title": item["title"],
                "description": item["description"],
                "objective": item["objective"],
                "completion_condition": item["completion_condition"],
                "action_type": item["action_type"],
                "difficulty": item["difficulty"],
                "required_count": item["required_count"],
                "persona_role": item["persona_role"],
                "persona_goal": item["persona_goal"],
                "lesson_id": item["lesson_id"],
                "reward_badge": item["reward_badge"],
                "reward_credits": item["reward_credits"],
                "reward_premium_days": item["reward_premium_days"],
                "is_active": item["is_active"],
                "sort_order": item["sort_order"],
                "created_at": now,
                "updated_at": now,
                **({"mission_type": "action"} if "mission_type" in lesson_mission_cols else {}),
                **({"is_repeatable": False} if "is_repeatable" in lesson_mission_cols else {}),
                **({"repeat_interval_days": 0} if "repeat_interval_days" in lesson_mission_cols else {}),
                **({"chain_id": None} if "chain_id" in lesson_mission_cols else {}),
                **({"chain_step": 0} if "chain_step" in lesson_mission_cols else {}),
                **({"chain_total": 0} if "chain_total" in lesson_mission_cols else {}),
                **({"chain_bonus_credits": 0} if "chain_bonus_credits" in lesson_mission_cols else {}),
                **({"chain_unlock_on_slug": None} if "chain_unlock_on_slug" in lesson_mission_cols else {}),
                **({"adaptive_segment": None} if "adaptive_segment" in lesson_mission_cols else {}),
            }
        )
    if rows:
        op.bulk_insert(mission_table, rows)

    mission_ids = {
        row[1]: row[0]
        for row in bind.execute(
            sa.text(
                """
                SELECT id, slug
                FROM lesson_missions
                WHERE slug IN (
                    'copy-a-prompt-and-run-it',
                    'save-your-first-workflow',
                    'onboarding-first-win'
                )
                """
            )
        ).fetchall()
    }
    prompt_ids = [row[0] for row in bind.execute(
        sa.text(
            """
            SELECT id
            FROM prompts
            WHERE status = 'published'
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
    ).fetchall()]

    if mission_ids and prompt_ids:
        link_table = sa.table(
            "lesson_mission_prompts",
            sa.column("mission_id", sa.Uuid()),
            sa.column("prompt_id", sa.Uuid()),
            sa.column("sort_order", sa.Integer()),
        )
        existing_links = {
            (row[0], row[1])
            for row in bind.execute(
                sa.text(
                    """
                    SELECT mission_id, prompt_id
                    FROM lesson_mission_prompts
                    WHERE mission_id IN (
                        SELECT id
                        FROM lesson_missions
                        WHERE slug IN (
                            'copy-a-prompt-and-run-it',
                            'save-your-first-workflow',
                            'onboarding-first-win'
                        )
                    )
                    """
                )
            ).fetchall()
        }
        links: list[dict[str, object]] = []
        mapping = {
            "onboarding-first-win": prompt_ids[:1],
            "copy-a-prompt-and-run-it": prompt_ids[:3],
            "save-your-first-workflow": prompt_ids[:3],
        }
        for slug, selected_prompt_ids in mapping.items():
            mission_id = mission_ids.get(slug)
            if mission_id is None:
                continue
            for index, prompt_id in enumerate(selected_prompt_ids):
                if (mission_id, prompt_id) in existing_links:
                    continue
                links.append({"mission_id": mission_id, "prompt_id": prompt_id, "sort_order": index})
        if links:
            op.bulk_insert(link_table, links)


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())
    user_cols = {c["name"] for c in insp.get_columns("users")}

    if "user_mission_reward_grants" in tables:
        op.drop_index("ix_user_mission_reward_grants_reward_type", table_name="user_mission_reward_grants")
        op.drop_index("ix_user_mission_reward_grants_mission_id", table_name="user_mission_reward_grants")
        op.drop_index("ix_user_mission_reward_grants_user_id", table_name="user_mission_reward_grants")
        op.drop_table("user_mission_reward_grants")

    if "mission_completion_events" in tables:
        op.drop_index("ix_mission_completion_events_source_event_key", table_name="mission_completion_events")
        op.drop_index("ix_mission_completion_events_event_type", table_name="mission_completion_events")
        op.drop_index("ix_mission_completion_events_mission_id", table_name="mission_completion_events")
        op.drop_index("ix_mission_completion_events_user_id", table_name="mission_completion_events")
        op.drop_index("ix_mission_completion_events_progress_id", table_name="mission_completion_events")
        op.drop_table("mission_completion_events")

    if "user_mission_progress" in tables:
        op.drop_index("ix_user_mission_progress_status", table_name="user_mission_progress")
        op.drop_index("ix_user_mission_progress_mission_id", table_name="user_mission_progress")
        op.drop_index("ix_user_mission_progress_user_id", table_name="user_mission_progress")
        op.drop_table("user_mission_progress")

    if "lesson_mission_prompts" in tables:
        op.drop_index("ix_lesson_mission_prompts_prompt_id", table_name="lesson_mission_prompts")
        op.drop_table("lesson_mission_prompts")

    if "lesson_missions" in tables:
        op.execute("DROP INDEX IF EXISTS ix_lesson_missions_difficulty")
        op.drop_index("ix_lesson_missions_is_active", table_name="lesson_missions")
        op.drop_index("ix_lesson_missions_persona_goal", table_name="lesson_missions")
        op.drop_index("ix_lesson_missions_persona_role", table_name="lesson_missions")
        op.drop_index("ix_lesson_missions_lesson_id", table_name="lesson_missions")
        op.drop_index("ix_lesson_missions_slug", table_name="lesson_missions")
        op.drop_table("lesson_missions")

    if "premium_unlock_until" in user_cols:
        op.execute("DROP INDEX IF EXISTS ix_users_premium_unlock_until")
        op.drop_column("users", "premium_unlock_until")
    if "mission_credits" in user_cols:
        op.drop_column("users", "mission_credits")

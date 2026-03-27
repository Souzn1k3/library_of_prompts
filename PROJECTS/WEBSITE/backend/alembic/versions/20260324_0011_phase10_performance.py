"""phase10 performance indexes

Revision ID: 20260324_0011
Revises: 20260324_0010
Create Date: 2026-03-24

"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260324_0011"
down_revision: str | None = "20260324_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # prompts: common filtering/sorting lanes used by catalog + discovery
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompts_status_created_at
        ON prompts (status, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompts_status_category_created_at
        ON prompts (status, category_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompts_status_difficulty_created_at
        ON prompts (status, difficulty, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompts_status_output_type_created_at
        ON prompts (status, output_type, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompts_author_created_at
        ON prompts (author_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompts_moderation_state_created_at
        ON prompts (moderation_state, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompts_category_id
        ON prompts (category_id)
        """
    )

    # lessons + categories + missions
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_lessons_sort_order_title
        ON lessons (sort_order, title)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_categories_parent_sort_order
        ON categories (parent_id, sort_order)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_lesson_missions_is_active_sort_order
        ON lesson_missions (is_active, sort_order, created_at)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_mission_completion_events_lesson_created_at
        ON mission_completion_events (lesson_id, created_at DESC)
        WHERE lesson_id IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_mission_completion_events_prompt_created_at
        ON mission_completion_events (prompt_id, created_at DESC)
        WHERE prompt_id IS NOT NULL
        """
    )

    # analytics + billing/auth hot paths
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_analytics_events_name_occurred_at
        ON analytics_events (event_name, occurred_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_subscriptions_user_status
        ON subscriptions (user_id, status, current_period_end DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_auth_refresh_tokens_user_revoked_expires
        ON auth_refresh_tokens (user_id, revoked_at, expires_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_auth_refresh_tokens_user_revoked_expires")
    op.execute("DROP INDEX IF EXISTS ix_subscriptions_user_status")
    op.execute("DROP INDEX IF EXISTS ix_analytics_events_name_occurred_at")
    op.execute("DROP INDEX IF EXISTS ix_mission_completion_events_prompt_created_at")
    op.execute("DROP INDEX IF EXISTS ix_mission_completion_events_lesson_created_at")
    op.execute("DROP INDEX IF EXISTS ix_lesson_missions_is_active_sort_order")
    op.execute("DROP INDEX IF EXISTS ix_categories_parent_sort_order")
    op.execute("DROP INDEX IF EXISTS ix_lessons_sort_order_title")
    op.execute("DROP INDEX IF EXISTS ix_prompts_category_id")
    op.execute("DROP INDEX IF EXISTS ix_prompts_moderation_state_created_at")
    op.execute("DROP INDEX IF EXISTS ix_prompts_author_created_at")
    op.execute("DROP INDEX IF EXISTS ix_prompts_status_output_type_created_at")
    op.execute("DROP INDEX IF EXISTS ix_prompts_status_difficulty_created_at")
    op.execute("DROP INDEX IF EXISTS ix_prompts_status_category_created_at")
    op.execute("DROP INDEX IF EXISTS ix_prompts_status_created_at")


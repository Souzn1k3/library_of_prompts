"""legacy_cleanup

Revision ID: 20260328_0013
Revises: 20260327_0012
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260328_0013"
down_revision = "20260327_0012"
branch_labels = None
depends_on = None


TEST_USER_CONDITION = """
    lower(email) LIKE 'pytest_%@example.com'
    OR lower(email) LIKE 'mod_%@example.com'
    OR lower(email) IN (
        'test@example.com',
        'phase11.user@promptsvault.com',
        'admin@promptsvault.com',
        'moderator@promptsvault.com'
    )
"""


def upgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            """
            UPDATE users
            SET email = 'system-curated@promptsvault.local',
                display_name = 'Prompts Vault Team'
            WHERE lower(email) = 'seed.author@promptsvault.com'
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE contributor_profiles
            SET slug = 'prompts-vault-curated',
                bio = COALESCE(
                    bio,
                    'Curated starter prompts maintained by the Prompts Vault team.'
                )
            WHERE slug = 'seed-author'
            """
        )
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM analytics_events
            WHERE event_id LIKE 'phase11_%'
               OR event_id LIKE 'pytest_evt_%'
               OR session_id IN ('phase11-session', 'pytest_session')
               OR user_id IN (SELECT id FROM users WHERE {condition})
            """.format(condition=TEST_USER_CONDITION)
        )
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM subscription_events
            WHERE provider_event_id LIKE 'evt_phase11_%'
               OR user_id IN (SELECT id FROM users WHERE {condition})
            """.format(condition=TEST_USER_CONDITION)
        )
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM processed_webhook_events
            WHERE event_id LIKE 'evt_phase11_%'
               OR event_id = 'evt_test'
            """
        )
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM lesson_missions
            WHERE slug IN ('first-win', 'save-a-prompt', 'complete-basics-lesson')
            """
        )
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM prompts
            WHERE author_id IN (SELECT id FROM users WHERE {condition})
            """.format(condition=TEST_USER_CONDITION)
        )
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM users
            WHERE {condition}
            """.format(condition=TEST_USER_CONDITION)
        )
    )


def downgrade() -> None:
    # Data cleanup is intentionally irreversible.
    pass

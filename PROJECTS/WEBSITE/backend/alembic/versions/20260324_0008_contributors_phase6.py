"""phase6 contributors and reputation

Revision ID: 20260324_0008
Revises: 20260324_0007
Create Date: 2026-03-24

"""

from collections.abc import Sequence
from datetime import datetime, timezone
import re
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "20260324_0008"
down_revision: str | None = "20260324_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "contributor"


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())
    prompt_cols = {c["name"] for c in insp.get_columns("prompts")}

    if "contributor_profiles" not in tables:
        op.create_table(
            "contributor_profiles",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("slug", sa.String(length=120), nullable=False, unique=True),
            sa.Column("bio", sa.String(length=500), nullable=True),
            sa.Column("reputation_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("reputation_tier", sa.String(length=24), nullable=False, server_default="new"),
            sa.Column("total_submissions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("approved_submissions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("rejected_submissions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("rejection_rate", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_saves", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_copies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("mission_success_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("average_prompt_quality", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("computed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_contributor_profiles_user_id", "contributor_profiles", ["user_id"], unique=True)
        op.create_index("ix_contributor_profiles_slug", "contributor_profiles", ["slug"], unique=True)
        op.create_index(
            "ix_contributor_profiles_reputation_score",
            "contributor_profiles",
            ["reputation_score"],
            unique=False,
        )
        op.create_index(
            "ix_contributor_profiles_reputation_tier",
            "contributor_profiles",
            ["reputation_tier"],
            unique=False,
        )

    if "prompt_quality_metrics" not in tables:
        op.create_table(
            "prompt_quality_metrics",
            sa.Column(
                "prompt_id",
                sa.Uuid(),
                sa.ForeignKey("prompts.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column("unique_savers", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("copy_events", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("mission_success_events", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("quality_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("computed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_prompt_quality_metrics_quality_score",
            "prompt_quality_metrics",
            ["quality_score"],
            unique=False,
        )

    if "moderated_by_id" not in prompt_cols:
        op.add_column(
            "prompts",
            sa.Column(
                "moderated_by_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
        op.create_index("ix_prompts_moderated_by_id", "prompts", ["moderated_by_id"], unique=False)

    if "moderated_at" not in prompt_cols:
        op.add_column("prompts", sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True))

    if "auto_approved" not in prompt_cols:
        op.add_column("prompts", sa.Column("auto_approved", sa.Boolean(), nullable=False, server_default=sa.false()))
        op.create_index("ix_prompts_auto_approved", "prompts", ["auto_approved"], unique=False)

    now = _utcnow()
    profile_table = sa.table(
        "contributor_profiles",
        sa.column("id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
        sa.column("slug", sa.String(length=120)),
        sa.column("bio", sa.String(length=500)),
        sa.column("reputation_score", sa.Integer()),
        sa.column("reputation_tier", sa.String(length=24)),
        sa.column("total_submissions", sa.Integer()),
        sa.column("approved_submissions", sa.Integer()),
        sa.column("rejected_submissions", sa.Integer()),
        sa.column("rejection_rate", sa.Integer()),
        sa.column("total_saves", sa.Integer()),
        sa.column("total_copies", sa.Integer()),
        sa.column("mission_success_count", sa.Integer()),
        sa.column("average_prompt_quality", sa.Integer()),
        sa.column("computed_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    existing_profile_user_ids = {
        row[0] for row in bind.execute(sa.text("SELECT user_id FROM contributor_profiles")).fetchall()
    }
    used_slugs = {row[0] for row in bind.execute(sa.text("SELECT slug FROM contributor_profiles")).fetchall()}
    user_rows = bind.execute(sa.text("SELECT id, display_name FROM users")).fetchall()
    inserts: list[dict[str, object]] = []
    for user_id, display_name in user_rows:
        if user_id in existing_profile_user_ids:
            continue
        base = _slugify(display_name or "contributor")
        slug = base
        suffix = 1
        while slug in used_slugs:
            suffix += 1
            slug = f"{base}-{suffix}"
        used_slugs.add(slug)
        inserts.append(
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "slug": slug,
                "bio": None,
                "reputation_score": 0,
                "reputation_tier": "new",
                "total_submissions": 0,
                "approved_submissions": 0,
                "rejected_submissions": 0,
                "rejection_rate": 0,
                "total_saves": 0,
                "total_copies": 0,
                "mission_success_count": 0,
                "average_prompt_quality": 0,
                "computed_at": now,
                "created_at": now,
                "updated_at": now,
            }
        )
    if inserts:
        op.bulk_insert(profile_table, inserts)

    op.execute(
        """
        INSERT INTO prompt_quality_metrics (
            prompt_id,
            unique_savers,
            copy_events,
            mission_success_events,
            quality_score,
            computed_at,
            updated_at
        )
        SELECT
            p.id AS prompt_id,
            COALESCE(ps.save_count, 0) AS unique_savers,
            COALESCE(ps.copy_count, 0) AS copy_events,
            COALESCE(ms.success_count, 0) AS mission_success_events,
            LEAST(
                100,
                GREATEST(
                    0,
                    (COALESCE(ps.save_count, 0) * 4)
                    + (COALESCE(ps.copy_count, 0) * 2)
                    + (COALESCE(ms.success_count, 0) * 5)
                )
            )::int AS quality_score,
            NOW() AS computed_at,
            NOW() AS updated_at
        FROM prompts p
        LEFT JOIN prompt_stats ps ON ps.prompt_id = p.id
        LEFT JOIN (
            SELECT prompt_id, COUNT(*)::int AS success_count
            FROM mission_completion_events
            WHERE prompt_id IS NOT NULL
            GROUP BY prompt_id
        ) ms ON ms.prompt_id = p.id
        ON CONFLICT (prompt_id) DO UPDATE
        SET unique_savers = EXCLUDED.unique_savers,
            copy_events = EXCLUDED.copy_events,
            mission_success_events = EXCLUDED.mission_success_events,
            quality_score = EXCLUDED.quality_score,
            computed_at = EXCLUDED.computed_at,
            updated_at = EXCLUDED.updated_at
        """
    )

    op.execute(
        """
        WITH agg AS (
            SELECT
                p.author_id AS user_id,
                COUNT(p.id)::int AS total_submissions,
                SUM(CASE WHEN p.moderation_state = 'approved' THEN 1 ELSE 0 END)::int AS approved_submissions,
                SUM(CASE WHEN p.moderation_state = 'rejected' THEN 1 ELSE 0 END)::int AS rejected_submissions,
                SUM(
                    CASE
                        WHEN p.moderation_state = 'approved' THEN COALESCE(ps.save_count, 0)
                        ELSE 0
                    END
                )::int AS total_saves,
                SUM(
                    CASE
                        WHEN p.moderation_state = 'approved' THEN COALESCE(ps.copy_count, 0)
                        ELSE 0
                    END
                )::int AS total_copies,
                COALESCE(
                    AVG(
                        CASE
                            WHEN p.moderation_state = 'approved' THEN COALESCE(pqm.quality_score, 0)
                            ELSE NULL
                        END
                    ),
                    0
                )::int AS average_prompt_quality
            FROM prompts p
            LEFT JOIN prompt_stats ps ON ps.prompt_id = p.id
            LEFT JOIN prompt_quality_metrics pqm ON pqm.prompt_id = p.id
            WHERE p.author_id IS NOT NULL
            GROUP BY p.author_id
        ),
        mission AS (
            SELECT
                p.author_id AS user_id,
                COUNT(mce.id)::int AS mission_success_count
            FROM mission_completion_events mce
            JOIN prompts p ON p.id = mce.prompt_id
            WHERE p.author_id IS NOT NULL
            GROUP BY p.author_id
        ),
        merged AS (
            SELECT
                cp.user_id,
                COALESCE(a.total_submissions, 0) AS total_submissions,
                COALESCE(a.approved_submissions, 0) AS approved_submissions,
                COALESCE(a.rejected_submissions, 0) AS rejected_submissions,
                COALESCE(a.total_saves, 0) AS total_saves,
                COALESCE(a.total_copies, 0) AS total_copies,
                COALESCE(m.mission_success_count, 0) AS mission_success_count,
                COALESCE(a.average_prompt_quality, 0) AS average_prompt_quality
            FROM contributor_profiles cp
            LEFT JOIN agg a ON a.user_id = cp.user_id
            LEFT JOIN mission m ON m.user_id = cp.user_id
        ),
        scored AS (
            SELECT
                user_id,
                total_submissions,
                approved_submissions,
                rejected_submissions,
                CASE
                    WHEN (approved_submissions + rejected_submissions) > 0
                        THEN ROUND((rejected_submissions::numeric / (approved_submissions + rejected_submissions)::numeric) * 100)::int
                    ELSE 0
                END AS rejection_rate,
                total_saves,
                total_copies,
                mission_success_count,
                average_prompt_quality,
                LEAST(
                    100,
                    GREATEST(
                        0,
                        ROUND(
                            (
                                (
                                    CASE
                                        WHEN (approved_submissions + rejected_submissions) > 0
                                            THEN (approved_submissions::numeric / (approved_submissions + rejected_submissions)::numeric) * 45
                                        ELSE 0
                                    END
                                )
                                + LEAST(COALESCE(total_saves::numeric / GREATEST(approved_submissions, 1), 0) / 6.0, 1.0) * 20
                                + LEAST(COALESCE(total_copies::numeric / GREATEST(approved_submissions, 1), 0) / 12.0, 1.0) * 20
                                + LEAST(COALESCE(mission_success_count::numeric / GREATEST(approved_submissions, 1), 0) / 4.0, 1.0) * 10
                                + LEAST(COALESCE(average_prompt_quality::numeric / 100.0, 0), 1.0) * 5
                                - (
                                    CASE
                                        WHEN (approved_submissions + rejected_submissions) > 0
                                            THEN (rejected_submissions::numeric / (approved_submissions + rejected_submissions)::numeric) * 15
                                        ELSE 0
                                    END
                                )
                                - (
                                    CASE
                                        WHEN total_submissions <= 5 THEN 0
                                        ELSE LEAST(
                                            GREATEST((total_submissions - approved_submissions)::numeric / GREATEST(total_submissions, 1), 0),
                                            1
                                        ) * 5
                                    END
                                )
                            )
                        )::int
                    )
                ) AS reputation_score
            FROM merged
        )
        UPDATE contributor_profiles cp
        SET
            total_submissions = s.total_submissions,
            approved_submissions = s.approved_submissions,
            rejected_submissions = s.rejected_submissions,
            rejection_rate = s.rejection_rate,
            total_saves = s.total_saves,
            total_copies = s.total_copies,
            mission_success_count = s.mission_success_count,
            average_prompt_quality = s.average_prompt_quality,
            reputation_score = s.reputation_score,
            reputation_tier = CASE
                WHEN s.reputation_score >= 78 AND s.approved_submissions >= 20
                    AND (100 - s.rejection_rate) >= 88
                    AND (COALESCE(s.total_saves::numeric / GREATEST(s.approved_submissions, 1), 0) >= 2.5)
                    THEN 'top'
                WHEN s.reputation_score >= 45 AND s.approved_submissions >= 5
                    AND (100 - s.rejection_rate) >= 65
                    THEN 'verified'
                ELSE 'new'
            END,
            computed_at = NOW(),
            updated_at = NOW()
        FROM scored s
        WHERE cp.user_id = s.user_id
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())
    prompt_cols = {c["name"] for c in insp.get_columns("prompts")}

    if "prompt_quality_metrics" in tables:
        op.drop_index("ix_prompt_quality_metrics_quality_score", table_name="prompt_quality_metrics")
        op.drop_table("prompt_quality_metrics")

    if "contributor_profiles" in tables:
        op.drop_index("ix_contributor_profiles_reputation_tier", table_name="contributor_profiles")
        op.drop_index("ix_contributor_profiles_reputation_score", table_name="contributor_profiles")
        op.drop_index("ix_contributor_profiles_slug", table_name="contributor_profiles")
        op.drop_index("ix_contributor_profiles_user_id", table_name="contributor_profiles")
        op.drop_table("contributor_profiles")

    if "auto_approved" in prompt_cols:
        op.drop_index("ix_prompts_auto_approved", table_name="prompts")
        op.drop_column("prompts", "auto_approved")

    if "moderated_at" in prompt_cols:
        op.drop_column("prompts", "moderated_at")

    if "moderated_by_id" in prompt_cols:
        op.drop_index("ix_prompts_moderated_by_id", table_name="prompts")
        op.drop_column("prompts", "moderated_by_id")

"""phase4 discovery taxonomy and search indexes

Revision ID: 20260324_0006
Revises: 20260324_0005
Create Date: 2026-03-24

"""

from collections.abc import Sequence
from datetime import datetime, timezone
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "20260324_0006"
down_revision: str | None = "20260324_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    prompt_cols = {c["name"] for c in insp.get_columns("prompts")}
    if "difficulty" not in prompt_cols:
        op.add_column("prompts", sa.Column("difficulty", sa.String(length=32), nullable=True))
        op.create_index("ix_prompts_difficulty", "prompts", ["difficulty"], unique=False)
    if "output_type" not in prompt_cols:
        op.add_column("prompts", sa.Column("output_type", sa.String(length=32), nullable=True))
        op.create_index("ix_prompts_output_type", "prompts", ["output_type"], unique=False)

    if "use_cases" not in tables:
        op.create_table(
            "use_cases",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_use_cases_slug", "use_cases", ["slug"], unique=True)

    if "model_compatibilities" not in tables:
        op.create_table(
            "model_compatibilities",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_model_compatibilities_slug", "model_compatibilities", ["slug"], unique=True)

    if "tags" not in tables:
        op.create_table(
            "tags",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_tags_slug", "tags", ["slug"], unique=True)

    if "prompt_use_cases" not in tables:
        op.create_table(
            "prompt_use_cases",
            sa.Column(
                "prompt_id",
                sa.Uuid(),
                sa.ForeignKey("prompts.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "use_case_id",
                sa.Uuid(),
                sa.ForeignKey("use_cases.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
        )
        op.create_index(
            "ix_prompt_use_cases_use_case_id",
            "prompt_use_cases",
            ["use_case_id"],
            unique=False,
        )

    if "prompt_model_compatibilities" not in tables:
        op.create_table(
            "prompt_model_compatibilities",
            sa.Column(
                "prompt_id",
                sa.Uuid(),
                sa.ForeignKey("prompts.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "model_id",
                sa.Uuid(),
                sa.ForeignKey("model_compatibilities.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
        )
        op.create_index(
            "ix_prompt_model_compatibilities_model_id",
            "prompt_model_compatibilities",
            ["model_id"],
            unique=False,
        )

    if "prompt_tags" not in tables:
        op.create_table(
            "prompt_tags",
            sa.Column(
                "prompt_id",
                sa.Uuid(),
                sa.ForeignKey("prompts.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "tag_id",
                sa.Uuid(),
                sa.ForeignKey("tags.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
        )
        op.create_index("ix_prompt_tags_tag_id", "prompt_tags", ["tag_id"], unique=False)

    if "prompt_stats" not in tables:
        op.create_table(
            "prompt_stats",
            sa.Column(
                "prompt_id",
                sa.Uuid(),
                sa.ForeignKey("prompts.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column("save_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("copy_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("quality_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompts_search_vector
        ON prompts
        USING GIN (
          to_tsvector(
            'english',
            coalesce(title, '') || ' ' || coalesce(summary, '') || ' ' || coalesce(body, '')
          )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompts_title_trgm
        ON prompts
        USING GIN (lower(title) gin_trgm_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompts_summary_trgm
        ON prompts
        USING GIN (lower(coalesce(summary, '')) gin_trgm_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompts_created_at
        ON prompts (created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompt_stats_save_count
        ON prompt_stats (save_count DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_prompt_stats_copy_count
        ON prompt_stats (copy_count DESC)
        """
    )

    now = _utcnow()
    use_case_table = sa.table(
        "use_cases",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String(length=100)),
        sa.column("name", sa.String(length=120)),
        sa.column("sort_order", sa.Integer()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    model_table = sa.table(
        "model_compatibilities",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String(length=100)),
        sa.column("name", sa.String(length=120)),
        sa.column("sort_order", sa.Integer()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    tag_table = sa.table(
        "tags",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String(length=100)),
        sa.column("name", sa.String(length=120)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    existing_use_cases = {
        row[0] for row in bind.execute(sa.text("SELECT slug FROM use_cases")).fetchall()
    }
    default_use_cases = [
        ("debugging", "Debugging", 1),
        ("studying", "Studying", 2),
        ("writing", "Writing", 3),
        ("planning", "Planning", 4),
        ("analysis", "Analysis", 5),
    ]
    use_case_rows: list[dict[str, object]] = []
    for slug, name, order in default_use_cases:
        if slug in existing_use_cases:
            continue
        use_case_rows.append(
            {"id": uuid.uuid4(), "slug": slug, "name": name, "sort_order": order, "created_at": now}
        )
    if use_case_rows:
        op.bulk_insert(use_case_table, use_case_rows)

    existing_models = {
        row[0] for row in bind.execute(sa.text("SELECT slug FROM model_compatibilities")).fetchall()
    }
    default_models = [
        ("gpt-4o", "GPT-4o", 1),
        ("gpt-5", "GPT-5", 2),
        ("claude-3-5", "Claude 3.5", 3),
        ("gemini-1-5", "Gemini 1.5", 4),
    ]
    model_rows: list[dict[str, object]] = []
    for slug, name, order in default_models:
        if slug in existing_models:
            continue
        model_rows.append(
            {"id": uuid.uuid4(), "slug": slug, "name": name, "sort_order": order, "created_at": now}
        )
    if model_rows:
        op.bulk_insert(model_table, model_rows)

    existing_tags = {
        row[0] for row in bind.execute(sa.text("SELECT slug FROM tags")).fetchall()
    }
    default_tags = ["beginner-friendly", "prompt-template", "chatbot", "productivity", "coding"]
    tag_rows: list[dict[str, object]] = []
    for slug in default_tags:
        if slug in existing_tags:
            continue
        tag_rows.append(
            {
                "id": uuid.uuid4(),
                "slug": slug,
                "name": slug.replace("-", " ").title(),
                "created_at": now,
            }
        )
    if tag_rows:
        op.bulk_insert(tag_table, tag_rows)

    op.execute(
        """
        INSERT INTO prompt_stats (prompt_id, save_count, copy_count, view_count, quality_score, updated_at)
        SELECT p.id,
               COALESCE(s.save_count, 0) AS save_count,
               0 AS copy_count,
               0 AS view_count,
               CASE
                 WHEN p.summary IS NOT NULL AND length(p.summary) > 20 THEN 60
                 ELSE 40
               END AS quality_score,
               NOW()
        FROM prompts p
        LEFT JOIN (
          SELECT prompt_id, COUNT(*)::int AS save_count
          FROM saved_prompts
          GROUP BY prompt_id
        ) s ON s.prompt_id = p.id
        ON CONFLICT (prompt_id) DO UPDATE
        SET save_count = EXCLUDED.save_count,
            updated_at = EXCLUDED.updated_at
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_prompt_stats_copy_count")
    op.execute("DROP INDEX IF EXISTS ix_prompt_stats_save_count")
    op.execute("DROP INDEX IF EXISTS ix_prompts_created_at")
    op.execute("DROP INDEX IF EXISTS ix_prompts_summary_trgm")
    op.execute("DROP INDEX IF EXISTS ix_prompts_title_trgm")
    op.execute("DROP INDEX IF EXISTS ix_prompts_search_vector")

    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())
    prompt_cols = {c["name"] for c in insp.get_columns("prompts")}

    if "prompt_stats" in tables:
        op.drop_table("prompt_stats")

    if "prompt_tags" in tables:
        op.drop_index("ix_prompt_tags_tag_id", table_name="prompt_tags")
        op.drop_table("prompt_tags")

    if "prompt_model_compatibilities" in tables:
        op.drop_index(
            "ix_prompt_model_compatibilities_model_id",
            table_name="prompt_model_compatibilities",
        )
        op.drop_table("prompt_model_compatibilities")

    if "prompt_use_cases" in tables:
        op.drop_index("ix_prompt_use_cases_use_case_id", table_name="prompt_use_cases")
        op.drop_table("prompt_use_cases")

    if "tags" in tables:
        op.drop_index("ix_tags_slug", table_name="tags")
        op.drop_table("tags")

    if "model_compatibilities" in tables:
        op.drop_index("ix_model_compatibilities_slug", table_name="model_compatibilities")
        op.drop_table("model_compatibilities")

    if "use_cases" in tables:
        op.drop_index("ix_use_cases_slug", table_name="use_cases")
        op.drop_table("use_cases")

    if "difficulty" in prompt_cols:
        op.drop_index("ix_prompts_difficulty", table_name="prompts")
        op.drop_column("prompts", "difficulty")
    if "output_type" in prompt_cols:
        op.drop_index("ix_prompts_output_type", table_name="prompts")
        op.drop_column("prompts", "output_type")

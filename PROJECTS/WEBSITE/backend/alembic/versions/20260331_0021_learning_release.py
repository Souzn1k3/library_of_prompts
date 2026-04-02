"""learning_release

Revision ID: 20260331_0021
Revises: 20260331_0020
Create Date: 2026-03-31
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op


revision = "20260331_0021"
down_revision = "20260331_0020"
branch_labels = None
depends_on = None


LEGACY_LEARNING_LESSONS: list[tuple[str, str]] = [
    ("pe-foundations", "Prompt Foundations: clear request design"),
    ("pe-structure-pattern", "Prompt Structure Pattern: role, context, task, output"),
    ("pe-constraints-and-examples", "Prompt Constraints and Examples"),
    ("pe-iteration-loop", "Prompt Iteration Loop"),
    ("pe-evaluate-quality", "Prompt Quality Evaluation"),
    ("pe-final-studio", "Prompt Final Studio"),
    ("wf-task-briefing", "Workflow Task Briefing"),
    ("wf-research-and-synthesis", "Workflow Research and Synthesis"),
    ("wf-writing-workflow", "Workflow for Writing"),
    ("wf-analysis-workflow", "Workflow for Analysis"),
    ("wf-prompt-debugging", "Workflow Prompt Debugging"),
    ("wf-capstone", "Workflow Capstone"),
]


def _insert_learning_lessons() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "lessons" not in inspector.get_table_names():
        return

    existing = {
        row[0]
        for row in bind.execute(sa.text("SELECT slug FROM lessons")).fetchall()
    }
    now = datetime.now(timezone.utc)
    for index, (slug, title) in enumerate(LEGACY_LEARNING_LESSONS, start=100):
        if slug in existing:
            continue
        bind.execute(
            sa.text(
                """
                INSERT INTO lessons (id, slug, title, body, min_tier, sort_order, created_at)
                VALUES (:id, :slug, :title, :body, :min_tier, :sort_order, :created_at)
                """
            ),
            {
                "id": uuid.uuid5(uuid.NAMESPACE_URL, f"promptsvault.lesson.{slug}"),
                "slug": slug,
                "title": title,
                "body": "This lesson has moved to the new learning runtime.",
                "min_tier": "free",
                "sort_order": index,
                "created_at": now,
            },
        )


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if not _has_table("learning_course_progress"):
        op.create_table(
            "learning_course_progress",
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("course_slug", sa.String(length=120), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
            sa.Column("completed_lessons", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_lessons", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_module_slug", sa.String(length=120), nullable=True),
            sa.Column("last_lesson_slug", sa.String(length=120), nullable=True),
            sa.Column("last_step_slug", sa.String(length=120), nullable=True),
            sa.Column("weak_areas", sa.JSON(), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "course_slug", name="uq_learning_course_progress_user_course"),
        )
    if not _has_index("learning_course_progress", "ix_learning_course_progress_user_status"):
        op.create_index(
            "ix_learning_course_progress_user_status",
            "learning_course_progress",
            ["user_id", "status", "last_activity_at"],
            unique=False,
        )

    if not _has_table("learning_lesson_progress"):
        op.create_table(
            "learning_lesson_progress",
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("course_slug", sa.String(length=120), nullable=False),
            sa.Column("module_slug", sa.String(length=120), nullable=False),
            sa.Column("lesson_slug", sa.String(length=120), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="in_progress"),
            sa.Column("completed_steps", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_steps", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("attempts_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_step_slug", sa.String(length=120), nullable=True),
            sa.Column("last_feedback", sa.JSON(), nullable=True),
            sa.Column("lmn_reward_granted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "course_slug", "lesson_slug", name="uq_learning_lesson_progress_user_lesson"),
        )
    if not _has_index("learning_lesson_progress", "ix_learning_lesson_progress_user_course"):
        op.create_index(
            "ix_learning_lesson_progress_user_course",
            "learning_lesson_progress",
            ["user_id", "course_slug", "status", "last_activity_at"],
            unique=False,
        )

    if not _has_table("learning_step_progress"):
        op.create_table(
            "learning_step_progress",
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("course_slug", sa.String(length=120), nullable=False),
            sa.Column("module_slug", sa.String(length=120), nullable=False),
            sa.Column("lesson_slug", sa.String(length=120), nullable=False),
            sa.Column("step_slug", sa.String(length=120), nullable=False),
            sa.Column("step_kind", sa.String(length=40), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="not_started"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("last_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("best_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("answer_json", sa.JSON(), nullable=True),
            sa.Column("feedback_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id",
                "course_slug",
                "lesson_slug",
                "step_slug",
                name="uq_learning_step_progress_user_step",
            ),
        )
    if not _has_index("learning_step_progress", "ix_learning_step_progress_user_lesson"):
        op.create_index(
            "ix_learning_step_progress_user_lesson",
            "learning_step_progress",
            ["user_id", "course_slug", "lesson_slug", "status"],
            unique=False,
        )

    if not _has_table("learning_reward_grants"):
        op.create_table(
            "learning_reward_grants",
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("grant_key", sa.String(length=180), nullable=False),
            sa.Column("reward_type", sa.String(length=40), nullable=False),
            sa.Column("course_slug", sa.String(length=120), nullable=True),
            sa.Column("lesson_slug", sa.String(length=120), nullable=True),
            sa.Column("lmn_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "grant_key", name="uq_learning_reward_grants_user_key"),
        )

    if not _has_table("learning_achievements"):
        op.create_table(
            "learning_achievements",
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("achievement_code", sa.String(length=180), nullable=False),
            sa.Column("course_slug", sa.String(length=120), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "achievement_code", name="uq_learning_achievements_user_code"),
        )

    _insert_learning_lessons()


def downgrade() -> None:
    if _has_table("learning_achievements"):
        op.drop_table("learning_achievements")
    if _has_table("learning_reward_grants"):
        op.drop_table("learning_reward_grants")
    if _has_index("learning_step_progress", "ix_learning_step_progress_user_lesson"):
        op.drop_index("ix_learning_step_progress_user_lesson", table_name="learning_step_progress")
    if _has_table("learning_step_progress"):
        op.drop_table("learning_step_progress")
    if _has_index("learning_lesson_progress", "ix_learning_lesson_progress_user_course"):
        op.drop_index("ix_learning_lesson_progress_user_course", table_name="learning_lesson_progress")
    if _has_table("learning_lesson_progress"):
        op.drop_table("learning_lesson_progress")
    if _has_index("learning_course_progress", "ix_learning_course_progress_user_status"):
        op.drop_index("ix_learning_course_progress_user_status", table_name="learning_course_progress")
    if _has_table("learning_course_progress"):
        op.drop_table("learning_course_progress")

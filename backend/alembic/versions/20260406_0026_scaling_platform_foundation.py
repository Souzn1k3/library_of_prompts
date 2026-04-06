"""scaling_platform_foundation

Revision ID: 20260406_0026
Revises: 20260406_0025
Create Date: 2026-04-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260406_0026"
down_revision = "20260406_0025"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("user_scenario_run_boosts"):
        op.create_table(
            "user_scenario_run_boosts",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("prompt_id", sa.Uuid(), nullable=False),
            sa.Column("bonus_runs_remaining", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "prompt_id", name="uq_user_scenario_run_boosts_user_prompt"),
        )
        op.create_index("ix_user_scenario_run_boosts_user_id", "user_scenario_run_boosts", ["user_id"])
        op.create_index("ix_user_scenario_run_boosts_prompt_id", "user_scenario_run_boosts", ["prompt_id"])

    if not _has_table("user_scenario_blueprints"):
        op.create_table(
            "user_scenario_blueprints",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("owner_user_id", sa.Uuid(), nullable=False),
            sa.Column("source_prompt_id", sa.Uuid(), nullable=True),
            sa.Column("forked_from_id", sa.Uuid(), nullable=True),
            sa.Column("slug", sa.String(length=180), nullable=False),
            sa.Column("title", sa.String(length=260), nullable=False),
            sa.Column("summary", sa.String(length=700), nullable=True),
            sa.Column("category", sa.String(length=40), nullable=False, server_default="utility"),
            sa.Column("visibility", sa.String(length=24), nullable=False, server_default="private"),
            sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("token_price", sa.Integer(), nullable=True),
            sa.Column("input_schema", sa.JSON(), nullable=True),
            sa.Column("context_text", sa.Text(), nullable=True),
            sa.Column("logic_text", sa.Text(), nullable=True),
            sa.Column("output_text", sa.Text(), nullable=True),
            sa.Column("run_instructions", sa.Text(), nullable=True),
            sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("fork_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["forked_from_id"], ["user_scenario_blueprints.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["source_prompt_id"], ["prompts.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("owner_user_id", "slug", name="uq_user_scenario_blueprints_owner_slug"),
        )
        op.create_index("ix_user_scenario_blueprints_owner_user_id", "user_scenario_blueprints", ["owner_user_id"])
        op.create_index("ix_user_scenario_blueprints_source_prompt_id", "user_scenario_blueprints", ["source_prompt_id"])
        op.create_index("ix_user_scenario_blueprints_forked_from_id", "user_scenario_blueprints", ["forked_from_id"])
        op.create_index("ix_user_scenario_blueprints_category", "user_scenario_blueprints", ["category"])
        op.create_index("ix_user_scenario_blueprints_visibility", "user_scenario_blueprints", ["visibility"])
        op.create_index("ix_user_scenario_blueprints_is_published", "user_scenario_blueprints", ["is_published"])

    if not _has_table("user_scenario_blueprint_shares"):
        op.create_table(
            "user_scenario_blueprint_shares",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("blueprint_id", sa.Uuid(), nullable=False),
            sa.Column("owner_user_id", sa.Uuid(), nullable=False),
            sa.Column("member_user_id", sa.Uuid(), nullable=False),
            sa.Column("can_edit", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["blueprint_id"], ["user_scenario_blueprints.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["member_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "blueprint_id",
                "member_user_id",
                name="uq_user_scenario_blueprint_shares_blueprint_member",
            ),
        )
        op.create_index("ix_user_scenario_blueprint_shares_blueprint_id", "user_scenario_blueprint_shares", ["blueprint_id"])
        op.create_index("ix_user_scenario_blueprint_shares_owner_user_id", "user_scenario_blueprint_shares", ["owner_user_id"])
        op.create_index("ix_user_scenario_blueprint_shares_member_user_id", "user_scenario_blueprint_shares", ["member_user_id"])

    if not _has_table("user_scenario_workflows"):
        op.create_table(
            "user_scenario_workflows",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("owner_user_id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(length=220), nullable=False),
            sa.Column("description", sa.String(length=600), nullable=True),
            sa.Column("visibility", sa.String(length=24), nullable=False, server_default="private"),
            sa.Column("step_blueprint_ids", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_user_scenario_workflows_owner_user_id", "user_scenario_workflows", ["owner_user_id"])
        op.create_index("ix_user_scenario_workflows_visibility", "user_scenario_workflows", ["visibility"])

    if not _has_table("user_scenario_workflow_runs"):
        op.create_table(
            "user_scenario_workflow_runs",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("workflow_id", sa.Uuid(), nullable=False),
            sa.Column("actor_user_id", sa.Uuid(), nullable=True),
            sa.Column("guest_id", sa.String(length=80), nullable=True),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="in_progress"),
            sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("completed_steps", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("context_json", sa.JSON(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["workflow_id"], ["user_scenario_workflows.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_user_scenario_workflow_runs_workflow_id", "user_scenario_workflow_runs", ["workflow_id"])
        op.create_index("ix_user_scenario_workflow_runs_actor_user_id", "user_scenario_workflow_runs", ["actor_user_id"])
        op.create_index("ix_user_scenario_workflow_runs_guest_id", "user_scenario_workflow_runs", ["guest_id"])
        op.create_index("ix_user_scenario_workflow_runs_status", "user_scenario_workflow_runs", ["status"])

    if not _has_table("scenario_output_showcases"):
        op.create_table(
            "scenario_output_showcases",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("share_id", sa.String(length=120), nullable=False),
            sa.Column("author_user_id", sa.Uuid(), nullable=True),
            sa.Column("prompt_slug", sa.String(length=200), nullable=True),
            sa.Column("blueprint_id", sa.Uuid(), nullable=True),
            sa.Column("title", sa.String(length=240), nullable=False),
            sa.Column("excerpt", sa.String(length=700), nullable=False),
            sa.Column("output_preview", sa.Text(), nullable=False),
            sa.Column("visibility", sa.String(length=24), nullable=False, server_default="public"),
            sa.Column("upvotes", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["blueprint_id"], ["user_scenario_blueprints.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_scenario_output_showcases_share_id", "scenario_output_showcases", ["share_id"], unique=True)
        op.create_index("ix_scenario_output_showcases_author_user_id", "scenario_output_showcases", ["author_user_id"])
        op.create_index("ix_scenario_output_showcases_prompt_slug", "scenario_output_showcases", ["prompt_slug"])
        op.create_index("ix_scenario_output_showcases_blueprint_id", "scenario_output_showcases", ["blueprint_id"])
        op.create_index("ix_scenario_output_showcases_visibility", "scenario_output_showcases", ["visibility"])
        op.create_index("ix_scenario_output_showcases_created_at", "scenario_output_showcases", ["created_at"])

    if not _has_table("scenario_creator_reward_events"):
        op.create_table(
            "scenario_creator_reward_events",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("event_key", sa.String(length=160), nullable=False),
            sa.Column("recipient_user_id", sa.Uuid(), nullable=False),
            sa.Column("blueprint_id", sa.Uuid(), nullable=True),
            sa.Column("reward_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("reason", sa.String(length=80), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["blueprint_id"], ["user_scenario_blueprints.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_scenario_creator_reward_events_event_key", "scenario_creator_reward_events", ["event_key"], unique=True)
        op.create_index("ix_scenario_creator_reward_events_recipient_user_id", "scenario_creator_reward_events", ["recipient_user_id"])
        op.create_index("ix_scenario_creator_reward_events_blueprint_id", "scenario_creator_reward_events", ["blueprint_id"])


def downgrade() -> None:
    if _has_table("scenario_creator_reward_events"):
        op.drop_index("ix_scenario_creator_reward_events_blueprint_id", table_name="scenario_creator_reward_events")
        op.drop_index("ix_scenario_creator_reward_events_recipient_user_id", table_name="scenario_creator_reward_events")
        op.drop_index("ix_scenario_creator_reward_events_event_key", table_name="scenario_creator_reward_events")
        op.drop_table("scenario_creator_reward_events")

    if _has_table("scenario_output_showcases"):
        op.drop_index("ix_scenario_output_showcases_created_at", table_name="scenario_output_showcases")
        op.drop_index("ix_scenario_output_showcases_visibility", table_name="scenario_output_showcases")
        op.drop_index("ix_scenario_output_showcases_blueprint_id", table_name="scenario_output_showcases")
        op.drop_index("ix_scenario_output_showcases_prompt_slug", table_name="scenario_output_showcases")
        op.drop_index("ix_scenario_output_showcases_author_user_id", table_name="scenario_output_showcases")
        op.drop_index("ix_scenario_output_showcases_share_id", table_name="scenario_output_showcases")
        op.drop_table("scenario_output_showcases")

    if _has_table("user_scenario_workflow_runs"):
        op.drop_index("ix_user_scenario_workflow_runs_status", table_name="user_scenario_workflow_runs")
        op.drop_index("ix_user_scenario_workflow_runs_guest_id", table_name="user_scenario_workflow_runs")
        op.drop_index("ix_user_scenario_workflow_runs_actor_user_id", table_name="user_scenario_workflow_runs")
        op.drop_index("ix_user_scenario_workflow_runs_workflow_id", table_name="user_scenario_workflow_runs")
        op.drop_table("user_scenario_workflow_runs")

    if _has_table("user_scenario_workflows"):
        op.drop_index("ix_user_scenario_workflows_visibility", table_name="user_scenario_workflows")
        op.drop_index("ix_user_scenario_workflows_owner_user_id", table_name="user_scenario_workflows")
        op.drop_table("user_scenario_workflows")

    if _has_table("user_scenario_blueprint_shares"):
        op.drop_index("ix_user_scenario_blueprint_shares_member_user_id", table_name="user_scenario_blueprint_shares")
        op.drop_index("ix_user_scenario_blueprint_shares_owner_user_id", table_name="user_scenario_blueprint_shares")
        op.drop_index("ix_user_scenario_blueprint_shares_blueprint_id", table_name="user_scenario_blueprint_shares")
        op.drop_table("user_scenario_blueprint_shares")

    if _has_table("user_scenario_blueprints"):
        op.drop_index("ix_user_scenario_blueprints_is_published", table_name="user_scenario_blueprints")
        op.drop_index("ix_user_scenario_blueprints_visibility", table_name="user_scenario_blueprints")
        op.drop_index("ix_user_scenario_blueprints_category", table_name="user_scenario_blueprints")
        op.drop_index("ix_user_scenario_blueprints_forked_from_id", table_name="user_scenario_blueprints")
        op.drop_index("ix_user_scenario_blueprints_source_prompt_id", table_name="user_scenario_blueprints")
        op.drop_index("ix_user_scenario_blueprints_owner_user_id", table_name="user_scenario_blueprints")
        op.drop_table("user_scenario_blueprints")

    if _has_table("user_scenario_run_boosts"):
        op.drop_index("ix_user_scenario_run_boosts_prompt_id", table_name="user_scenario_run_boosts")
        op.drop_index("ix_user_scenario_run_boosts_user_id", table_name="user_scenario_run_boosts")
        op.drop_table("user_scenario_run_boosts")

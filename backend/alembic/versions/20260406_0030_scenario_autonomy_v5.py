"""scenario_autonomy_v5

Revision ID: 20260406_0030
Revises: 20260406_0029
Create Date: 2026-04-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260406_0030"
down_revision = "20260406_0029"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(column.get("name") == column_name for column in inspector.get_columns(table_name))


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if _has_table("user_scenario_blueprints"):
        if not _has_column("user_scenario_blueprints", "autonomous_mode"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("autonomous_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
            )
        if not _has_column("user_scenario_blueprints", "autonomous_stage"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("autonomous_stage", sa.String(length=24), nullable=False, server_default="manual"),
            )
        if not _has_column("user_scenario_blueprints", "autonomous_quality_score"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("autonomous_quality_score", sa.Float(), nullable=False, server_default="0"),
            )
        if not _has_column("user_scenario_blueprints", "autonomous_target_segment"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("autonomous_target_segment", sa.String(length=120), nullable=True),
            )
        if not _has_column("user_scenario_blueprints", "autonomous_last_iteration_at"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("autonomous_last_iteration_at", sa.DateTime(timezone=True), nullable=True),
            )

        if not _has_index("user_scenario_blueprints", "ix_user_scenario_blueprints_autonomous_mode"):
            op.create_index(
                "ix_user_scenario_blueprints_autonomous_mode",
                "user_scenario_blueprints",
                ["autonomous_mode"],
            )
        if not _has_index("user_scenario_blueprints", "ix_user_scenario_blueprints_autonomous_stage"):
            op.create_index(
                "ix_user_scenario_blueprints_autonomous_stage",
                "user_scenario_blueprints",
                ["autonomous_stage"],
            )
        if not _has_index("user_scenario_blueprints", "ix_user_scenario_blueprints_autonomous_target_segment"):
            op.create_index(
                "ix_user_scenario_blueprints_autonomous_target_segment",
                "user_scenario_blueprints",
                ["autonomous_target_segment"],
            )
        if not _has_index("user_scenario_blueprints", "ix_user_scenario_blueprints_autonomous_last_iteration_at"):
            op.create_index(
                "ix_user_scenario_blueprints_autonomous_last_iteration_at",
                "user_scenario_blueprints",
                ["autonomous_last_iteration_at"],
            )

    if not _has_table("scenario_autonomy_cycles"):
        op.create_table(
            "scenario_autonomy_cycles",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("trigger", sa.String(length=24), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("generated_count", sa.Integer(), nullable=False),
            sa.Column("published_count", sa.Integer(), nullable=False),
            sa.Column("iterations_count", sa.Integer(), nullable=False),
            sa.Column("notes_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_scenario_autonomy_cycles_trigger", "scenario_autonomy_cycles", ["trigger"])
        op.create_index("ix_scenario_autonomy_cycles_status", "scenario_autonomy_cycles", ["status"])
        op.create_index("ix_scenario_autonomy_cycles_started_at", "scenario_autonomy_cycles", ["started_at"])

    if not _has_table("scenario_autonomy_experiments"):
        op.create_table(
            "scenario_autonomy_experiments",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("cycle_id", sa.Uuid(), nullable=False),
            sa.Column("blueprint_id", sa.Uuid(), nullable=True),
            sa.Column("experiment_key", sa.String(length=120), nullable=False),
            sa.Column("dimension", sa.String(length=40), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False),
            sa.Column("control_variant", sa.String(length=120), nullable=False),
            sa.Column("treatment_variant", sa.String(length=120), nullable=False),
            sa.Column("winner_variant", sa.String(length=120), nullable=True),
            sa.Column("baseline_metrics_json", sa.JSON(), nullable=False),
            sa.Column("outcome_metrics_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["cycle_id"], ["scenario_autonomy_cycles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["blueprint_id"], ["user_scenario_blueprints.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_scenario_autonomy_experiments_cycle_id", "scenario_autonomy_experiments", ["cycle_id"])
        op.create_index("ix_scenario_autonomy_experiments_blueprint_id", "scenario_autonomy_experiments", ["blueprint_id"])
        op.create_index(
            "ix_scenario_autonomy_experiments_experiment_key",
            "scenario_autonomy_experiments",
            ["experiment_key"],
        )
        op.create_index("ix_scenario_autonomy_experiments_dimension", "scenario_autonomy_experiments", ["dimension"])
        op.create_index("ix_scenario_autonomy_experiments_status", "scenario_autonomy_experiments", ["status"])

    if not _has_table("scenario_autonomy_growth_decisions"):
        op.create_table(
            "scenario_autonomy_growth_decisions",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("cycle_id", sa.Uuid(), nullable=False),
            sa.Column("source", sa.String(length=120), nullable=False),
            sa.Column("campaign", sa.String(length=160), nullable=True),
            sa.Column("action", sa.String(length=40), nullable=False),
            sa.Column("rationale_json", sa.JSON(), nullable=False),
            sa.Column("before_state_json", sa.JSON(), nullable=False),
            sa.Column("after_state_json", sa.JSON(), nullable=False),
            sa.Column("guardrail_passed", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["cycle_id"], ["scenario_autonomy_cycles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_scenario_autonomy_growth_decisions_cycle_id",
            "scenario_autonomy_growth_decisions",
            ["cycle_id"],
        )
        op.create_index(
            "ix_scenario_autonomy_growth_decisions_source",
            "scenario_autonomy_growth_decisions",
            ["source"],
        )
        op.create_index(
            "ix_scenario_autonomy_growth_decisions_campaign",
            "scenario_autonomy_growth_decisions",
            ["campaign"],
        )
        op.create_index(
            "ix_scenario_autonomy_growth_decisions_action",
            "scenario_autonomy_growth_decisions",
            ["action"],
        )

    if not _has_table("scenario_autonomy_guardrail_events"):
        op.create_table(
            "scenario_autonomy_guardrail_events",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("cycle_id", sa.Uuid(), nullable=False),
            sa.Column("scope", sa.String(length=40), nullable=False),
            sa.Column("rule_key", sa.String(length=120), nullable=False),
            sa.Column("severity", sa.String(length=24), nullable=False),
            sa.Column("triggered", sa.Boolean(), nullable=False),
            sa.Column("details_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["cycle_id"], ["scenario_autonomy_cycles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_scenario_autonomy_guardrail_events_cycle_id",
            "scenario_autonomy_guardrail_events",
            ["cycle_id"],
        )
        op.create_index(
            "ix_scenario_autonomy_guardrail_events_scope",
            "scenario_autonomy_guardrail_events",
            ["scope"],
        )
        op.create_index(
            "ix_scenario_autonomy_guardrail_events_rule_key",
            "scenario_autonomy_guardrail_events",
            ["rule_key"],
        )
        op.create_index(
            "ix_scenario_autonomy_guardrail_events_triggered",
            "scenario_autonomy_guardrail_events",
            ["triggered"],
        )

    if not _has_table("scenario_autonomy_personalization_profiles"):
        op.create_table(
            "scenario_autonomy_personalization_profiles",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("ui_variant", sa.String(length=80), nullable=False),
            sa.Column("paywall_variant", sa.String(length=80), nullable=False),
            sa.Column("pricing_variant", sa.String(length=80), nullable=False),
            sa.Column("preferred_categories", sa.JSON(), nullable=False),
            sa.Column("recommended_blueprint_ids", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index(
            "ix_scenario_autonomy_personalization_profiles_user_id",
            "scenario_autonomy_personalization_profiles",
            ["user_id"],
        )


def downgrade() -> None:
    if _has_table("scenario_autonomy_personalization_profiles"):
        if _has_index(
            "scenario_autonomy_personalization_profiles",
            "ix_scenario_autonomy_personalization_profiles_user_id",
        ):
            op.drop_index(
                "ix_scenario_autonomy_personalization_profiles_user_id",
                table_name="scenario_autonomy_personalization_profiles",
            )
        op.drop_table("scenario_autonomy_personalization_profiles")

    if _has_table("scenario_autonomy_guardrail_events"):
        for index_name in (
            "ix_scenario_autonomy_guardrail_events_triggered",
            "ix_scenario_autonomy_guardrail_events_rule_key",
            "ix_scenario_autonomy_guardrail_events_scope",
            "ix_scenario_autonomy_guardrail_events_cycle_id",
        ):
            if _has_index("scenario_autonomy_guardrail_events", index_name):
                op.drop_index(index_name, table_name="scenario_autonomy_guardrail_events")
        op.drop_table("scenario_autonomy_guardrail_events")

    if _has_table("scenario_autonomy_growth_decisions"):
        for index_name in (
            "ix_scenario_autonomy_growth_decisions_action",
            "ix_scenario_autonomy_growth_decisions_campaign",
            "ix_scenario_autonomy_growth_decisions_source",
            "ix_scenario_autonomy_growth_decisions_cycle_id",
        ):
            if _has_index("scenario_autonomy_growth_decisions", index_name):
                op.drop_index(index_name, table_name="scenario_autonomy_growth_decisions")
        op.drop_table("scenario_autonomy_growth_decisions")

    if _has_table("scenario_autonomy_experiments"):
        for index_name in (
            "ix_scenario_autonomy_experiments_status",
            "ix_scenario_autonomy_experiments_dimension",
            "ix_scenario_autonomy_experiments_experiment_key",
            "ix_scenario_autonomy_experiments_blueprint_id",
            "ix_scenario_autonomy_experiments_cycle_id",
        ):
            if _has_index("scenario_autonomy_experiments", index_name):
                op.drop_index(index_name, table_name="scenario_autonomy_experiments")
        op.drop_table("scenario_autonomy_experiments")

    if _has_table("scenario_autonomy_cycles"):
        for index_name in (
            "ix_scenario_autonomy_cycles_started_at",
            "ix_scenario_autonomy_cycles_status",
            "ix_scenario_autonomy_cycles_trigger",
        ):
            if _has_index("scenario_autonomy_cycles", index_name):
                op.drop_index(index_name, table_name="scenario_autonomy_cycles")
        op.drop_table("scenario_autonomy_cycles")

    if _has_table("user_scenario_blueprints"):
        for index_name in (
            "ix_user_scenario_blueprints_autonomous_last_iteration_at",
            "ix_user_scenario_blueprints_autonomous_target_segment",
            "ix_user_scenario_blueprints_autonomous_stage",
            "ix_user_scenario_blueprints_autonomous_mode",
        ):
            if _has_index("user_scenario_blueprints", index_name):
                op.drop_index(index_name, table_name="user_scenario_blueprints")
        for column_name in (
            "autonomous_last_iteration_at",
            "autonomous_target_segment",
            "autonomous_quality_score",
            "autonomous_stage",
            "autonomous_mode",
        ):
            if _has_column("user_scenario_blueprints", column_name):
                op.drop_column("user_scenario_blueprints", column_name)

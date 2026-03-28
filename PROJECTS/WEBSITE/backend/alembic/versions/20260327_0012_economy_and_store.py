"""economy_and_store

Revision ID: 20260327_0012
Revises: 20260324_0011
Create Date: 2026-03-27
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260327_0012"
down_revision = "20260324_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    lesson_mission_cols = {column["name"] for column in inspector.get_columns("lesson_missions")}
    lesson_mission_indexes = {index["name"] for index in inspector.get_indexes("lesson_missions")}
    mission_completion_event_cols = {
        column["name"] for column in inspector.get_columns("mission_completion_events")
    }
    mission_completion_event_indexes = {
        index["name"] for index in inspector.get_indexes("mission_completion_events")
    }
    mission_completion_event_fks = {
        foreign_key.get("name")
        for foreign_key in inspector.get_foreign_keys("mission_completion_events")
        if foreign_key.get("name")
    }
    currency_transaction_indexes = (
        {index["name"] for index in inspector.get_indexes("currency_transactions")}
        if "currency_transactions" in tables
        else set()
    )
    user_purchase_indexes = (
        {index["name"] for index in inspector.get_indexes("user_purchases")}
        if "user_purchases" in tables
        else set()
    )

    if "difficulty" not in lesson_mission_cols:
        op.add_column(
            "lesson_missions",
            sa.Column("difficulty", sa.String(length=24), nullable=False, server_default="standard"),
        )
        op.alter_column("lesson_missions", "difficulty", server_default=None)
    if "ix_lesson_missions_difficulty" not in lesson_mission_indexes:
        op.create_index("ix_lesson_missions_difficulty", "lesson_missions", ["difficulty"])

    if "mission_steps" not in tables:
        op.create_table(
            "mission_steps",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("mission_id", sa.Uuid(as_uuid=True), sa.ForeignKey("lesson_missions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.String(length=500)),
            sa.Column("action_type", sa.String(length=40), nullable=False),
            sa.Column("required_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("target_prompt_id", sa.Uuid(as_uuid=True), sa.ForeignKey("prompts.id", ondelete="SET NULL")),
            sa.Column("target_lesson_id", sa.Uuid(as_uuid=True), sa.ForeignKey("lessons.id", ondelete="SET NULL")),
            sa.Column("reward_credits", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    if "user_mission_step_progress" not in tables:
        op.create_table(
            "user_mission_step_progress",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("mission_step_id", sa.Uuid(as_uuid=True), sa.ForeignKey("mission_steps.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="not_started"),
            sa.Column("progress_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("required_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("started_at", sa.DateTime(timezone=True)),
            sa.Column("last_event_at", sa.DateTime(timezone=True)),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("user_id", "mission_step_id", name="uq_user_mission_step_progress"),
        )

    if "mission_step_id" not in mission_completion_event_cols:
        op.add_column(
            "mission_completion_events",
            sa.Column("mission_step_id", sa.Uuid(as_uuid=True), nullable=True),
        )
    if "ix_mission_completion_events_mission_step_id" not in mission_completion_event_indexes:
        op.create_index(
            "ix_mission_completion_events_mission_step_id",
            "mission_completion_events",
            ["mission_step_id"],
        )
    if "fk_mission_completion_events_step" not in mission_completion_event_fks:
        op.create_foreign_key(
            "fk_mission_completion_events_step",
            "mission_completion_events",
            "mission_steps",
            ["mission_step_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if "user_currency_balances" not in tables:
        op.create_table(
            "user_currency_balances",
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_earned", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_spent", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    if "currency_transactions" not in tables:
        op.create_table(
            "currency_transactions",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("amount", sa.Integer(), nullable=False),
            sa.Column("balance_after", sa.Integer(), nullable=False),
            sa.Column("reason", sa.String(length=40), nullable=False),
            sa.Column("context", sa.String(length=200)),
            sa.Column("source_id", sa.Uuid(as_uuid=True)),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        currency_transaction_indexes = set()
    if "ix_currency_transactions_user_id" not in currency_transaction_indexes:
        op.create_index("ix_currency_transactions_user_id", "currency_transactions", ["user_id"])
    if "ix_currency_transactions_reason" not in currency_transaction_indexes:
        op.create_index("ix_currency_transactions_reason", "currency_transactions", ["reason"])

    if "store_items" not in tables:
        op.create_table(
            "store_items",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("slug", sa.String(length=160), nullable=False, unique=True),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.String(length=500)),
            sa.Column("price", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("kind", sa.String(length=40), nullable=False, server_default="premium_pass"),
            sa.Column("availability", sa.Integer(), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    if "user_purchases" not in tables:
        op.create_table(
            "user_purchases",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("store_item_id", sa.Uuid(as_uuid=True), sa.ForeignKey("store_items.id", ondelete="CASCADE"), nullable=False),
            sa.Column("price_paid", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        user_purchase_indexes = set()
    if "ix_user_purchases_user_id" not in user_purchase_indexes:
        op.create_index("ix_user_purchases_user_id", "user_purchases", ["user_id"])
    if "ix_user_purchases_store_item_id" not in user_purchase_indexes:
        op.create_index("ix_user_purchases_store_item_id", "user_purchases", ["store_item_id"])


def downgrade() -> None:
    op.drop_index("ix_user_purchases_store_item_id", table_name="user_purchases")
    op.drop_index("ix_user_purchases_user_id", table_name="user_purchases")
    op.drop_table("user_purchases")

    op.drop_table("store_items")

    op.drop_index("ix_currency_transactions_reason", table_name="currency_transactions")
    op.drop_index("ix_currency_transactions_user_id", table_name="currency_transactions")
    op.drop_table("currency_transactions")

    op.drop_table("user_currency_balances")

    op.drop_constraint("fk_mission_completion_events_step", "mission_completion_events", type_="foreignkey")
    op.drop_index("ix_mission_completion_events_mission_step_id", table_name="mission_completion_events")
    op.drop_column("mission_completion_events", "mission_step_id")

    op.drop_table("user_mission_step_progress")
    op.drop_table("mission_steps")

    op.execute("DROP INDEX IF EXISTS ix_lesson_missions_difficulty")
    op.drop_column("lesson_missions", "difficulty")

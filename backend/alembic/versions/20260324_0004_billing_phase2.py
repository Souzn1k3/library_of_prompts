"""phase2 billing tables

Revision ID: 20260324_0004
Revises: 20250321_0003
Create Date: 2026-03-24

"""

from collections.abc import Sequence
from datetime import datetime, timezone
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "20260324_0004"
down_revision: str | None = "20250321_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "plans" not in tables:
        op.create_table(
            "plans",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("tier", sa.String(length=32), nullable=False, unique=True),
            sa.Column("name", sa.String(length=80), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column("price_usd_month", sa.Integer(), nullable=False),
            sa.Column("stripe_price_id", sa.String(length=128), nullable=True, unique=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_plans_tier", "plans", ["tier"], unique=True)

    plan_columns = set()
    if "plans" in sa.inspect(bind).get_table_names():
        plan_columns = {column["name"] for column in sa.inspect(bind).get_columns("plans")}

    if "billing_customers" not in tables:
        op.create_table(
            "billing_customers",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("provider", sa.String(length=16), nullable=False),
            sa.Column("provider_customer_id", sa.String(length=128), nullable=False, unique=True),
            sa.Column("email", sa.String(length=320), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_billing_customers_user_id",
            "billing_customers",
            ["user_id"],
            unique=True,
        )
        op.create_index(
            "ix_billing_customers_provider_customer_id",
            "billing_customers",
            ["provider_customer_id"],
            unique=True,
        )

    if "subscriptions" not in tables:
        op.create_table(
            "subscriptions",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "plan_id",
                sa.Uuid(),
                sa.ForeignKey("plans.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("provider", sa.String(length=16), nullable=False),
            sa.Column("provider_subscription_id", sa.String(length=128), nullable=False, unique=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"], unique=False)
        op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"], unique=False)
        op.create_index(
            "ix_subscriptions_provider_subscription_id",
            "subscriptions",
            ["provider_subscription_id"],
            unique=True,
        )
        op.create_index("ix_subscriptions_status", "subscriptions", ["status"], unique=False)

    if "subscription_events" not in tables:
        op.create_table(
            "subscription_events",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column(
                "subscription_id",
                sa.Uuid(),
                sa.ForeignKey("subscriptions.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("provider", sa.String(length=16), nullable=False),
            sa.Column("provider_event_id", sa.String(length=128), nullable=False),
            sa.Column("event_type", sa.String(length=120), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "provider",
                "provider_event_id",
                "subscription_id",
                name="uq_subscription_event_provider_event_subscription",
            ),
        )
        op.create_index(
            "ix_subscription_events_subscription_id",
            "subscription_events",
            ["subscription_id"],
            unique=False,
        )
        op.create_index("ix_subscription_events_user_id", "subscription_events", ["user_id"], unique=False)
        op.create_index(
            "ix_subscription_events_provider_event_id",
            "subscription_events",
            ["provider_event_id"],
            unique=False,
        )

    if "processed_webhook_events" not in tables:
        op.create_table(
            "processed_webhook_events",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("provider", sa.String(length=16), nullable=False),
            sa.Column("event_id", sa.String(length=128), nullable=False),
            sa.Column("payload_hash", sa.String(length=64), nullable=True),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "provider",
                "event_id",
                name="uq_processed_webhook_events_provider_event",
            ),
        )

    plans_table = sa.table(
        "plans",
        sa.column("id", sa.Uuid()),
        sa.column("tier", sa.String(length=32)),
        sa.column("name", sa.String(length=80)),
        sa.column("description", sa.String(length=255)),
        sa.column("price_usd_month", sa.Integer()),
        *((
            sa.column("price_rub_month", sa.Integer()),
            sa.column("monthly_paid_prompt_limit", sa.Integer()),
            sa.column("prompt_purchase_discount_percent", sa.Integer()),
            sa.column("lumen_purchase_discount_percent", sa.Integer()),
        ) if "price_rub_month" in plan_columns else ()),
        sa.column("stripe_price_id", sa.String(length=128)),
        sa.column("is_active", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    existing_tiers = {
        row[0]
        for row in bind.execute(sa.text("SELECT tier FROM plans")).fetchall()
    }

    now = _utcnow()
    rows: list[dict[str, object]] = []
    defaults = [
        ("free", "Free", "Browse, save, and submit prompts.", 0, 0),
        ("starter", "Starter", "Unlock premium prompt bodies.", 9, 1),
        ("pro", "Pro", "Access full lessons and restricted categories.", 29, 2),
        ("enterprise", "Enterprise", "Team features and dedicated support.", 99, 3),
    ]
    for tier, name, description, price, order in defaults:
        if tier in existing_tiers:
            continue
        rows.append(
            {
                "id": uuid.uuid4(),
                "tier": tier,
                "name": name,
                "description": description,
                "price_usd_month": price,
                **(
                    {
                        "price_rub_month": 0,
                        "monthly_paid_prompt_limit": 0,
                        "prompt_purchase_discount_percent": 0,
                        "lumen_purchase_discount_percent": 0,
                    }
                    if "price_rub_month" in plan_columns
                    else {}
                ),
                "stripe_price_id": None,
                "is_active": True,
                "sort_order": order,
                "created_at": now,
                "updated_at": now,
            }
        )
    if rows:
        op.bulk_insert(plans_table, rows)


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "processed_webhook_events" in tables:
        op.drop_table("processed_webhook_events")

    if "subscription_events" in tables:
        op.drop_index("ix_subscription_events_provider_event_id", table_name="subscription_events")
        op.drop_index("ix_subscription_events_user_id", table_name="subscription_events")
        op.drop_index("ix_subscription_events_subscription_id", table_name="subscription_events")
        op.drop_table("subscription_events")

    if "subscriptions" in tables:
        op.drop_index("ix_subscriptions_status", table_name="subscriptions")
        op.drop_index("ix_subscriptions_provider_subscription_id", table_name="subscriptions")
        op.drop_index("ix_subscriptions_plan_id", table_name="subscriptions")
        op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
        op.drop_table("subscriptions")

    if "billing_customers" in tables:
        op.drop_index("ix_billing_customers_provider_customer_id", table_name="billing_customers")
        op.drop_index("ix_billing_customers_user_id", table_name="billing_customers")
        op.drop_table("billing_customers")

    if "plans" in tables:
        op.drop_index("ix_plans_tier", table_name="plans")
        op.drop_table("plans")

"""marketplace foundation

Revision ID: 20260330_0016
Revises: 20260328_0015
Create Date: 2026-03-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260330_0016"
down_revision: str | None = "20260328_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_columns(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_indexes(inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "plans" in tables:
        plan_cols = _table_columns(inspector, "plans")
        if "price_rub_month" not in plan_cols:
            op.add_column(
                "plans",
                sa.Column("price_rub_month", sa.Integer(), nullable=False, server_default="0"),
            )
        if "monthly_paid_prompt_limit" not in plan_cols:
            op.add_column(
                "plans",
                sa.Column("monthly_paid_prompt_limit", sa.Integer(), nullable=False, server_default="0"),
            )
        if "prompt_purchase_discount_percent" not in plan_cols:
            op.add_column(
                "plans",
                sa.Column("prompt_purchase_discount_percent", sa.Integer(), nullable=False, server_default="0"),
            )
        if "lumen_purchase_discount_percent" not in plan_cols:
            op.add_column(
                "plans",
                sa.Column("lumen_purchase_discount_percent", sa.Integer(), nullable=False, server_default="0"),
            )

        bind.execute(
            sa.text(
                """
                UPDATE plans
                SET
                    name = :name,
                    description = :description,
                    price_usd_month = :price_usd_month,
                    price_rub_month = :price_rub_month,
                    monthly_paid_prompt_limit = :monthly_paid_prompt_limit,
                    prompt_purchase_discount_percent = :prompt_purchase_discount_percent,
                    lumen_purchase_discount_percent = :lumen_purchase_discount_percent,
                    sort_order = :sort_order
                WHERE tier = :tier
                """
            ),
            [
                {
                    "tier": "free",
                    "name": "Free",
                    "description": "Free prompts, saved library, and a small monthly paid prompt quota.",
                    "price_usd_month": 0,
                    "price_rub_month": 0,
                    "monthly_paid_prompt_limit": 2,
                    "prompt_purchase_discount_percent": 0,
                    "lumen_purchase_discount_percent": 0,
                    "sort_order": 0,
                },
                {
                    "tier": "starter",
                    "name": "Starter",
                    "description": "Low-cost monthly access with a healthy paid prompt allowance.",
                    "price_usd_month": 2,
                    "price_rub_month": 200,
                    "monthly_paid_prompt_limit": 15,
                    "prompt_purchase_discount_percent": 5,
                    "lumen_purchase_discount_percent": 8,
                    "sort_order": 1,
                },
                {
                    "tier": "pro",
                    "name": "Pro",
                    "description": "Main growth plan for active buyers and sellers.",
                    "price_usd_month": 10,
                    "price_rub_month": 1000,
                    "monthly_paid_prompt_limit": 60,
                    "prompt_purchase_discount_percent": 12,
                    "lumen_purchase_discount_percent": 15,
                    "sort_order": 2,
                },
                {
                    "tier": "enterprise",
                    "name": "MAX",
                    "description": "Best value for creators, teams, and heavy marketplace usage.",
                    "price_usd_month": 12,
                    "price_rub_month": 1200,
                    "monthly_paid_prompt_limit": 90,
                    "prompt_purchase_discount_percent": 15,
                    "lumen_purchase_discount_percent": 20,
                    "sort_order": 3,
                },
            ],
        )

    if "prompt_prices" not in tables:
        op.create_table(
            "prompt_prices",
            sa.Column(
                "prompt_id",
                sa.Uuid(as_uuid=True),
                sa.ForeignKey("prompts.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column("price_rub", sa.Integer(), nullable=False),
            sa.Column("price_lumens", sa.Integer(), nullable=False),
            sa.Column("commission_percent", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_prompt_prices_is_active", "prompt_prices", ["is_active"])

    if "plan_usage_windows" not in tables:
        op.create_table(
            "plan_usage_windows",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("plan_tier", sa.String(length=32), nullable=False),
            sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("window_ends_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("included_paid_prompt_limit", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("used_paid_prompt_unlocks", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint(
                "user_id",
                "plan_tier",
                "window_started_at",
                "window_ends_at",
                name="uq_plan_usage_windows_scope",
            ),
        )
        op.create_index("ix_plan_usage_windows_user_id", "plan_usage_windows", ["user_id"])
        op.create_index("ix_plan_usage_windows_plan_tier", "plan_usage_windows", ["plan_tier"])

    if "prompt_purchases" not in tables:
        op.create_table(
            "prompt_purchases",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("prompt_id", sa.Uuid(as_uuid=True), sa.ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("seller_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("payment_method", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("price_rub", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("price_lumens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("platform_fee_rub", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("seller_amount_rub", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("platform_fee_lumens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("seller_amount_lumens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("provider_checkout_id", sa.String(length=128), nullable=True, unique=True),
            sa.Column("provider_payment_id", sa.String(length=128), nullable=True, unique=True),
            sa.Column("client_token", sa.String(length=80), nullable=True, unique=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_prompt_purchases_user_id", "prompt_purchases", ["user_id"])
        op.create_index("ix_prompt_purchases_prompt_id", "prompt_purchases", ["prompt_id"])
        op.create_index("ix_prompt_purchases_seller_user_id", "prompt_purchases", ["seller_user_id"])
        op.create_index("ix_prompt_purchases_payment_method", "prompt_purchases", ["payment_method"])
        op.create_index("ix_prompt_purchases_status", "prompt_purchases", ["status"])
        op.create_index("ix_prompt_purchases_provider_checkout_id", "prompt_purchases", ["provider_checkout_id"], unique=True)
        op.create_index("ix_prompt_purchases_provider_payment_id", "prompt_purchases", ["provider_payment_id"], unique=True)
        op.create_index("ix_prompt_purchases_client_token", "prompt_purchases", ["client_token"], unique=True)

    if "prompt_entitlements" not in tables:
        op.create_table(
            "prompt_entitlements",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("prompt_id", sa.Uuid(as_uuid=True), sa.ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("purchase_id", sa.Uuid(as_uuid=True), sa.ForeignKey("prompt_purchases.id", ondelete="SET NULL"), nullable=True, unique=True),
            sa.Column("source", sa.String(length=32), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoke_reason", sa.String(length=200), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("user_id", "prompt_id", name="uq_prompt_entitlements_user_prompt"),
        )
        op.create_index("ix_prompt_entitlements_user_id", "prompt_entitlements", ["user_id"])
        op.create_index("ix_prompt_entitlements_prompt_id", "prompt_entitlements", ["prompt_id"])
        op.create_index("ix_prompt_entitlements_purchase_id", "prompt_entitlements", ["purchase_id"], unique=True)
        op.create_index("ix_prompt_entitlements_source", "prompt_entitlements", ["source"])

    if "prompt_reviews" not in tables:
        op.create_table(
            "prompt_reviews",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("prompt_purchase_id", sa.Uuid(as_uuid=True), sa.ForeignKey("prompt_purchases.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("prompt_id", sa.Uuid(as_uuid=True), sa.ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("seller_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("author_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("rating", sa.Integer(), nullable=False),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_prompt_reviews_prompt_purchase_id", "prompt_reviews", ["prompt_purchase_id"], unique=True)
        op.create_index("ix_prompt_reviews_prompt_id", "prompt_reviews", ["prompt_id"])
        op.create_index("ix_prompt_reviews_seller_user_id", "prompt_reviews", ["seller_user_id"])
        op.create_index("ix_prompt_reviews_author_user_id", "prompt_reviews", ["author_user_id"])
        op.create_index("ix_prompt_reviews_is_visible", "prompt_reviews", ["is_visible"])

    if "marketplace_transactions" not in tables:
        op.create_table(
            "marketplace_transactions",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("prompt_purchase_id", sa.Uuid(as_uuid=True), sa.ForeignKey("prompt_purchases.id", ondelete="SET NULL"), nullable=True),
            sa.Column("prompt_id", sa.Uuid(as_uuid=True), sa.ForeignKey("prompts.id", ondelete="SET NULL"), nullable=True),
            sa.Column("actor_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("kind", sa.String(length=32), nullable=False),
            sa.Column("currency_code", sa.String(length=8), nullable=False),
            sa.Column("amount", sa.Integer(), nullable=False),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_marketplace_transactions_prompt_purchase_id", "marketplace_transactions", ["prompt_purchase_id"])
        op.create_index("ix_marketplace_transactions_prompt_id", "marketplace_transactions", ["prompt_id"])
        op.create_index("ix_marketplace_transactions_actor_user_id", "marketplace_transactions", ["actor_user_id"])
        op.create_index("ix_marketplace_transactions_kind", "marketplace_transactions", ["kind"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "marketplace_transactions" in tables:
        op.drop_index("ix_marketplace_transactions_kind", table_name="marketplace_transactions")
        op.drop_index("ix_marketplace_transactions_actor_user_id", table_name="marketplace_transactions")
        op.drop_index("ix_marketplace_transactions_prompt_id", table_name="marketplace_transactions")
        op.drop_index("ix_marketplace_transactions_prompt_purchase_id", table_name="marketplace_transactions")
        op.drop_table("marketplace_transactions")

    if "prompt_reviews" in tables:
        op.drop_index("ix_prompt_reviews_is_visible", table_name="prompt_reviews")
        op.drop_index("ix_prompt_reviews_author_user_id", table_name="prompt_reviews")
        op.drop_index("ix_prompt_reviews_seller_user_id", table_name="prompt_reviews")
        op.drop_index("ix_prompt_reviews_prompt_id", table_name="prompt_reviews")
        op.drop_index("ix_prompt_reviews_prompt_purchase_id", table_name="prompt_reviews")
        op.drop_table("prompt_reviews")

    if "prompt_entitlements" in tables:
        op.drop_index("ix_prompt_entitlements_source", table_name="prompt_entitlements")
        op.drop_index("ix_prompt_entitlements_purchase_id", table_name="prompt_entitlements")
        op.drop_index("ix_prompt_entitlements_prompt_id", table_name="prompt_entitlements")
        op.drop_index("ix_prompt_entitlements_user_id", table_name="prompt_entitlements")
        op.drop_table("prompt_entitlements")

    if "prompt_purchases" in tables:
        op.drop_index("ix_prompt_purchases_client_token", table_name="prompt_purchases")
        op.drop_index("ix_prompt_purchases_provider_payment_id", table_name="prompt_purchases")
        op.drop_index("ix_prompt_purchases_provider_checkout_id", table_name="prompt_purchases")
        op.drop_index("ix_prompt_purchases_status", table_name="prompt_purchases")
        op.drop_index("ix_prompt_purchases_payment_method", table_name="prompt_purchases")
        op.drop_index("ix_prompt_purchases_seller_user_id", table_name="prompt_purchases")
        op.drop_index("ix_prompt_purchases_prompt_id", table_name="prompt_purchases")
        op.drop_index("ix_prompt_purchases_user_id", table_name="prompt_purchases")
        op.drop_table("prompt_purchases")

    if "plan_usage_windows" in tables:
        op.drop_index("ix_plan_usage_windows_plan_tier", table_name="plan_usage_windows")
        op.drop_index("ix_plan_usage_windows_user_id", table_name="plan_usage_windows")
        op.drop_table("plan_usage_windows")

    if "prompt_prices" in tables:
        op.drop_index("ix_prompt_prices_is_active", table_name="prompt_prices")
        op.drop_table("prompt_prices")

    if "plans" in tables:
        plan_cols = _table_columns(inspector, "plans")
        if "lumen_purchase_discount_percent" in plan_cols:
            op.drop_column("plans", "lumen_purchase_discount_percent")
        if "prompt_purchase_discount_percent" in plan_cols:
            op.drop_column("plans", "prompt_purchase_discount_percent")
        if "monthly_paid_prompt_limit" in plan_cols:
            op.drop_column("plans", "monthly_paid_prompt_limit")
        if "price_rub_month" in plan_cols:
            op.drop_column("plans", "price_rub_month")

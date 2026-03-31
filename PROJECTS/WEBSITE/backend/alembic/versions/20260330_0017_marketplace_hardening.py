"""marketplace hardening

Revision ID: 20260330_0017
Revises: 20260330_0016
Create Date: 2026-03-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260330_0017"
down_revision: str | None = "20260330_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_columns(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "marketplace_payouts" not in tables:
        op.create_table(
            "marketplace_payouts",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("seller_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("currency_code", sa.String(length=8), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="requested"),
            sa.Column("total_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("purchase_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("external_reference", sa.String(length=120), nullable=True),
            sa.Column("notes", sa.String(length=500), nullable=True),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_marketplace_payouts_seller_user_id", "marketplace_payouts", ["seller_user_id"])
        op.create_index("ix_marketplace_payouts_status", "marketplace_payouts", ["status"])

    if "prompt_purchases" in tables:
        purchase_cols = _table_columns(inspector, "prompt_purchases")
        if "settlement_status" not in purchase_cols:
            op.add_column(
                "prompt_purchases",
                sa.Column("settlement_status", sa.String(length=32), nullable=False, server_default="pending"),
            )
        if "settlement_available_at" not in purchase_cols:
            op.add_column("prompt_purchases", sa.Column("settlement_available_at", sa.DateTime(timezone=True), nullable=True))
        if "paid_out_at" not in purchase_cols:
            op.add_column("prompt_purchases", sa.Column("paid_out_at", sa.DateTime(timezone=True), nullable=True))
        if "disputed_at" not in purchase_cols:
            op.add_column("prompt_purchases", sa.Column("disputed_at", sa.DateTime(timezone=True), nullable=True))
        if "payout_id" not in purchase_cols:
            op.add_column(
                "prompt_purchases",
                sa.Column("payout_id", sa.Uuid(as_uuid=True), sa.ForeignKey("marketplace_payouts.id", ondelete="SET NULL"), nullable=True),
            )
        index_names = {index["name"] for index in inspector.get_indexes("prompt_purchases")}
        if "ix_prompt_purchases_settlement_status" not in index_names:
            op.create_index("ix_prompt_purchases_settlement_status", "prompt_purchases", ["settlement_status"])
        if "ix_prompt_purchases_payout_id" not in index_names:
            op.create_index("ix_prompt_purchases_payout_id", "prompt_purchases", ["payout_id"])
        if "uq_prompt_purchases_active_pending" not in index_names:
            op.create_index(
                "uq_prompt_purchases_active_pending",
                "prompt_purchases",
                ["user_id", "prompt_id"],
                unique=True,
                postgresql_where=sa.text("status = 'pending'"),
                sqlite_where=sa.text("status = 'pending'"),
            )

        bind.execute(
            sa.text(
                """
                UPDATE prompt_purchases
                SET
                    settlement_status = CASE
                        WHEN status = 'refunded' THEN 'refunded'
                        WHEN COALESCE(seller_amount_rub, 0) > 0 OR COALESCE(seller_amount_lumens, 0) > 0 THEN 'pending'
                        ELSE 'available'
                    END,
                    settlement_available_at = CASE
                        WHEN status = 'completed' AND (COALESCE(seller_amount_rub, 0) > 0 OR COALESCE(seller_amount_lumens, 0) > 0)
                            THEN completed_at + INTERVAL '7 day'
                        ELSE completed_at
                    END
                """
            )
        )

    if "prompt_reviews" in tables:
        review_cols = _table_columns(inspector, "prompt_reviews")
        if "moderation_status" not in review_cols:
            op.add_column(
                "prompt_reviews",
                sa.Column("moderation_status", sa.String(length=32), nullable=False, server_default="visible"),
            )
        if "moderation_reason" not in review_cols:
            op.add_column("prompt_reviews", sa.Column("moderation_reason", sa.String(length=120), nullable=True))
        if "reported_count" not in review_cols:
            op.add_column("prompt_reviews", sa.Column("reported_count", sa.Integer(), nullable=False, server_default="0"))
        if "edit_count" not in review_cols:
            op.add_column("prompt_reviews", sa.Column("edit_count", sa.Integer(), nullable=False, server_default="0"))
        if "last_reported_at" not in review_cols:
            op.add_column("prompt_reviews", sa.Column("last_reported_at", sa.DateTime(timezone=True), nullable=True))
        if "hidden_at" not in review_cols:
            op.add_column("prompt_reviews", sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True))
        index_names = {index["name"] for index in inspector.get_indexes("prompt_reviews")}
        if "ix_prompt_reviews_moderation_status" not in index_names:
            op.create_index("ix_prompt_reviews_moderation_status", "prompt_reviews", ["moderation_status"])

        bind.execute(
            sa.text(
                """
                UPDATE prompt_reviews
                SET moderation_status = CASE WHEN is_visible THEN 'visible' ELSE 'hidden' END
                """
            )
        )

    if "prompt_review_reports" not in tables:
        op.create_table(
            "prompt_review_reports",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("review_id", sa.Uuid(as_uuid=True), sa.ForeignKey("prompt_reviews.id", ondelete="CASCADE"), nullable=False),
            sa.Column("reporter_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("reason", sa.String(length=64), nullable=False),
            sa.Column("details", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("review_id", "reporter_user_id", name="uq_prompt_review_reports_unique_reporter"),
        )
        op.create_index("ix_prompt_review_reports_review_id", "prompt_review_reports", ["review_id"])
        op.create_index("ix_prompt_review_reports_reporter_user_id", "prompt_review_reports", ["reporter_user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "prompt_review_reports" in tables:
        op.drop_index("ix_prompt_review_reports_reporter_user_id", table_name="prompt_review_reports")
        op.drop_index("ix_prompt_review_reports_review_id", table_name="prompt_review_reports")
        op.drop_table("prompt_review_reports")

    if "prompt_reviews" in tables:
        review_cols = _table_columns(inspector, "prompt_reviews")
        index_names = {index["name"] for index in inspector.get_indexes("prompt_reviews")}
        if "ix_prompt_reviews_moderation_status" in index_names:
            op.drop_index("ix_prompt_reviews_moderation_status", table_name="prompt_reviews")
        for column_name in ["hidden_at", "last_reported_at", "edit_count", "reported_count", "moderation_reason", "moderation_status"]:
            if column_name in review_cols:
                op.drop_column("prompt_reviews", column_name)

    if "prompt_purchases" in tables:
        purchase_cols = _table_columns(inspector, "prompt_purchases")
        index_names = {index["name"] for index in inspector.get_indexes("prompt_purchases")}
        if "uq_prompt_purchases_active_pending" in index_names:
            op.drop_index("uq_prompt_purchases_active_pending", table_name="prompt_purchases")
        if "ix_prompt_purchases_payout_id" in index_names:
            op.drop_index("ix_prompt_purchases_payout_id", table_name="prompt_purchases")
        if "ix_prompt_purchases_settlement_status" in index_names:
            op.drop_index("ix_prompt_purchases_settlement_status", table_name="prompt_purchases")
        for column_name in ["payout_id", "disputed_at", "paid_out_at", "settlement_available_at", "settlement_status"]:
            if column_name in purchase_cols:
                op.drop_column("prompt_purchases", column_name)

    if "marketplace_payouts" in tables:
        op.drop_index("ix_marketplace_payouts_status", table_name="marketplace_payouts")
        op.drop_index("ix_marketplace_payouts_seller_user_id", table_name="marketplace_payouts")
        op.drop_table("marketplace_payouts")

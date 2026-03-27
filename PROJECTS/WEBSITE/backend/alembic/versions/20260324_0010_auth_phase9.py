"""phase9 auth refresh tokens

Revision ID: 20260324_0010
Revises: 20260324_0009
Create Date: 2026-03-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260324_0010"
down_revision: str | None = "20260324_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "auth_refresh_tokens" not in tables:
        op.create_table(
            "auth_refresh_tokens",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("token_hash", sa.String(length=128), nullable=False),
            sa.Column("token_jti", sa.String(length=64), nullable=False),
            sa.Column("family_id", sa.Uuid(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_reason", sa.String(length=120), nullable=True),
            sa.Column("replaced_by_token_id", sa.Uuid(), nullable=True),
            sa.Column("created_ip", sa.String(length=64), nullable=True),
            sa.Column("user_agent", sa.String(length=255), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("token_hash", name="uq_auth_refresh_tokens_token_hash"),
            sa.UniqueConstraint("token_jti", name="uq_auth_refresh_tokens_token_jti"),
        )
        op.create_index("ix_auth_refresh_tokens_user_id", "auth_refresh_tokens", ["user_id"], unique=False)
        op.create_index("ix_auth_refresh_tokens_token_hash", "auth_refresh_tokens", ["token_hash"], unique=True)
        op.create_index("ix_auth_refresh_tokens_token_jti", "auth_refresh_tokens", ["token_jti"], unique=True)
        op.create_index("ix_auth_refresh_tokens_family_id", "auth_refresh_tokens", ["family_id"], unique=False)
        op.create_index("ix_auth_refresh_tokens_expires_at", "auth_refresh_tokens", ["expires_at"], unique=False)
        op.create_index("ix_auth_refresh_tokens_revoked_at", "auth_refresh_tokens", ["revoked_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "auth_refresh_tokens" in tables:
        op.drop_index("ix_auth_refresh_tokens_revoked_at", table_name="auth_refresh_tokens")
        op.drop_index("ix_auth_refresh_tokens_expires_at", table_name="auth_refresh_tokens")
        op.drop_index("ix_auth_refresh_tokens_family_id", table_name="auth_refresh_tokens")
        op.drop_index("ix_auth_refresh_tokens_token_jti", table_name="auth_refresh_tokens")
        op.drop_index("ix_auth_refresh_tokens_token_hash", table_name="auth_refresh_tokens")
        op.drop_index("ix_auth_refresh_tokens_user_id", table_name="auth_refresh_tokens")
        op.drop_table("auth_refresh_tokens")


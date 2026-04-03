"""initial schema

Revision ID: 20250321_0001
Revises:
Create Date: 2025-03-21

"""
from collections.abc import Sequence

from alembic import op

from app.infrastructure.db.base import Base
from app.infrastructure.db import models  # noqa: F401

revision: str = "20250321_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)

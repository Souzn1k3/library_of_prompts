"""unique_display_name

Revision ID: 20260404_0022
Revises: 20260331_0021
Create Date: 2026-04-04
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260404_0022"
down_revision = "20260331_0021"
branch_labels = None
depends_on = None


MAX_DISPLAY_NAME_LEN = 120


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


def _normalize_display_name(value: str | None) -> str:
    normalized = (value or "").strip()
    return normalized or "User"


def _next_unique_display_name(base: str, seen: set[str]) -> str:
    candidate = base
    suffix = 2
    while candidate.lower() in seen:
        suffix_text = f" #{suffix}"
        max_base_len = max(1, MAX_DISPLAY_NAME_LEN - len(suffix_text))
        trimmed_base = base[:max_base_len].rstrip() or "U"
        candidate = f"{trimmed_base}{suffix_text}"
        suffix += 1
    return candidate


def _dedupe_existing_display_names() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT id, display_name
            FROM users
            ORDER BY created_at ASC, id ASC
            """
        )
    ).fetchall()

    seen: set[str] = set()
    for row in rows:
        user_id = row[0]
        original_name = row[1]
        base_name = _normalize_display_name(original_name)
        next_name = _next_unique_display_name(base_name, seen)
        seen.add(next_name.lower())
        if next_name != original_name:
            bind.execute(
                sa.text(
                    """
                    UPDATE users
                    SET display_name = :display_name
                    WHERE id = :id
                    """
                ),
                {"id": user_id, "display_name": next_name},
            )


def upgrade() -> None:
    if not _has_table("users"):
        return

    _dedupe_existing_display_names()

    if not _has_index("users", "uq_users_display_name_ci"):
        op.create_index(
            "uq_users_display_name_ci",
            "users",
            [sa.text("lower(trim(display_name))")],
            unique=True,
        )


def downgrade() -> None:
    if _has_index("users", "uq_users_display_name_ci"):
        op.drop_index("uq_users_display_name_ci", table_name="users")

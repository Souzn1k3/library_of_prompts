"""telegram sync

Revision ID: 20260328_0015
Revises: 20260328_0014
Create Date: 2026-03-28
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260328_0015"
down_revision: str | None = "20260328_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_cols = _column_names(inspector, "users")
    user_indexes = _index_names(inspector, "users")
    prompt_cols = _column_names(inspector, "prompts")
    prompt_indexes = _index_names(inspector, "prompts")

    if "telegram_user_id" not in user_cols:
        op.add_column("users", sa.Column("telegram_user_id", sa.BigInteger(), nullable=True))
    if "ix_users_telegram_user_id" not in user_indexes:
        op.create_index("ix_users_telegram_user_id", "users", ["telegram_user_id"], unique=True)

    if "telegram_username" not in user_cols:
        op.add_column("users", sa.Column("telegram_username", sa.String(length=255), nullable=True))
    if "telegram_first_name" not in user_cols:
        op.add_column("users", sa.Column("telegram_first_name", sa.String(length=255), nullable=True))
    if "telegram_last_name" not in user_cols:
        op.add_column("users", sa.Column("telegram_last_name", sa.String(length=255), nullable=True))
    if "telegram_language" not in user_cols:
        op.add_column("users", sa.Column("telegram_language", sa.String(length=10), nullable=True))
    if "telegram_is_active" not in user_cols:
        op.add_column(
            "users",
            sa.Column("telegram_is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.alter_column("users", "telegram_is_active", server_default=None)
    if "telegram_joined_at" not in user_cols:
        op.add_column("users", sa.Column("telegram_joined_at", sa.DateTime(timezone=True), nullable=True))
    if "telegram_last_active" not in user_cols:
        op.add_column("users", sa.Column("telegram_last_active", sa.DateTime(timezone=True), nullable=True))

    if "legacy_bot_prompt_id" not in prompt_cols:
        op.add_column("prompts", sa.Column("legacy_bot_prompt_id", sa.Integer(), nullable=True))
    if "ix_prompts_legacy_bot_prompt_id" not in prompt_indexes:
        op.create_index(
            "ix_prompts_legacy_bot_prompt_id",
            "prompts",
            ["legacy_bot_prompt_id"],
            unique=True,
        )

    if "legacy_bot_category" not in prompt_cols:
        op.add_column("prompts", sa.Column("legacy_bot_category", sa.String(length=80), nullable=True))
    if "ix_prompts_legacy_bot_category" not in prompt_indexes:
        op.create_index("ix_prompts_legacy_bot_category", "prompts", ["legacy_bot_category"])

    if "legacy_bot_subcategory" not in prompt_cols:
        op.add_column("prompts", sa.Column("legacy_bot_subcategory", sa.String(length=120), nullable=True))
    if "ix_prompts_legacy_bot_subcategory" not in prompt_indexes:
        op.create_index("ix_prompts_legacy_bot_subcategory", "prompts", ["legacy_bot_subcategory"])

    if "content_language" not in prompt_cols:
        op.add_column("prompts", sa.Column("content_language", sa.String(length=10), nullable=True))
    if "ix_prompts_content_language" not in prompt_indexes:
        op.create_index("ix_prompts_content_language", "prompts", ["content_language"])

    if "ix_prompts_legacy_bot_lookup" not in prompt_indexes:
        op.create_index(
            "ix_prompts_legacy_bot_lookup",
            "prompts",
            ["legacy_bot_subcategory", "content_language", "status"],
        )

    existing_category_slugs = {
        row[0]
        for row in bind.execute(sa.text("SELECT slug FROM categories")).fetchall()
    }
    default_categories = [
        ("it", "Информационные технологии и Разработка ПО", 1),
        ("marketing", "Маркетинг, Реклама и PR", 2),
        ("business", "Бизнес, Менеджмент и Предпринимательство", 3),
        ("education", "Образование и Наука", 4),
        ("arts", "Творчество, Искусство и Медиа", 5),
        ("engineering", "Инженерия, Строительство и Производство", 6),
        ("finance", "Финансы, Банкинг и Страхование", 7),
        ("law", "Государственное управление и Право", 8),
        ("agro", "Сельское хозяйство и Экология", 9),
        ("logistics", "Логистика, Транспорт и Туризм", 10),
        ("real-estate", "Недвижимость", 11),
        ("lifestyle", "Персональная эффективность и Lifestyle", 12),
        ("niche", "Специализированные и Нишевые области", 13),
    ]
    rows_to_insert = [
        {
            "slug": slug,
            "name": name,
            "sort_order": sort_order,
            "is_restricted": False,
        }
        for slug, name, sort_order in default_categories
        if slug not in existing_category_slugs
    ]
    for row in rows_to_insert:
        bind.execute(
            sa.text(
                """
                INSERT INTO categories (id, parent_id, slug, name, sort_order, is_restricted)
                VALUES (gen_random_uuid(), NULL, :slug, :name, :sort_order, :is_restricted)
                """
            ),
            {
                "slug": row["slug"],
                "name": row["name"],
                "sort_order": row["sort_order"],
                "is_restricted": row["is_restricted"],
            },
        )


def downgrade() -> None:
    op.drop_index("ix_prompts_legacy_bot_lookup", table_name="prompts")
    op.drop_index("ix_prompts_content_language", table_name="prompts")
    op.drop_column("prompts", "content_language")
    op.drop_index("ix_prompts_legacy_bot_subcategory", table_name="prompts")
    op.drop_column("prompts", "legacy_bot_subcategory")
    op.drop_index("ix_prompts_legacy_bot_category", table_name="prompts")
    op.drop_column("prompts", "legacy_bot_category")
    op.drop_index("ix_prompts_legacy_bot_prompt_id", table_name="prompts")
    op.drop_column("prompts", "legacy_bot_prompt_id")

    op.drop_column("users", "telegram_last_active")
    op.drop_column("users", "telegram_joined_at")
    op.drop_column("users", "telegram_is_active")
    op.drop_column("users", "telegram_language")
    op.drop_column("users", "telegram_last_name")
    op.drop_column("users", "telegram_first_name")
    op.drop_column("users", "telegram_username")
    op.drop_index("ix_users_telegram_user_id", table_name="users")
    op.drop_column("users", "telegram_user_id")

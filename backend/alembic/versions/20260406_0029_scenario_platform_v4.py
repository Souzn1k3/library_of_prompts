"""scenario_platform_v4

Revision ID: 20260406_0029
Revises: 20260406_0028
Create Date: 2026-04-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260406_0029"
down_revision = "20260406_0028"
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


def _has_fk(table_name: str, fk_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(fk.get("name") == fk_name for fk in inspector.get_foreign_keys(table_name))


def upgrade() -> None:
    if _has_table("user_scenario_blueprints"):
        if not _has_column("user_scenario_blueprints", "root_blueprint_id"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("root_blueprint_id", sa.Uuid(), nullable=True),
            )
            op.create_foreign_key(
                "fk_user_scenario_blueprints_root_blueprint_id",
                "user_scenario_blueprints",
                "user_scenario_blueprints",
                ["root_blueprint_id"],
                ["id"],
                ondelete="SET NULL",
            )
            op.create_index(
                "ix_user_scenario_blueprints_root_blueprint_id",
                "user_scenario_blueprints",
                ["root_blueprint_id"],
            )
            op.execute("UPDATE user_scenario_blueprints SET root_blueprint_id = id WHERE root_blueprint_id IS NULL")

        if not _has_column("user_scenario_blueprints", "tags"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            )
        if not _has_column("user_scenario_blueprints", "metadata_json"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("metadata_json", sa.JSON(), nullable=True),
            )
        if not _has_column("user_scenario_blueprints", "monetization_mode"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("monetization_mode", sa.String(length=24), nullable=False, server_default="free"),
            )
            op.create_index(
                "ix_user_scenario_blueprints_monetization_mode",
                "user_scenario_blueprints",
                ["monetization_mode"],
            )
        if not _has_column("user_scenario_blueprints", "run_count"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("run_count", sa.Integer(), nullable=False, server_default="0"),
            )
        if not _has_column("user_scenario_blueprints", "completion_count"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("completion_count", sa.Integer(), nullable=False, server_default="0"),
            )
        if not _has_column("user_scenario_blueprints", "save_count"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("save_count", sa.Integer(), nullable=False, server_default="0"),
            )
        if not _has_column("user_scenario_blueprints", "comment_count"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
            )
        if not _has_column("user_scenario_blueprints", "rating_average"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("rating_average", sa.Float(), nullable=False, server_default="0"),
            )
        if not _has_column("user_scenario_blueprints", "rating_count"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
            )
        if not _has_column("user_scenario_blueprints", "version_number"):
            op.add_column(
                "user_scenario_blueprints",
                sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
            )

    if not _has_table("scenario_blueprint_versions"):
        op.create_table(
            "scenario_blueprint_versions",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("blueprint_id", sa.Uuid(), nullable=False),
            sa.Column("version_number", sa.Integer(), nullable=False),
            sa.Column("snapshot_json", sa.JSON(), nullable=False),
            sa.Column("change_note", sa.String(length=300), nullable=True),
            sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["blueprint_id"], ["user_scenario_blueprints.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "blueprint_id",
                "version_number",
                name="uq_scenario_blueprint_versions_blueprint_version",
            ),
        )
        op.create_index(
            "ix_scenario_blueprint_versions_blueprint_id",
            "scenario_blueprint_versions",
            ["blueprint_id"],
        )
        op.create_index(
            "ix_scenario_blueprint_versions_created_by_user_id",
            "scenario_blueprint_versions",
            ["created_by_user_id"],
        )

    if not _has_table("scenario_blueprint_comments"):
        op.create_table(
            "scenario_blueprint_comments",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("blueprint_id", sa.Uuid(), nullable=False),
            sa.Column("author_user_id", sa.Uuid(), nullable=True),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["blueprint_id"], ["user_scenario_blueprints.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_scenario_blueprint_comments_blueprint_id",
            "scenario_blueprint_comments",
            ["blueprint_id"],
        )
        op.create_index(
            "ix_scenario_blueprint_comments_author_user_id",
            "scenario_blueprint_comments",
            ["author_user_id"],
        )
        op.create_index(
            "ix_scenario_blueprint_comments_created_at",
            "scenario_blueprint_comments",
            ["created_at"],
        )

    if not _has_table("scenario_blueprint_ratings"):
        op.create_table(
            "scenario_blueprint_ratings",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("blueprint_id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("rating", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["blueprint_id"], ["user_scenario_blueprints.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "blueprint_id",
                "user_id",
                name="uq_scenario_blueprint_ratings_blueprint_user",
            ),
        )
        op.create_index(
            "ix_scenario_blueprint_ratings_blueprint_id",
            "scenario_blueprint_ratings",
            ["blueprint_id"],
        )
        op.create_index(
            "ix_scenario_blueprint_ratings_user_id",
            "scenario_blueprint_ratings",
            ["user_id"],
        )

    if not _has_table("scenario_blueprint_saves"):
        op.create_table(
            "scenario_blueprint_saves",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("blueprint_id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["blueprint_id"], ["user_scenario_blueprints.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "blueprint_id",
                "user_id",
                name="uq_scenario_blueprint_saves_blueprint_user",
            ),
        )
        op.create_index(
            "ix_scenario_blueprint_saves_blueprint_id",
            "scenario_blueprint_saves",
            ["blueprint_id"],
        )
        op.create_index(
            "ix_scenario_blueprint_saves_user_id",
            "scenario_blueprint_saves",
            ["user_id"],
        )


def downgrade() -> None:
    if _has_table("scenario_blueprint_saves"):
        if _has_index("scenario_blueprint_saves", "ix_scenario_blueprint_saves_user_id"):
            op.drop_index("ix_scenario_blueprint_saves_user_id", table_name="scenario_blueprint_saves")
        if _has_index("scenario_blueprint_saves", "ix_scenario_blueprint_saves_blueprint_id"):
            op.drop_index("ix_scenario_blueprint_saves_blueprint_id", table_name="scenario_blueprint_saves")
        op.drop_table("scenario_blueprint_saves")

    if _has_table("scenario_blueprint_ratings"):
        if _has_index("scenario_blueprint_ratings", "ix_scenario_blueprint_ratings_user_id"):
            op.drop_index("ix_scenario_blueprint_ratings_user_id", table_name="scenario_blueprint_ratings")
        if _has_index("scenario_blueprint_ratings", "ix_scenario_blueprint_ratings_blueprint_id"):
            op.drop_index("ix_scenario_blueprint_ratings_blueprint_id", table_name="scenario_blueprint_ratings")
        op.drop_table("scenario_blueprint_ratings")

    if _has_table("scenario_blueprint_comments"):
        if _has_index("scenario_blueprint_comments", "ix_scenario_blueprint_comments_created_at"):
            op.drop_index("ix_scenario_blueprint_comments_created_at", table_name="scenario_blueprint_comments")
        if _has_index("scenario_blueprint_comments", "ix_scenario_blueprint_comments_author_user_id"):
            op.drop_index("ix_scenario_blueprint_comments_author_user_id", table_name="scenario_blueprint_comments")
        if _has_index("scenario_blueprint_comments", "ix_scenario_blueprint_comments_blueprint_id"):
            op.drop_index("ix_scenario_blueprint_comments_blueprint_id", table_name="scenario_blueprint_comments")
        op.drop_table("scenario_blueprint_comments")

    if _has_table("scenario_blueprint_versions"):
        if _has_index("scenario_blueprint_versions", "ix_scenario_blueprint_versions_created_by_user_id"):
            op.drop_index(
                "ix_scenario_blueprint_versions_created_by_user_id",
                table_name="scenario_blueprint_versions",
            )
        if _has_index("scenario_blueprint_versions", "ix_scenario_blueprint_versions_blueprint_id"):
            op.drop_index(
                "ix_scenario_blueprint_versions_blueprint_id",
                table_name="scenario_blueprint_versions",
            )
        op.drop_table("scenario_blueprint_versions")

    if _has_table("user_scenario_blueprints"):
        for index_name in (
            "ix_user_scenario_blueprints_root_blueprint_id",
            "ix_user_scenario_blueprints_monetization_mode",
        ):
            if _has_index("user_scenario_blueprints", index_name):
                op.drop_index(index_name, table_name="user_scenario_blueprints")

        if _has_fk("user_scenario_blueprints", "fk_user_scenario_blueprints_root_blueprint_id"):
            op.drop_constraint(
                "fk_user_scenario_blueprints_root_blueprint_id",
                "user_scenario_blueprints",
                type_="foreignkey",
            )

        for column_name in (
            "version_number",
            "rating_count",
            "rating_average",
            "comment_count",
            "save_count",
            "completion_count",
            "run_count",
            "monetization_mode",
            "metadata_json",
            "tags",
            "root_blueprint_id",
        ):
            if _has_column("user_scenario_blueprints", column_name):
                op.drop_column("user_scenario_blueprints", column_name)

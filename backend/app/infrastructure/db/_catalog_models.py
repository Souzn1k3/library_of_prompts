from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._enums import ModerationState, PromptDifficulty, PromptOutputType, PromptStatus, PromptTechnique
from ._user_model import User
from .base import Base

if TYPE_CHECKING:
    from ._marketplace_models import PromptEntitlement, PromptPrice, PromptPurchase, PromptReview
    from ._mission_models import LessonMissionPrompt


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_restricted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        foreign_keys=[parent_id],
    )
    parent: Mapped["Category | None"] = relationship(
        "Category",
        back_populates="children",
        remote_side=[id],
        foreign_keys=[parent_id],
    )
    prompts: Mapped[list["Prompt"]] = relationship(back_populates="category")


class UseCase(Base):
    __tablename__ = "use_cases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    prompt_links: Mapped[list["PromptUseCase"]] = relationship(
        back_populates="use_case",
        cascade="all, delete-orphan",
    )


class ModelCompatibility(Base):
    __tablename__ = "model_compatibilities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    prompt_links: Mapped[list["PromptModelCompatibility"]] = relationship(
        back_populates="model",
        cascade="all, delete-orphan",
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    prompt_links: Mapped[list["PromptTag"]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
    )


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[PromptStatus] = mapped_column(
        Enum(PromptStatus), nullable=False, default=PromptStatus.draft
    )
    technique: Mapped[PromptTechnique] = mapped_column(
        Enum(PromptTechnique), nullable=False, default=PromptTechnique.other
    )
    difficulty: Mapped[PromptDifficulty | None] = mapped_column(
        Enum(PromptDifficulty, native_enum=False, length=32),
        nullable=True,
        index=True,
    )
    output_type: Mapped[PromptOutputType | None] = mapped_column(
        Enum(PromptOutputType, native_enum=False, length=32),
        nullable=True,
        index=True,
    )
    moderation_state: Mapped[ModerationState] = mapped_column(
        Enum(ModerationState), nullable=False, default=ModerationState.none_
    )
    is_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    moderation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    moderated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    legacy_bot_prompt_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True, index=True)
    legacy_bot_category: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    legacy_bot_subcategory: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    content_language: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)

    category: Mapped["Category"] = relationship(back_populates="prompts")
    author: Mapped["User | None"] = relationship(back_populates="prompts", foreign_keys=[author_id])
    moderated_by: Mapped["User | None"] = relationship(foreign_keys=[moderated_by_id])
    saved_by_links: Mapped[list["SavedPrompt"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    stats: Mapped["PromptStats | None"] = relationship(
        back_populates="prompt",
        uselist=False,
        cascade="all, delete-orphan",
    )
    quality_metrics: Mapped["PromptQualityMetric | None"] = relationship(
        back_populates="prompt",
        uselist=False,
        cascade="all, delete-orphan",
    )
    use_case_links: Mapped[list["PromptUseCase"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    model_links: Mapped[list["PromptModelCompatibility"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    tag_links: Mapped[list["PromptTag"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    mission_links: Mapped[list["LessonMissionPrompt"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    pricing: Mapped["PromptPrice | None"] = relationship(
        back_populates="prompt",
        uselist=False,
        cascade="all, delete-orphan",
    )
    marketplace_entitlements: Mapped[list["PromptEntitlement"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    marketplace_purchases: Mapped[list["PromptPurchase"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    marketplace_reviews: Mapped[list["PromptReview"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )


class PromptStats(Base):
    __tablename__ = "prompt_stats"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    save_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    copy_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    prompt: Mapped["Prompt"] = relationship(back_populates="stats")


class PromptQualityMetric(Base):
    __tablename__ = "prompt_quality_metrics"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    unique_savers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    copy_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mission_success_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    prompt: Mapped["Prompt"] = relationship(back_populates="quality_metrics")


class PromptUseCase(Base):
    __tablename__ = "prompt_use_cases"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    use_case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("use_cases.id", ondelete="CASCADE"),
        primary_key=True,
    )

    prompt: Mapped["Prompt"] = relationship(back_populates="use_case_links")
    use_case: Mapped["UseCase"] = relationship(back_populates="prompt_links")


class PromptModelCompatibility(Base):
    __tablename__ = "prompt_model_compatibilities"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("model_compatibilities.id", ondelete="CASCADE"),
        primary_key=True,
    )

    prompt: Mapped["Prompt"] = relationship(back_populates="model_links")
    model: Mapped["ModelCompatibility"] = relationship(back_populates="prompt_links")


class PromptTag(Base):
    __tablename__ = "prompt_tags"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    prompt: Mapped["Prompt"] = relationship(back_populates="tag_links")
    tag: Mapped["Tag"] = relationship(back_populates="prompt_links")


class SavedPrompt(Base):
    __tablename__ = "saved_prompts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="saved_prompt_links")
    prompt: Mapped["Prompt"] = relationship(back_populates="saved_by_links")


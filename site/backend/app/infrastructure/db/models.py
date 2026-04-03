import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class UserRole(str, enum.Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class PlanTier(str, enum.Enum):
    free = "free"
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class PromptStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class PromptTechnique(str, enum.Enum):
    zero_shot = "zero_shot"
    few_shot = "few_shot"
    chain_of_thought = "chain_of_thought"
    other = "other"


class ModerationState(str, enum.Enum):
    none_ = "none"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.user)
    plan_tier: Mapped[PlanTier] = mapped_column(
        Enum(PlanTier, native_enum=False, length=32),
        nullable=False,
        default=PlanTier.free,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    prompts: Mapped[list["Prompt"]] = relationship(back_populates="author")
    saved_prompt_links: Mapped[list["SavedPrompt"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    category: Mapped["Category"] = relationship(back_populates="prompts")
    author: Mapped["User | None"] = relationship(back_populates="prompts")
    saved_by_links: Mapped[list["SavedPrompt"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )


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


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    min_tier: Mapped[PlanTier] = mapped_column(
        Enum(PlanTier, native_enum=False, length=32),
        nullable=False,
        default=PlanTier.free,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

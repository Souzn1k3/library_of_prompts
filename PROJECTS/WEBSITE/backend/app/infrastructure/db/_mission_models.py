from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .models import (
    MissionActionType,
    MissionDifficulty,
    MissionProgressStatus,
    MissionRewardType,
    MissionType,
    OnboardingGoal,
    OnboardingRole,
    PlanTier,
    Prompt,
    User,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    missions: Mapped[list["LessonMission"]] = relationship(back_populates="lesson")


class LessonMission(Base):
    __tablename__ = "lesson_missions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    objective: Mapped[str] = mapped_column(String(320), nullable=False)
    completion_condition: Mapped[str] = mapped_column(String(320), nullable=False)
    action_type: Mapped[MissionActionType] = mapped_column(
        Enum(MissionActionType, native_enum=False, length=40),
        nullable=False,
    )
    difficulty: Mapped[MissionDifficulty] = mapped_column(
        Enum(MissionDifficulty, native_enum=False, length=24),
        nullable=False,
        default=MissionDifficulty.standard,
        index=True,
    )
    mission_type: Mapped[MissionType] = mapped_column(
        Enum(MissionType, native_enum=False, length=24),
        nullable=False,
        default=MissionType.action,
        index=True,
    )
    required_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_repeatable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    repeat_interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    persona_role: Mapped[OnboardingRole | None] = mapped_column(
        Enum(OnboardingRole, native_enum=False, length=32),
        nullable=True,
        index=True,
    )
    persona_goal: Mapped[OnboardingGoal | None] = mapped_column(
        Enum(OnboardingGoal, native_enum=False, length=32),
        nullable=True,
        index=True,
    )
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reward_badge: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reward_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reward_premium_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    lesson: Mapped["Lesson | None"] = relationship(back_populates="missions")
    prompt_links: Mapped[list["LessonMissionPrompt"]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
    )
    steps: Mapped[list["MissionStep"]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
        order_by="MissionStep.sort_order",
    )
    progress_rows: Mapped[list["UserMissionProgress"]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
    )
    completion_events: Mapped[list["MissionCompletionEvent"]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
    )
    reward_grants: Mapped[list["UserMissionRewardGrant"]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
    )


class LessonMissionPrompt(Base):
    __tablename__ = "lesson_mission_prompts"

    mission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lesson_missions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    mission: Mapped["LessonMission"] = relationship(back_populates="prompt_links")
    prompt: Mapped["Prompt"] = relationship(back_populates="mission_links")


class MissionStep(Base):
    __tablename__ = "mission_steps"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lesson_missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    action_type: Mapped[MissionActionType] = mapped_column(
        Enum(MissionActionType, native_enum=False, length=40),
        nullable=False,
    )
    required_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    target_prompt_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
    )
    reward_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    mission: Mapped["LessonMission"] = relationship(back_populates="steps")
    target_prompt: Mapped["Prompt | None"] = relationship()
    target_lesson: Mapped["Lesson | None"] = relationship()
    progress_rows: Mapped[list["UserMissionStepProgress"]] = relationship(
        back_populates="step",
        cascade="all, delete-orphan",
    )


class UserMissionStepProgress(Base):
    __tablename__ = "user_mission_step_progress"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mission_step_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("mission_steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[MissionProgressStatus] = mapped_column(
        Enum(MissionProgressStatus, native_enum=False, length=24),
        nullable=False,
        default=MissionProgressStatus.not_started,
        index=True,
    )
    progress_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    required_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "mission_step_id", name="uq_user_mission_step_progress"),
    )

    user: Mapped["User"] = relationship()
    step: Mapped["MissionStep"] = relationship(back_populates="progress_rows")


class UserMissionProgress(Base):
    __tablename__ = "user_mission_progress"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lesson_missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[MissionProgressStatus] = mapped_column(
        Enum(MissionProgressStatus, native_enum=False, length=24),
        nullable=False,
        default=MissionProgressStatus.not_started,
        index=True,
    )
    completion_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    required_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reward_granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "mission_id", name="uq_user_mission_progress_user_mission"),
    )

    user: Mapped["User"] = relationship(back_populates="mission_progress")
    mission: Mapped["LessonMission"] = relationship(back_populates="progress_rows")
    completion_events: Mapped[list["MissionCompletionEvent"]] = relationship(
        back_populates="progress",
        cascade="all, delete-orphan",
    )


class MissionCompletionEvent(Base):
    __tablename__ = "mission_completion_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    progress_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_mission_progress.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lesson_missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source_event_key: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)
    prompt_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="SET NULL"),
        nullable=True,
    )
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
    )
    mission_step_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("mission_steps.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    progress: Mapped["UserMissionProgress"] = relationship(back_populates="completion_events")
    user: Mapped["User"] = relationship(back_populates="mission_completion_events")
    mission: Mapped["LessonMission"] = relationship(back_populates="completion_events")
    mission_step: Mapped["MissionStep | None"] = relationship()
    prompt: Mapped["Prompt | None"] = relationship()
    lesson: Mapped["Lesson | None"] = relationship()


class UserMissionRewardGrant(Base):
    __tablename__ = "user_mission_reward_grants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lesson_missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reward_type: Mapped[MissionRewardType] = mapped_column(
        Enum(MissionRewardType, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    reward_cycle: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    badge_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    premium_access_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "mission_id",
            "reward_type",
            "reward_cycle",
            name="uq_user_mission_reward_grants_key",
        ),
    )

    user: Mapped["User"] = relationship(back_populates="mission_reward_grants")
    mission: Mapped["LessonMission"] = relationship(back_populates="reward_grants")

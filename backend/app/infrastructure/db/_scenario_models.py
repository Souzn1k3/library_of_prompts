from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BIGINT, JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from ._catalog_models import Prompt
    from ._user_model import User


class UserScenarioWorkspace(Base):
    __tablename__ = "user_scenario_workspace"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_saved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    unfinished_task: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    copy_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    share_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_copied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_shared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="scenario_workspace_entries")
    prompt: Mapped["Prompt"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "prompt_id", name="uq_user_scenario_workspace_user_prompt"),
    )


class GuestScenarioRunUsage(Base):
    __tablename__ = "guest_scenario_run_usage"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guest_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    last_user_agent_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_fingerprint_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    prompt: Mapped["Prompt"] = relationship()

    __table_args__ = (
        UniqueConstraint("guest_id", "prompt_id", name="uq_guest_scenario_run_usage_guest_prompt"),
    )


class ScenarioGameTokenEvent(Base):
    __tablename__ = "scenario_game_token_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="web_demo", index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    guest_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    challenge_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    choice_index: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", index=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fingerprint_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claim_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User | None"] = relationship(back_populates="scenario_game_events")


class ScenarioGameTokenClaim(Base):
    __tablename__ = "scenario_game_token_claims"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    guest_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="web_demo", index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="completed", index=True)
    claimed_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_tokens_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balance_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="scenario_game_claims")


class TelegramRewardClaim(Base):
    __tablename__ = "telegram_reward_claims"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    telegram_user_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reward_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    challenge_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signature: Mapped[str] = mapped_column(String(128), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    verification_error: Mapped[str | None] = mapped_column(String(300), nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User | None"] = relationship(back_populates="telegram_reward_claims")


class UserScenarioRunBoost(Base):
    __tablename__ = "user_scenario_run_boosts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bonus_runs_remaining: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (UniqueConstraint("user_id", "prompt_id", name="uq_user_scenario_run_boosts_user_prompt"),)


class UserScenarioBlueprint(Base):
    __tablename__ = "user_scenario_blueprints"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_prompt_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    forked_from_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_scenario_blueprints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    title: Mapped[str] = mapped_column(String(260), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(700), nullable=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="utility", index=True)
    visibility: Mapped[str] = mapped_column(String(24), nullable=False, default="private", index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    token_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    context_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    logic_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fork_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("owner_user_id", "slug", name="uq_user_scenario_blueprints_owner_slug"),
    )


class UserScenarioBlueprintShare(Base):
    __tablename__ = "user_scenario_blueprint_shares"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blueprint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_scenario_blueprints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    member_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    can_edit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "blueprint_id",
            "member_user_id",
            name="uq_user_scenario_blueprint_shares_blueprint_member",
        ),
    )


class UserScenarioWorkflow(Base):
    __tablename__ = "user_scenario_workflows"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str | None] = mapped_column(String(600), nullable=True)
    visibility: Mapped[str] = mapped_column(String(24), nullable=False, default="private", index=True)
    step_blueprint_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class UserScenarioWorkflowRun(Base):
    __tablename__ = "user_scenario_workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_scenario_workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    guest_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="in_progress", index=True)
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    context_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ScenarioOutputShowcase(Base):
    __tablename__ = "scenario_output_showcases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    share_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    author_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prompt_slug: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    blueprint_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_scenario_blueprints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    excerpt: Mapped[str] = mapped_column(String(700), nullable=False)
    output_preview: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(String(24), nullable=False, default="public", index=True)
    upvotes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


class ScenarioCreatorRewardEvent(Base):
    __tablename__ = "scenario_creator_reward_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_key: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    blueprint_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_scenario_blueprints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reward_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

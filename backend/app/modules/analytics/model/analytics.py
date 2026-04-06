import enum
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, model_validator

_META_KEY_RE = re.compile(r"^[a-z0-9_]{1,64}$")
_MAX_METADATA_JSON_CHARS = 4096


class AnalyticsEventName(str, enum.Enum):
    signup_completed = "signup_completed"
    first_visit = "first_visit"
    page_viewed = "page_viewed"
    onboarding_started = "onboarding_started"
    onboarding_completed = "onboarding_completed"
    onboarding_first_action = "onboarding_first_action"
    prompt_viewed = "prompt_viewed"
    prompt_copied = "prompt_copied"
    prompt_saved = "prompt_saved"
    mission_started = "mission_started"
    mission_progressed = "mission_progressed"
    mission_completed = "mission_completed"
    mission_next_step_clicked = "mission_next_step_clicked"
    submission_form_submitted = "submission_form_submitted"
    submission_created = "submission_created"
    submission_moderated = "submission_moderated"
    submission_engaged = "submission_engaged"
    locked_content_viewed = "locked_content_viewed"
    upgrade_clicked = "upgrade_clicked"
    checkout_started = "checkout_started"
    checkout_completed = "checkout_completed"
    payment_failed = "payment_failed"
    subscription_activated = "subscription_activated"
    subscription_started = "subscription_started"
    subscription_renewed = "subscription_renewed"
    subscription_canceled = "subscription_canceled"
    refund_processed = "refund_processed"
    paywall_viewed = "paywall_viewed"
    paywall_interaction = "paywall_interaction"
    pricing_plan_selected = "pricing_plan_selected"
    catalog_search_used = "catalog_search_used"
    catalog_filter_used = "catalog_filter_used"
    scenario_run = "scenario_run"
    scenario_saved = "scenario_saved"
    scenario_resumed = "scenario_resumed"
    scenario_upgrade_clicked = "scenario_upgrade_clicked"
    scenario_completed = "scenario_completed"
    scenario_shared = "scenario_shared"
    scenario_pack_started = "scenario_pack_started"
    scenario_chain_next_clicked = "scenario_chain_next_clicked"
    user_acquired = "user_acquired"
    attribution_assigned = "attribution_assigned"
    growth_experiment_assigned = "growth_experiment_assigned"
    feature_flag_exposed = "feature_flag_exposed"
    churn_risk_detected = "churn_risk_detected"
    reactivation_trigger = "reactivation_trigger"
    economy_experiment_assigned = "economy_experiment_assigned"
    store_offer_viewed = "store_offer_viewed"
    store_purchase_completed = "store_purchase_completed"
    second_purchase_challenge_started = "second_purchase_challenge_started"
    second_purchase_challenge_completed = "second_purchase_challenge_completed"
    locked_cashback_unlocked = "locked_cashback_unlocked"
    streak_recovery_offered = "streak_recovery_offered"
    streak_recovery_completed = "streak_recovery_completed"
    goal_completed = "goal_completed"


class AnalyticsContext(BaseModel):
    page: str = Field(min_length=1, max_length=260)
    feature: str = Field(min_length=1, max_length=120)


class AnalyticsAttribution(BaseModel):
    utm_source: str | None = Field(default=None, max_length=120)
    utm_medium: str | None = Field(default=None, max_length=120)
    utm_campaign: str | None = Field(default=None, max_length=160)
    utm_term: str | None = Field(default=None, max_length=160)
    utm_content: str | None = Field(default=None, max_length=160)
    referrer: str | None = Field(default=None, max_length=500)


def _validate_json(value: Any, *, depth: int = 0) -> None:
    if depth > 6:
        raise ValueError("metadata nesting is too deep")
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    if isinstance(value, list):
        for item in value:
            _validate_json(item, depth=depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not _META_KEY_RE.match(key):
                raise ValueError("metadata keys must be snake_case and <= 64 chars")
            _validate_json(item, depth=depth + 1)
        return
    raise ValueError("metadata must be JSON-serializable")


class AnalyticsEventIn(BaseModel):
    event_id: str = Field(min_length=8, max_length=80)
    event_name: AnalyticsEventName
    session_id: str = Field(min_length=6, max_length=120)
    timestamp: datetime
    context: AnalyticsContext
    metadata: dict[str, Any] = Field(default_factory=dict)
    attribution: AnalyticsAttribution | None = None
    source: str = Field(default="web", min_length=1, max_length=40)

    @model_validator(mode="after")
    def validate_payload(self) -> "AnalyticsEventIn":
        _validate_json(self.metadata)
        serialized_metadata = json.dumps(self.metadata, ensure_ascii=False, separators=(",", ":"))
        if len(serialized_metadata) > _MAX_METADATA_JSON_CHARS:
            raise ValueError("metadata payload is too large")
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
        else:
            self.timestamp = self.timestamp.astimezone(timezone.utc)
        return self


class AnalyticsIngestPayload(BaseModel):
    event: AnalyticsEventIn | None = None
    events: list[AnalyticsEventIn] | None = None

    @model_validator(mode="after")
    def validate_event_collection(self) -> "AnalyticsIngestPayload":
        has_single = self.event is not None
        has_many = bool(self.events)
        if has_single == has_many:
            raise ValueError("Provide exactly one of `event` or `events`")
        if self.events is not None and len(self.events) > 100:
            raise ValueError("events batch size cannot exceed 100")
        return self

    def normalized_events(self) -> list[AnalyticsEventIn]:
        if self.event is not None:
            return [self.event]
        return list(self.events or [])


class AnalyticsIngestResponse(BaseModel):
    accepted: int
    ingested: int
    duplicates: int


class AttributionCaptureWrite(BaseModel):
    session_id: str = Field(min_length=6, max_length=120)
    attribution: AnalyticsAttribution
    source: str = Field(default="web", min_length=1, max_length=40)


class AttributionTouchRead(BaseModel):
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    referrer: str | None = None
    seen_at: datetime


class AttributionCaptureRead(BaseModel):
    session_id: str
    user_id: uuid.UUID | None
    first_touch: AttributionTouchRead
    last_touch: AttributionTouchRead


class AnalyticsEventRead(BaseModel):
    id: uuid.UUID
    event_id: str
    event_name: str
    user_id: uuid.UUID | None
    session_id: str
    source: str
    context_page: str
    context_feature: str
    utm_source: str | None
    utm_medium: str | None
    utm_campaign: str | None
    utm_term: str | None
    utm_content: str | None
    referrer: str | None
    metadata_json: dict[str, Any]
    occurred_at: datetime
    ingested_at: datetime

    model_config = {"from_attributes": True}

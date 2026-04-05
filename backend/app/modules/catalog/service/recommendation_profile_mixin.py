from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.core.tiers import can_view_restricted_category
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.catalog.service.recommendation_constants import (
    ANALYTICS_WEIGHTS,
    PROFILE_KEYWORDS,
    UserSignalProfile,
)


class RecommendationProfileMixin:
    async def _build_user_profile(self, viewer) -> UserSignalProfile:
        profile = UserSignalProfile()
        if viewer is None:
            return profile
        restrict_to_unrestricted_categories = not can_view_restricted_category(viewer)

        saved_rows = await self._saved_prompts.list_saved_published_prompts(viewer.id)
        if saved_rows:
            profile.has_behavioral_history = True
        for row in saved_rows:
            profile.saved_prompt_ids.add(row.id)
            self._append_recent_prompt(profile, row.id)
            self._add_prompt_signal(profile, row, weight=3.2)

        recent_events = await self._analytics.list_recent_for_user(
            user_id=viewer.id,
            event_names=[
                AnalyticsEventName.prompt_viewed,
                AnalyticsEventName.prompt_copied,
                AnalyticsEventName.prompt_saved,
            ],
            limit=120,
            from_ts=datetime.now(timezone.utc) - timedelta(days=120),
        )
        prompt_event_ids: list[uuid.UUID] = []
        prompt_event_weights: dict[uuid.UUID, float] = defaultdict(float)
        for event in recent_events:
            prompt_id = self._prompt_id_from_metadata(event.metadata_json)
            if prompt_id is None:
                continue
            try:
                prompt_uuid = uuid.UUID(prompt_id)
            except ValueError:
                continue
            prompt_event_ids.append(prompt_uuid)
            event_name = AnalyticsEventName(event.event_name)
            prompt_event_weights[prompt_uuid] += ANALYTICS_WEIGHTS.get(event_name, 0.0)

        if prompt_event_weights:
            profile.has_behavioral_history = True
        event_rows = await self._prompts.list_published_by_ids(
            prompt_event_ids,
            restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
        )
        for row in event_rows:
            self._append_recent_prompt(profile, row.id)
            self._add_prompt_signal(profile, row, weight=prompt_event_weights.get(row.id, 0.0))

        mission_events = await self._missions.list_recent_completion_events(user_id=viewer.id, limit=24)
        lesson_ids: list[uuid.UUID] = []
        for event in mission_events:
            if event.prompt_id is not None:
                self._append_recent_prompt(profile, event.prompt_id)
            if event.lesson_id is not None:
                lesson_ids.append(event.lesson_id)
        for lesson_id in list(dict.fromkeys(lesson_ids))[:4]:
            lesson = await self._lessons.get_by_id(lesson_id)
            if lesson is None:
                continue
            self._add_keyword_signal(profile, lesson.title, weight=1.6)

        onboarding_profile = await self._onboarding.get_profile(viewer.id)
        if onboarding_profile is not None:
            hint_tokens: list[str] = []
            if onboarding_profile.role is not None:
                hint_tokens.extend(PROFILE_KEYWORDS.get(onboarding_profile.role.value, []))
            if onboarding_profile.goal is not None:
                hint_tokens.extend(PROFILE_KEYWORDS.get(onboarding_profile.goal.value, []))
            if onboarding_profile.ai_context:
                hint_tokens.extend(PROFILE_KEYWORDS.get(onboarding_profile.ai_context, []))
            for token in dict.fromkeys(hint_tokens):
                profile.keyword_weights[token] += 1.2
            if hint_tokens:
                profile.has_profile_hints = True

            if onboarding_profile.first_win_prompt_id is not None:
                first_win_rows = await self._prompts.list_published_by_ids(
                    [onboarding_profile.first_win_prompt_id],
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                )
                for row in first_win_rows:
                    self._append_recent_prompt(profile, row.id)
                    self._add_prompt_signal(profile, row, weight=2.2)

        return profile

    def _add_prompt_signal(self, profile: UserSignalProfile, row, *, weight: float) -> None:
        if weight <= 0:
            return
        profile.category_weights[row.category_id] += weight
        if row.difficulty is not None:
            profile.difficulty_weights[row.difficulty.value] += weight
        profile.technique_weights[row.technique.value] += weight
        if row.output_type is not None:
            profile.output_type_weights[row.output_type.value] += weight
        for link in row.tag_links:
            if link.tag is not None:
                profile.tag_weights[link.tag.slug] += weight
        for link in row.use_case_links:
            if link.use_case is not None:
                profile.use_case_weights[link.use_case.slug] += weight
        for link in row.model_links:
            if link.model is not None:
                profile.model_weights[link.model.slug] += weight
        self._add_keyword_signal(profile, row.title, weight=weight)
        if row.summary:
            self._add_keyword_signal(profile, row.summary, weight=weight * 0.65)

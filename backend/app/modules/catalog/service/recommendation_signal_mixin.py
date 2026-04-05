from __future__ import annotations

import uuid
from collections.abc import Sequence

from app.modules.catalog.service.recommendation_constants import STOPWORDS, WORD_RE, UserSignalProfile


class RecommendationSignalMixin:
    def _keyword_query(self, weights: dict[str, float], limit: int = 6) -> str | None:
        terms = [key for key, _ in sorted(weights.items(), key=lambda item: item[1], reverse=True)[:limit]]
        query = " ".join(term for term in terms if term and term not in STOPWORDS).strip()
        return query or None

    def _extract_keywords(self, text: str) -> set[str]:
        return {
            token.lower()
            for token in WORD_RE.findall(text.lower())
            if token.lower() not in STOPWORDS and not token.isdigit()
        }

    def _add_keyword_signal(self, profile: UserSignalProfile, text: str, *, weight: float) -> None:
        for keyword in self._extract_keywords(text):
            profile.keyword_weights[keyword] += weight

    def _append_recent_prompt(self, profile: UserSignalProfile, prompt_id: uuid.UUID) -> None:
        if prompt_id not in profile.recent_prompt_ids:
            profile.recent_prompt_ids.append(prompt_id)

    def _prompt_id_from_metadata(self, metadata: dict | None) -> str | None:
        if not metadata:
            return None
        value = metadata.get("prompt_id")
        return str(value) if value else None

    def _top_weighted_keys(self, weights: dict, limit: int) -> list:
        return [key for key, _ in sorted(weights.items(), key=lambda item: item[1], reverse=True)[:limit]]

    def _preferred_key(self, weights: dict[str, float]) -> str | None:
        if not weights:
            return None
        return max(weights.items(), key=lambda item: item[1])[0]

    def _single_value_score(self, value, weights: dict) -> float:
        if value is None or not weights:
            return 0.0
        top_weight = max(float(weight) for weight in weights.values())
        if top_weight <= 0:
            return 0.0
        return min(float(weights.get(value, 0.0)) / top_weight, 1.0)

    def _multi_value_score(self, values: Sequence[str], weights: dict[str, float]) -> float:
        if not values or not weights:
            return 0.0
        top_total = sum(weight for _, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True)[:4])
        if top_total <= 0:
            return 0.0
        raw = sum(float(weights.get(value, 0.0)) for value in values)
        return min(raw / float(top_total), 1.0)

    def _keyword_match_score(self, values: set[str], weights: dict[str, float]) -> float:
        if not values or not weights:
            return 0.0
        top_total = sum(weight for _, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True)[:8])
        if top_total <= 0:
            return 0.0
        raw = sum(float(weights.get(value, 0.0)) for value in values)
        return min(raw / float(top_total), 1.0)

    def _set_overlap(self, left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        union = left | right
        if not union:
            return 0.0
        return len(left & right) / len(union)

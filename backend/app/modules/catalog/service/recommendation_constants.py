from __future__ import annotations

import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field

from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.catalog.model.recommendation import RecommendationContext

WORD_RE = re.compile(r"[\w-]{3,}", re.UNICODE)
STOPWORDS = {
    "and",
    "are",
    "assistant",
    "chat",
    "for",
    "from",
    "into",
    "prompt",
    "prompts",
    "that",
    "the",
    "this",
    "with",
    "your",
}
PROFILE_KEYWORDS: dict[str, list[str]] = {
    "student": ["study", "exam", "summary", "explain"],
    "developer": ["code", "debug", "api", "refactor"],
    "other": ["workflow", "planning", "research", "writing"],
    "learning": ["learn", "tutorial", "practice", "explain"],
    "solving_tasks": ["analysis", "solve", "task", "step"],
    "productivity": ["organize", "workflow", "checklist", "time"],
    "chatgpt": ["assistant", "chat"],
    "code_assistant": ["code", "debug", "test"],
    "school": ["study", "notes", "exam"],
    "work": ["email", "meeting", "planning"],
}
ANALYTICS_WEIGHTS = {
    AnalyticsEventName.prompt_saved: 3.0,
    AnalyticsEventName.prompt_copied: 2.25,
    AnalyticsEventName.prompt_viewed: 0.9,
}
CONTEXTUAL_STRATEGY_CONTEXTS = {
    RecommendationContext.prompt_detail,
    RecommendationContext.after_save,
    RecommendationContext.after_lesson_complete,
}
BEGINNER_CANDIDATE_CONTEXTS = {
    RecommendationContext.dashboard,
    RecommendationContext.after_save,
    RecommendationContext.after_lesson_complete,
}
CONTEXT_SCORE_WEIGHTS: dict[RecommendationContext, tuple[float, float, float, float, float]] = {
    RecommendationContext.prompt_detail: (0.58, 0.12, 0.08, 0.22, 0.0),
    RecommendationContext.after_save: (0.42, 0.28, 0.1, 0.2, 0.0),
    RecommendationContext.after_lesson_complete: (0.44, 0.22, 0.1, 0.24, 0.0),
    RecommendationContext.dashboard: (0.0, 0.44, 0.14, 0.26, 0.16),
    RecommendationContext.home: (0.0, 0.34, 0.16, 0.34, 0.16),
}


@dataclass
class UserSignalProfile:
    saved_prompt_ids: set[uuid.UUID] = field(default_factory=set)
    recent_prompt_ids: list[uuid.UUID] = field(default_factory=list)
    category_weights: dict[uuid.UUID, float] = field(default_factory=lambda: defaultdict(float))
    tag_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    use_case_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    model_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    difficulty_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    technique_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    output_type_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    keyword_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    has_behavioral_history: bool = False
    has_profile_hints: bool = False


@dataclass
class ScoreBreakdown:
    total: float
    global_score: float
    behavior_score: float
    text_score: float
    contextual_score: float
    reason_key: str

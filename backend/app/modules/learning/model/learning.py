from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.modules.economy.model.store import EconomyActionRead

LearningStepKind = Literal[
    "theory",
    "guided_practice",
    "quiz",
    "applied_exercise",
    "reflection",
    "final_checkpoint",
]
LearningProgressStatus = Literal["not_started", "active", "completed"]
LearningLessonStatus = Literal["not_started", "in_progress", "completed"]


class LearningStartTargetRead(BaseModel):
    target: str
    has_active_course: bool
    active_course_slug: str | None = None
    resume_href: str | None = None


class LearningActionLinkRead(BaseModel):
    label: str
    href: str
    body: str | None = None


class LearningCourseCardRead(BaseModel):
    slug: str
    title: str
    subtitle: str
    description: str
    difficulty: str
    result_headline: str | None = None
    deliverable_preview: str | None = None
    estimated_minutes: int
    module_count: int
    lesson_count: int
    progress_percent: int = 0
    status: LearningProgressStatus = "not_started"
    last_activity_at: datetime | None = None
    next_lesson_slug: str | None = None
    resume_href: str | None = None
    badge_earned: bool = False
    course_reward_lmn: int = 0


class LearningCatalogRead(BaseModel):
    courses: list[LearningCourseCardRead]
    recommended_course_slug: str | None = None


class LearningMyCourseItemRead(BaseModel):
    slug: str
    title: str
    subtitle: str
    progress_percent: int
    status: LearningProgressStatus
    last_activity_at: datetime | None = None
    next_lesson_title: str | None = None
    next_lesson_slug: str | None = None
    continue_href: str | None = None
    completed_at: datetime | None = None
    badge_code: str | None = None
    certificate_ready: bool = False


class LearningWeakAreaRead(BaseModel):
    tag: str
    count: int
    recommendation: str
    lesson_slug: str | None = None


class LearningMyModulesRead(BaseModel):
    active_courses: list[LearningMyCourseItemRead]
    completed_courses: list[LearningMyCourseItemRead]
    weak_areas: list[LearningWeakAreaRead] = Field(default_factory=list)


class LearningLessonOutlineRead(BaseModel):
    slug: str
    title: str
    summary: str
    estimated_minutes: int
    position: int
    status: LearningLessonStatus
    unlocked: bool
    is_final_assessment: bool
    progress_percent: int
    continue_href: str


class LearningModuleRead(BaseModel):
    slug: str
    title: str
    summary: str
    position: int
    lesson_count: int
    progress_percent: int
    lessons: list[LearningLessonOutlineRead]


class LearningCourseRewardsRead(BaseModel):
    lesson_reward_lmn: int
    course_reward_lmn: int
    badge_code: str
    certificate_template: str
    badge_earned: bool = False
    course_completed: bool = False


class LearningCourseRead(BaseModel):
    slug: str
    title: str
    subtitle: str
    description: str
    difficulty: str
    result_headline: str | None = None
    estimated_minutes: int
    module_count: int
    lesson_count: int
    progress_percent: int
    status: LearningProgressStatus
    last_activity_at: datetime | None = None
    resume_href: str | None = None
    start_or_continue_label: str
    what_you_will_learn: list[str]
    prerequisites: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    career_outcomes: list[str] = Field(default_factory=list)
    product_action: LearningActionLinkRead | None = None
    modules: list[LearningModuleRead]
    rewards: LearningCourseRewardsRead
    weak_areas: list[LearningWeakAreaRead] = Field(default_factory=list)


class LearningStepChoiceRead(BaseModel):
    id: str
    text: str
    explanation: str | None = None


class LearningQuizQuestionRead(BaseModel):
    id: str
    question: str
    choices: list[LearningStepChoiceRead] = Field(default_factory=list)


class LearningStepFeedbackRead(BaseModel):
    verdict: str
    score: int
    pass_score: int
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    revisit: list[str] = Field(default_factory=list)
    hint: str | None = None


class LearningLessonStepRead(BaseModel):
    slug: str
    kind: LearningStepKind
    title: str
    estimated_minutes: int
    content: list[str] = Field(default_factory=list)
    task: str | None = None
    placeholder: str | None = None
    question: str | None = None
    choices: list[LearningStepChoiceRead] = Field(default_factory=list)
    quiz_questions: list[LearningQuizQuestionRead] = Field(default_factory=list)
    pass_score: int = 0
    min_words: int | None = None
    required_markers: list[str] = Field(default_factory=list)
    bonus_markers: list[str] = Field(default_factory=list)
    forbidden_phrases: list[str] = Field(default_factory=list)
    submission_type: Literal["none", "text", "choice"] = "none"
    unlocked: bool = True
    completed: bool = False
    attempts: int = 0
    last_score: int | None = None
    last_answer_text: str | None = None
    last_choice_id: str | None = None
    last_choice_map: dict[str, str] = Field(default_factory=dict)
    feedback: LearningStepFeedbackRead | None = None


class LearningLessonRead(BaseModel):
    course_slug: str
    module_slug: str
    lesson_slug: str
    title: str
    summary: str
    objective: str | None = None
    deliverable: str | None = None
    scenario_title: str | None = None
    scenario_body: str | None = None
    debrief: list[str] = Field(default_factory=list)
    review_rubric: list[str] = Field(default_factory=list)
    common_mistakes: list[str] = Field(default_factory=list)
    estimated_minutes: int
    position_in_course: int
    total_lessons: int
    progress_percent: int
    course_progress_percent: int
    status: LearningLessonStatus
    unlocked: bool
    is_final_assessment: bool
    return_to_course_href: str
    previous_lesson_href: str | None = None
    next_lesson_href: str | None = None
    steps: list[LearningLessonStepRead]
    current_step_slug: str | None = None
    lesson_list: list[LearningLessonOutlineRead]


class LearningStepSubmitRequest(BaseModel):
    answer: dict[str, Any] | None = None


class LearningStepSubmitRead(BaseModel):
    course_slug: str
    module_slug: str
    lesson_slug: str
    step_slug: str
    passed: bool
    completed: bool
    score: int
    attempts: int
    feedback: LearningStepFeedbackRead
    lesson_progress_percent: int
    course_progress_percent: int
    lesson_completed: bool
    course_completed: bool
    next_step_slug: str | None = None
    next_lesson_slug: str | None = None
    resume_href: str
    weak_areas: list[LearningWeakAreaRead] = Field(default_factory=list)
    awarded_lmn: int = 0
    awarded_badge: str | None = None
    certificate_ready: bool = False
    economy: EconomyActionRead | None = None


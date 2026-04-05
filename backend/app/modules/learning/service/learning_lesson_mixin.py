from __future__ import annotations

from app.modules.learning.service.learning_lesson_projection_mixin import LearningLessonProjectionMixin
from app.modules.learning.service.learning_lesson_resolution_mixin import LearningLessonResolutionMixin
from app.modules.learning.service.learning_lesson_runtime_mixin import LearningLessonRuntimeMixin


class LearningLessonMixin(
    LearningLessonRuntimeMixin,
    LearningLessonProjectionMixin,
    LearningLessonResolutionMixin,
):
    """Lesson read flow composed from smaller mixins."""


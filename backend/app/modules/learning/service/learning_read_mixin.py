from __future__ import annotations

from app.modules.learning.service.learning_read_catalog_mixin import LearningReadCatalogMixin
from app.modules.learning.service.learning_read_course_mixin import LearningReadCourseMixin
from app.modules.learning.service.learning_read_resume_mixin import LearningReadResumeMixin


class LearningReadMixin(
    LearningReadCatalogMixin,
    LearningReadCourseMixin,
    LearningReadResumeMixin,
):
    """Composed learning read mixin with separated concerns."""


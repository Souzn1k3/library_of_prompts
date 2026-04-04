from app.core.i18n import SupportedLanguage
from app.core.errors import NotFoundError
from app.core.tiers import can_view_lesson, mask_body_if_needed
from app.infrastructure.db.models import User
from app.modules.education.model.lesson import LessonListItem, LessonRead, PopularLessonItem
from app.modules.education.repository.lesson_repository import LessonRepository
from app.modules.learning.content.catalog import find_lesson
from app.modules.learning.content.common import pick_text


class LessonService:
    def __init__(self, repo: LessonRepository) -> None:
        self._repo = repo

    def _localized_legacy_lesson_text(
        self,
        *,
        slug: str,
        title: str,
        body: str,
        language: SupportedLanguage,
    ) -> tuple[str, str]:
        located = find_lesson(slug)
        if located is None:
            return title, body

        _course_slug, _module_slug, lesson = located
        localized_title = pick_text(lesson["title"], language) if isinstance(lesson.get("title"), dict) else title
        localized_body = pick_text(lesson["summary"], language) if isinstance(lesson.get("summary"), dict) else body
        return localized_title or title, localized_body or body

    async def list_lessons(self, viewer: User | None, *, language: SupportedLanguage) -> list[LessonListItem]:
        rows = await self._repo.list_all()
        items: list[LessonListItem] = []
        for row in rows:
            locked = not can_view_lesson(viewer, row.min_tier)
            localized_title, _ = self._localized_legacy_lesson_text(
                slug=row.slug,
                title=row.title,
                body=row.body,
                language=language,
            )
            base = LessonListItem.model_validate(row).model_copy(update={"title": localized_title})
            items.append(base.model_copy(update={"locked": locked}))
        return items

    async def get_by_slug(self, slug: str, viewer: User | None, *, language: SupportedLanguage) -> LessonRead:
        row = await self._repo.get_by_slug(slug)
        if row is None:
            raise NotFoundError("lesson", slug)

        localized_title, localized_body = self._localized_legacy_lesson_text(
            slug=row.slug,
            title=row.title,
            body=row.body,
            language=language,
        )
        locked = not can_view_lesson(viewer, row.min_tier)
        body = mask_body_if_needed(body=localized_body, locked=locked)
        base = LessonListItem.model_validate(row).model_copy(update={"locked": locked, "title": localized_title})
        return LessonRead(**base.model_dump(), body=body, body_locked=locked)

    async def list_popular_lessons(
        self,
        viewer: User | None,
        *,
        limit: int = 8,
        language: SupportedLanguage,
    ) -> list[PopularLessonItem]:
        rows = await self._repo.list_popular(limit=limit)
        out: list[PopularLessonItem] = []
        for lesson, completion_count in rows:
            locked = not can_view_lesson(viewer, lesson.min_tier)
            localized_title, _ = self._localized_legacy_lesson_text(
                slug=lesson.slug,
                title=lesson.title,
                body=lesson.body,
                language=language,
            )
            base = LessonListItem.model_validate(lesson).model_copy(
                update={"locked": locked, "title": localized_title}
            )
            out.append(PopularLessonItem(**base.model_dump(), completion_count=completion_count))
        return out

from app.core.errors import NotFoundError
from app.core.tiers import can_view_lesson, mask_body_if_needed
from app.infrastructure.db.models import User
from app.modules.education.model.lesson import LessonListItem, LessonRead, PopularLessonItem
from app.modules.education.repository.lesson_repository import LessonRepository


class LessonService:
    def __init__(self, repo: LessonRepository) -> None:
        self._repo = repo

    async def list_lessons(self, viewer: User | None) -> list[LessonListItem]:
        rows = await self._repo.list_all()
        items: list[LessonListItem] = []
        for row in rows:
            locked = not can_view_lesson(viewer, row.min_tier)
            base = LessonListItem.model_validate(row)
            items.append(base.model_copy(update={"locked": locked}))
        return items

    async def get_by_slug(self, slug: str, viewer: User | None) -> LessonRead:
        row = await self._repo.get_by_slug(slug)
        if row is None:
            raise NotFoundError("lesson", slug)

        locked = not can_view_lesson(viewer, row.min_tier)
        body = mask_body_if_needed(body=row.body, locked=locked)
        base = LessonListItem.model_validate(row).model_copy(update={"locked": locked})
        return LessonRead(**base.model_dump(), body=body, body_locked=locked)

    async def list_popular_lessons(self, viewer: User | None, *, limit: int = 8) -> list[PopularLessonItem]:
        rows = await self._repo.list_popular(limit=limit)
        out: list[PopularLessonItem] = []
        for lesson, completion_count in rows:
            locked = not can_view_lesson(viewer, lesson.min_tier)
            base = LessonListItem.model_validate(lesson).model_copy(update={"locked": locked})
            out.append(PopularLessonItem(**base.model_dump(), completion_count=completion_count))
        return out

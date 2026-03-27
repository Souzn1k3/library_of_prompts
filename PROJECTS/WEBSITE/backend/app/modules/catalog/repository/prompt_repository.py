import uuid
from collections.abc import Sequence

from sqlalchemy import and_, case, delete, func, literal, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload, selectinload

from app.infrastructure.db.models import (
    Category,
    ContributorProfile,
    ContributorTier,
    ModelCompatibility,
    ModerationState,
    Prompt,
    PromptDifficulty,
    PromptModelCompatibility,
    PromptOutputType,
    PromptStats,
    PromptQualityMetric,
    PromptStatus,
    PromptTag,
    PromptTechnique,
    PromptUseCase,
    Tag,
    UseCase,
    User,
)
from app.modules.catalog.model.prompt import PromptSort


class PromptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _is_postgresql(self) -> bool:
        bind = self._session.bind
        return bool(bind and bind.dialect.name == "postgresql")

    def _insert(self, model):
        return pg_insert(model) if self._is_postgresql() else sqlite_insert(model)

    def _greatest(self, left, right):
        if self._is_postgresql():
            return func.greatest(left, right)
        return case((left >= right, left), else_=right)

    def _search_document(self):
        return func.to_tsvector(
            "english",
            func.coalesce(Prompt.title, "")
            + literal(" ")
            + func.coalesce(Prompt.summary, "")
            + literal(" ")
            + func.coalesce(Prompt.body, ""),
        )

    def _search_ranking(
        self,
        q: str | None,
        *,
        include_text_score: bool,
        include_contributor_score: bool,
    ):
        popularity_score = (
            (func.coalesce(PromptStats.save_count, 0) * 0.7 + func.coalesce(PromptStats.copy_count, 0) * 0.3)
            / 10.0
        )
        age_days = func.extract("epoch", func.now() - Prompt.created_at) / 86400.0
        recency_score = 1.0 / (1.0 + age_days / 14.0)
        quality_score = (
            self._greatest(
                func.coalesce(PromptQualityMetric.quality_score, 0),
                func.coalesce(PromptStats.quality_score, 0),
            )
            / 100.0
        )
        contributor_score = (
            func.coalesce(ContributorProfile.reputation_score, 0) / 100.0
            if include_contributor_score
            else literal(0.0)
        )

        if include_text_score and q and q.strip():
            normalized = q.strip().lower()
            if self._is_postgresql():
                doc = self._search_document()
                ts_query = func.plainto_tsquery("english", normalized)
                ts_rank = func.ts_rank_cd(doc, ts_query)
                fuzzy = func.greatest(
                    func.similarity(func.lower(Prompt.title), normalized),
                    func.similarity(func.lower(func.coalesce(Prompt.summary, "")), normalized),
                )
                text_score = ts_rank * 0.7 + fuzzy * 0.3
            else:
                like_pattern = f"%{normalized}%"
                phrase_title_match = case((func.lower(Prompt.title).like(like_pattern), 1.0), else_=0.0)
                phrase_summary_match = case(
                    (func.lower(func.coalesce(Prompt.summary, "")).like(like_pattern), 0.7),
                    else_=0.0,
                )
                phrase_body_match = case((func.lower(Prompt.body).like(like_pattern), 0.4), else_=0.0)
                phrase_score = phrase_title_match + phrase_summary_match + phrase_body_match

                # SQLite fallback for typo-tolerant intent search:
                # if the full phrase does not match, score token-level matches.
                tokens: list[str] = []
                seen: set[str] = set()
                for raw_token in normalized.split():
                    token = raw_token.strip()
                    if len(token) < 2 or token in seen:
                        continue
                    seen.add(token)
                    tokens.append(token)
                    if len(tokens) >= 6:
                        break

                token_score = literal(0.0)
                for token in tokens:
                    token_pattern = f"%{token}%"
                    token_score = token_score + (
                        case((func.lower(Prompt.title).like(token_pattern), 0.45), else_=0.0)
                        + case(
                            (func.lower(func.coalesce(Prompt.summary, "")).like(token_pattern), 0.25),
                            else_=0.0,
                        )
                        + case((func.lower(Prompt.body).like(token_pattern), 0.15), else_=0.0)
                    )

                text_score = phrase_score + token_score
        else:
            text_score = literal(0.0)

        relevance_score = (
            text_score * 0.5
            + popularity_score * 0.18
            + recency_score * 0.12
            + quality_score * 0.1
            + contributor_score * 0.1
        )
        trending_score = popularity_score * 0.52 + recency_score * 0.24 + quality_score * 0.14 + contributor_score * 0.1
        usage_score = func.coalesce(PromptStats.save_count, 0) + func.coalesce(PromptStats.copy_count, 0)
        save_score = func.coalesce(PromptStats.save_count, 0)
        return {
            "relevance": relevance_score,
            "trending": trending_score,
            "usage": usage_score,
            "save": save_score,
        }

    def _search_filters(
        self,
        *,
        q: str | None,
        contributor_slug: str | None,
        category_id: uuid.UUID | None,
        technique: PromptTechnique | None,
        difficulty: PromptDifficulty | None,
        output_type: PromptOutputType | None,
        use_cases: Sequence[str] | None,
        model_compatibility: Sequence[str] | None,
        tags: Sequence[str] | None,
        restrict_to_unrestricted_categories: bool,
        only_free: bool,
    ):
        parts = [Prompt.status == PromptStatus.published]
        if category_id is not None:
            parts.append(Prompt.category_id == category_id)
        if technique is not None:
            parts.append(Prompt.technique == technique)
        if difficulty is not None:
            parts.append(Prompt.difficulty == difficulty)
        if output_type is not None:
            parts.append(Prompt.output_type == output_type)
        if restrict_to_unrestricted_categories:
            parts.append(Category.is_restricted.is_(False))
        if only_free:
            parts.append(Prompt.is_premium.is_(False))
        if contributor_slug:
            parts.append(func.lower(ContributorProfile.slug) == contributor_slug.strip().lower())

        if use_cases:
            subq = (
                select(PromptUseCase.prompt_id)
                .join(UseCase, UseCase.id == PromptUseCase.use_case_id)
                .where(UseCase.slug.in_(list(use_cases)))
            )
            parts.append(Prompt.id.in_(subq))
        if model_compatibility:
            subq = (
                select(PromptModelCompatibility.prompt_id)
                .join(ModelCompatibility, ModelCompatibility.id == PromptModelCompatibility.model_id)
                .where(ModelCompatibility.slug.in_(list(model_compatibility)))
            )
            parts.append(Prompt.id.in_(subq))
        if tags:
            subq = (
                select(PromptTag.prompt_id)
                .join(Tag, Tag.id == PromptTag.tag_id)
                .where(Tag.slug.in_(list(tags)))
            )
            parts.append(Prompt.id.in_(subq))

        if q and q.strip():
            normalized = q.strip().lower()
            if self._is_postgresql():
                doc = self._search_document()
                ts_query = func.plainto_tsquery("english", normalized)
                fuzzy_title = func.similarity(func.lower(Prompt.title), normalized)
                fuzzy_summary = func.similarity(func.lower(func.coalesce(Prompt.summary, "")), normalized)
                parts.append(or_(doc.op("@@")(ts_query), fuzzy_title > 0.2, fuzzy_summary > 0.2))
            else:
                like_pattern = f"%{normalized}%"
                phrase_match = or_(
                    func.lower(Prompt.title).like(like_pattern),
                    func.lower(func.coalesce(Prompt.summary, "")).like(like_pattern),
                    func.lower(Prompt.body).like(like_pattern),
                )
                tokens: list[str] = []
                seen: set[str] = set()
                for raw_token in normalized.split():
                    token = raw_token.strip()
                    if len(token) < 2 or token in seen:
                        continue
                    seen.add(token)
                    tokens.append(token)
                    if len(tokens) >= 6:
                        break

                if not tokens:
                    parts.append(phrase_match)
                else:
                    token_hit_count = literal(0)
                    for token in tokens:
                        token_pattern = f"%{token}%"
                        token_hit_count = token_hit_count + case(
                            (
                                or_(
                                    func.lower(Prompt.title).like(token_pattern),
                                    func.lower(func.coalesce(Prompt.summary, "")).like(token_pattern),
                                    func.lower(Prompt.body).like(token_pattern),
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    minimum_hits = 1 if len(tokens) == 1 else 2
                    parts.append(or_(phrase_match, token_hit_count >= minimum_hits))

        return and_(*parts)

    def _apply_sort(self, stmt, *, sort: PromptSort, ranking: dict[str, object]):
        if sort == PromptSort.trending:
            return stmt.order_by(ranking["trending"].desc(), Prompt.created_at.desc())
        if sort == PromptSort.most_used:
            return stmt.order_by(ranking["usage"].desc(), Prompt.created_at.desc())
        if sort == PromptSort.newest:
            return stmt.order_by(Prompt.created_at.desc())
        if sort == PromptSort.most_saved:
            return stmt.order_by(ranking["save"].desc(), Prompt.created_at.desc())
        return stmt.order_by(ranking["relevance"].desc(), Prompt.created_at.desc())

    async def list_published(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        q: str | None = None,
        contributor_slug: str | None = None,
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
        difficulty: PromptDifficulty | None = None,
        output_type: PromptOutputType | None = None,
        use_cases: Sequence[str] | None = None,
        model_compatibility: Sequence[str] | None = None,
        tags: Sequence[str] | None = None,
        sort: PromptSort = PromptSort.relevance,
        restrict_to_unrestricted_categories: bool = False,
        only_free: bool = False,
    ) -> Sequence[Prompt]:
        include_text_score = sort == PromptSort.relevance
        include_contributor_score = sort in {PromptSort.relevance, PromptSort.trending} or bool(contributor_slug)

        ranking = self._search_ranking(
            q,
            include_text_score=include_text_score,
            include_contributor_score=include_contributor_score,
        )

        stmt = (
            select(Prompt)
            .join(Category, Prompt.category_id == Category.id)
            .outerjoin(PromptStats, PromptStats.prompt_id == Prompt.id)
            .outerjoin(PromptQualityMetric, PromptQualityMetric.prompt_id == Prompt.id)
            .where(
                self._search_filters(
                    q=q,
                    contributor_slug=contributor_slug,
                    category_id=category_id,
                    technique=technique,
                    difficulty=difficulty,
                    output_type=output_type,
                    use_cases=use_cases,
                    model_compatibility=model_compatibility,
                    tags=tags,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                    only_free=only_free,
                )
            )
        )

        if include_contributor_score:
            stmt = stmt.outerjoin(User, User.id == Prompt.author_id).outerjoin(
                ContributorProfile, ContributorProfile.user_id == User.id
            )
            stmt = stmt.options(
                contains_eager(Prompt.author).contains_eager(User.contributor_profile)
            )
        else:
            stmt = stmt.options(selectinload(Prompt.author).selectinload(User.contributor_profile))

        stmt = stmt.options(
            contains_eager(Prompt.category),
            contains_eager(Prompt.stats),
            contains_eager(Prompt.quality_metrics),
            selectinload(Prompt.use_case_links).selectinload(PromptUseCase.use_case),
            selectinload(Prompt.model_links).selectinload(PromptModelCompatibility.model),
            selectinload(Prompt.tag_links).selectinload(PromptTag.tag),
        )

        stmt = self._apply_sort(stmt, sort=sort, ranking=ranking).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return result.unique().scalars().all()

    async def count_published(
        self,
        *,
        q: str | None = None,
        contributor_slug: str | None = None,
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
        difficulty: PromptDifficulty | None = None,
        output_type: PromptOutputType | None = None,
        use_cases: Sequence[str] | None = None,
        model_compatibility: Sequence[str] | None = None,
        tags: Sequence[str] | None = None,
        restrict_to_unrestricted_categories: bool = False,
        only_free: bool = False,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Prompt)
            .join(Category, Prompt.category_id == Category.id)
            .where(
                self._search_filters(
                    q=q,
                    contributor_slug=contributor_slug,
                    category_id=category_id,
                    technique=technique,
                    difficulty=difficulty,
                    output_type=output_type,
                    use_cases=use_cases,
                    model_compatibility=model_compatibility,
                    tags=tags,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                    only_free=only_free,
                )
            )
        )
        if contributor_slug:
            stmt = stmt.outerjoin(User, User.id == Prompt.author_id).outerjoin(
                ContributorProfile, ContributorProfile.user_id == User.id
            )
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def list_trending(self, *, limit: int = 8, restrict_to_unrestricted_categories: bool) -> Sequence[Prompt]:
        return await self.list_published(
            skip=0,
            limit=limit,
            sort=PromptSort.trending,
            restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            only_free=False,
        )

    async def list_best_for_beginners(
        self,
        *,
        limit: int = 8,
        restrict_to_unrestricted_categories: bool,
    ) -> Sequence[Prompt]:
        return await self.list_published(
            skip=0,
            limit=limit,
            difficulty=PromptDifficulty.beginner,
            sort=PromptSort.relevance,
            restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            only_free=True,
        )

    async def list_most_saved(
        self,
        *,
        limit: int = 8,
        restrict_to_unrestricted_categories: bool,
    ) -> Sequence[Prompt]:
        return await self.list_published(
            skip=0,
            limit=limit,
            sort=PromptSort.most_saved,
            restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            only_free=False,
        )

    async def get_by_slug(self, slug: str) -> Prompt | None:
        stmt = (
            select(Prompt)
            .options(
                joinedload(Prompt.category),
                joinedload(Prompt.stats),
                joinedload(Prompt.quality_metrics),
                selectinload(Prompt.use_case_links).selectinload(PromptUseCase.use_case),
                selectinload(Prompt.model_links).selectinload(PromptModelCompatibility.model),
                selectinload(Prompt.tag_links).selectinload(PromptTag.tag),
                joinedload(Prompt.author).joinedload(User.contributor_profile),
            )
            .where(Prompt.slug == slug)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, prompt_id: uuid.UUID) -> Prompt | None:
        stmt = (
            select(Prompt)
            .options(
                joinedload(Prompt.category),
                joinedload(Prompt.stats),
                joinedload(Prompt.quality_metrics),
                selectinload(Prompt.use_case_links).selectinload(PromptUseCase.use_case),
                selectinload(Prompt.model_links).selectinload(PromptModelCompatibility.model),
                selectinload(Prompt.tag_links).selectinload(PromptTag.tag),
                joinedload(Prompt.author).joinedload(User.contributor_profile),
            )
            .where(Prompt.id == prompt_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_published_by_ids(
        self,
        prompt_ids: Sequence[uuid.UUID],
        *,
        restrict_to_unrestricted_categories: bool,
    ) -> Sequence[Prompt]:
        ids = list(dict.fromkeys(prompt_ids))
        if not ids:
            return []

        stmt = (
            select(Prompt)
            .options(
                joinedload(Prompt.category),
                joinedload(Prompt.stats),
                joinedload(Prompt.quality_metrics),
                selectinload(Prompt.use_case_links).selectinload(PromptUseCase.use_case),
                selectinload(Prompt.model_links).selectinload(PromptModelCompatibility.model),
                selectinload(Prompt.tag_links).selectinload(PromptTag.tag),
                joinedload(Prompt.author).joinedload(User.contributor_profile),
            )
            .where(
                Prompt.id.in_(ids),
                Prompt.status == PromptStatus.published,
            )
        )
        if restrict_to_unrestricted_categories:
            stmt = stmt.join(Category, Prompt.category_id == Category.id).where(Category.is_restricted.is_(False))

        result = await self._session.execute(stmt)
        return result.unique().scalars().all()

    async def list_related(
        self,
        *,
        prompt: Prompt,
        limit: int = 6,
        restrict_to_unrestricted_categories: bool,
    ) -> Sequence[Prompt]:
        tag_ids = [link.tag_id for link in prompt.tag_links]
        use_case_ids = [link.use_case_id for link in prompt.use_case_links]

        tag_match_subq = (
            select(PromptTag.prompt_id, func.count().label("tag_match_count"))
            .where(PromptTag.tag_id.in_(tag_ids))
            .group_by(PromptTag.prompt_id)
            .subquery()
            if tag_ids
            else None
        )
        use_case_match_subq = (
            select(PromptUseCase.prompt_id, func.count().label("use_case_match_count"))
            .where(PromptUseCase.use_case_id.in_(use_case_ids))
            .group_by(PromptUseCase.prompt_id)
            .subquery()
            if use_case_ids
            else None
        )

        stmt = (
            select(Prompt)
            .join(Category, Prompt.category_id == Category.id)
            .outerjoin(PromptStats, PromptStats.prompt_id == Prompt.id)
            .outerjoin(PromptQualityMetric, PromptQualityMetric.prompt_id == Prompt.id)
            .outerjoin(User, User.id == Prompt.author_id)
            .outerjoin(ContributorProfile, ContributorProfile.user_id == User.id)
            .options(
                contains_eager(Prompt.stats),
                contains_eager(Prompt.quality_metrics),
                selectinload(Prompt.use_case_links).selectinload(PromptUseCase.use_case),
                selectinload(Prompt.model_links).selectinload(PromptModelCompatibility.model),
                selectinload(Prompt.tag_links).selectinload(PromptTag.tag),
                contains_eager(Prompt.author).contains_eager(User.contributor_profile),
            )
            .where(
                Prompt.status == PromptStatus.published,
                Prompt.id != prompt.id,
            )
        )
        if restrict_to_unrestricted_categories:
            stmt = stmt.where(Category.is_restricted.is_(False))
        if tag_match_subq is not None:
            stmt = stmt.outerjoin(tag_match_subq, tag_match_subq.c.prompt_id == Prompt.id)
        if use_case_match_subq is not None:
            stmt = stmt.outerjoin(use_case_match_subq, use_case_match_subq.c.prompt_id == Prompt.id)

        related_score = (
            case((Prompt.category_id == prompt.category_id, 1.2), else_=0.0)
            + case((Prompt.technique == prompt.technique, 0.8), else_=0.0)
            + (func.coalesce(tag_match_subq.c.tag_match_count, 0) * 1.5 if tag_match_subq is not None else 0.0)
            + (
                func.coalesce(use_case_match_subq.c.use_case_match_count, 0) * 1.2
                if use_case_match_subq is not None
                else 0.0
            )
            + (func.coalesce(PromptStats.save_count, 0) * 0.05)
            + (func.coalesce(ContributorProfile.reputation_score, 0) * 0.01)
        )

        stmt = stmt.order_by(related_score.desc(), Prompt.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.unique().scalars().all()

    async def list_use_cases(self) -> Sequence[UseCase]:
        result = await self._session.execute(select(UseCase).order_by(UseCase.sort_order, UseCase.name))
        return result.scalars().all()

    async def list_model_compatibility(self) -> Sequence[ModelCompatibility]:
        result = await self._session.execute(
            select(ModelCompatibility).order_by(ModelCompatibility.sort_order, ModelCompatibility.name)
        )
        return result.scalars().all()

    async def list_tags(self) -> Sequence[Tag]:
        result = await self._session.execute(select(Tag).order_by(Tag.name))
        return result.scalars().all()

    async def get_use_cases_by_slugs(self, slugs: Sequence[str]) -> Sequence[UseCase]:
        if not slugs:
            return []
        result = await self._session.execute(select(UseCase).where(UseCase.slug.in_(list(slugs))))
        return result.scalars().all()

    async def get_model_compatibility_by_slugs(self, slugs: Sequence[str]) -> Sequence[ModelCompatibility]:
        if not slugs:
            return []
        result = await self._session.execute(
            select(ModelCompatibility).where(ModelCompatibility.slug.in_(list(slugs)))
        )
        return result.scalars().all()

    async def get_tags_by_slugs(self, slugs: Sequence[str]) -> Sequence[Tag]:
        if not slugs:
            return []
        result = await self._session.execute(select(Tag).where(Tag.slug.in_(list(slugs))))
        return result.scalars().all()

    async def create(self, prompt: Prompt) -> Prompt:
        self._session.add(prompt)
        await self._session.flush()
        await self._session.refresh(prompt)
        await self.ensure_prompt_stats(prompt.id)
        return prompt

    async def save(self, prompt: Prompt) -> Prompt:
        await self._session.flush()
        await self._session.refresh(prompt)
        return prompt

    async def ensure_prompt_stats(self, prompt_id: uuid.UUID) -> None:
        stmt = self._insert(PromptStats).values(
            prompt_id=prompt_id,
            save_count=0,
            copy_count=0,
            view_count=0,
            quality_score=40,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["prompt_id"])
        await self._session.execute(stmt)

    async def increment_copy_count(self, prompt_id: uuid.UUID, amount: int = 1) -> None:
        await self.ensure_prompt_stats(prompt_id)
        await self._session.execute(
            update(PromptStats)
            .where(PromptStats.prompt_id == prompt_id)
            .values(
                copy_count=PromptStats.copy_count + amount,
                updated_at=func.now(),
            )
        )

    async def increment_view_count(self, prompt_id: uuid.UUID, amount: int = 1) -> None:
        await self.ensure_prompt_stats(prompt_id)
        await self._session.execute(
            update(PromptStats)
            .where(PromptStats.prompt_id == prompt_id)
            .values(
                view_count=PromptStats.view_count + amount,
                updated_at=func.now(),
            )
        )

    async def adjust_save_count(self, prompt_id: uuid.UUID, delta: int) -> None:
        await self.ensure_prompt_stats(prompt_id)
        next_value = PromptStats.save_count + delta
        bounded_next_value = (
            func.greatest(next_value, 0)
            if self._is_postgresql()
            else case((next_value < 0, 0), else_=next_value)
        )
        await self._session.execute(
            update(PromptStats)
            .where(PromptStats.prompt_id == prompt_id)
            .values(
                save_count=bounded_next_value,
                updated_at=func.now(),
            )
        )

    async def set_prompt_use_cases(self, prompt_id: uuid.UUID, use_case_ids: Sequence[uuid.UUID]) -> None:
        await self._session.execute(delete(PromptUseCase).where(PromptUseCase.prompt_id == prompt_id))
        if not use_case_ids:
            return
        rows = [{"prompt_id": prompt_id, "use_case_id": use_case_id} for use_case_id in use_case_ids]
        await self._session.execute(self._insert(PromptUseCase).values(rows))

    async def set_prompt_models(self, prompt_id: uuid.UUID, model_ids: Sequence[uuid.UUID]) -> None:
        await self._session.execute(
            delete(PromptModelCompatibility).where(PromptModelCompatibility.prompt_id == prompt_id)
        )
        if not model_ids:
            return
        rows = [{"prompt_id": prompt_id, "model_id": model_id} for model_id in model_ids]
        await self._session.execute(self._insert(PromptModelCompatibility).values(rows))

    async def set_prompt_tags(self, prompt_id: uuid.UUID, tag_ids: Sequence[uuid.UUID]) -> None:
        await self._session.execute(delete(PromptTag).where(PromptTag.prompt_id == prompt_id))
        if not tag_ids:
            return
        rows = [{"prompt_id": prompt_id, "tag_id": tag_id} for tag_id in tag_ids]
        await self._session.execute(self._insert(PromptTag).values(rows))

    async def list_moderation_queue(self, *, skip: int = 0, limit: int = 50) -> Sequence[Prompt]:
        stmt = (
            select(Prompt)
            .outerjoin(User, User.id == Prompt.author_id)
            .outerjoin(ContributorProfile, ContributorProfile.user_id == User.id)
            .options(
                joinedload(Prompt.category),
                contains_eager(Prompt.author).contains_eager(User.contributor_profile),
            )
            .where(
                Prompt.status == PromptStatus.draft,
                Prompt.moderation_state == ModerationState.pending,
            )
            .order_by(
                func.coalesce(ContributorProfile.reputation_score, 0).desc(),
                Prompt.created_at.asc(),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.unique().scalars().all()

    async def list_by_author(
        self,
        author_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Prompt]:
        stmt = (
            select(Prompt)
            .where(Prompt.author_id == author_id)
            .order_by(Prompt.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import and_, case, func, literal, or_, select

from app.infrastructure.db.models import (
    Category,
    ModelCompatibility,
    Prompt,
    PromptDifficulty,
    PromptModelCompatibility,
    PromptOutputType,
    PromptQualityMetric,
    PromptStats,
    PromptStatus,
    PromptTag,
    PromptTechnique,
    PromptUseCase,
    Tag,
    UseCase,
    ContributorProfile,
)
from app.modules.catalog.model.prompt import PromptSort


class PromptRepositoryQueryMixin:
    def _search_tokens(self, normalized: str) -> list[str]:
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
        return tokens

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
        quality_score = func.coalesce(PromptQualityMetric.quality_score, 0) / 100.0
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

                tokens = self._search_tokens(normalized)

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
        category_id,
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
                tokens = self._search_tokens(normalized)

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

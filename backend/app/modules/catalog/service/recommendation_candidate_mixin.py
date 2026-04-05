from __future__ import annotations

from app.modules.catalog.model.prompt import PromptSort
from app.modules.catalog.service.recommendation_constants import BEGINNER_CANDIDATE_CONTEXTS


class RecommendationCandidateMixin:
    async def _candidate_pool(
        self,
        viewer,
        profile,
        *,
        context,
        limit: int,
        seed_prompt,
        seed_lesson,
        restrict_to_unrestricted_categories: bool,
        only_free: bool,
    ):
        fetch_limit = max(limit * 4, 18)
        top_categories = self._top_weighted_keys(profile.category_weights, 2)
        top_tags = self._top_weighted_keys(profile.tag_weights, 4)
        top_use_cases = self._top_weighted_keys(profile.use_case_weights, 3)
        top_models = self._top_weighted_keys(profile.model_weights, 2)
        query = self._keyword_query(profile.keyword_weights)
        generic_query = "workflow writing research code"
        tasks = [
            self._prompts.list_trending(
                limit=fetch_limit,
                restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            ),
            self._prompts.list_most_saved(
                limit=fetch_limit,
                restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            ),
        ]
        if context in BEGINNER_CANDIDATE_CONTEXTS or viewer is None:
            tasks.append(
                self._prompts.list_best_for_beginners(
                    limit=fetch_limit,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                )
            )

        candidate_query = query
        if candidate_query is None and viewer is None:
            candidate_query = generic_query
        if candidate_query:
            tasks.append(
                self._candidate_query_task(
                    fetch_limit=fetch_limit,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                    only_free=only_free,
                    q=candidate_query,
                    sort=PromptSort.relevance,
                )
            )
        for category_id in top_categories:
            tasks.append(
                self._candidate_query_task(
                    fetch_limit=fetch_limit,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                    only_free=only_free,
                    category_id=category_id,
                    sort=PromptSort.trending,
                )
            )
        for filter_key, values in (
            ("tags", top_tags),
            ("use_cases", top_use_cases),
            ("model_compatibility", top_models),
        ):
            if values:
                tasks.append(
                    self._candidate_query_task(
                        fetch_limit=fetch_limit,
                        restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                        only_free=only_free,
                        sort=PromptSort.trending,
                        **{filter_key: values},
                    )
                )
        if seed_prompt is not None:
            self._append_seed_tasks(
                tasks,
                seed_prompt=seed_prompt,
                fetch_limit=fetch_limit,
                restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                only_free=only_free,
            )
        if seed_lesson is not None:
            tasks.append(
                self._candidate_query_task(
                    fetch_limit=fetch_limit,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                    only_free=only_free,
                    q=seed_lesson.title,
                    sort=PromptSort.relevance,
                )
            )

        batches = []
        try:
            for task in tasks:
                batches.append(await task)
        finally:
            for pending in tasks[len(batches) :]:
                pending.close()
        excluded_ids = set(profile.saved_prompt_ids)
        if seed_prompt is not None:
            excluded_ids.add(seed_prompt.id)

        candidates = []
        seen_ids = set()
        for batch in batches:
            for row in batch:
                if row.id in seen_ids or row.id in excluded_ids:
                    continue
                seen_ids.add(row.id)
                candidates.append(row)
        return candidates

    def _append_seed_tasks(
        self,
        tasks: list,
        *,
        seed_prompt,
        fetch_limit: int,
        restrict_to_unrestricted_categories: bool,
        only_free: bool,
    ) -> None:
        seed_query = " ".join(filter(None, [seed_prompt.title, seed_prompt.summary or ""])).strip()
        seed_tags = [link.tag.slug for link in seed_prompt.tag_links if link.tag is not None][:4]
        seed_use_cases = [link.use_case.slug for link in seed_prompt.use_case_links if link.use_case is not None][:3]
        seed_models = [link.model.slug for link in seed_prompt.model_links if link.model is not None][:2]
        tasks.append(
            self._candidate_query_task(
                fetch_limit=fetch_limit,
                restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                only_free=only_free,
                category_id=seed_prompt.category_id,
                sort=PromptSort.trending,
            )
        )
        for filter_key, values in (
            ("tags", seed_tags),
            ("use_cases", seed_use_cases),
            ("model_compatibility", seed_models),
        ):
            if values:
                tasks.append(
                    self._candidate_query_task(
                        fetch_limit=fetch_limit,
                        restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                        only_free=only_free,
                        sort=PromptSort.trending,
                        **{filter_key: values},
                    )
                )
        if seed_query:
            tasks.append(
                self._candidate_query_task(
                    fetch_limit=fetch_limit,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                    only_free=only_free,
                    q=seed_query,
                    sort=PromptSort.relevance,
                )
            )

    def _candidate_query_task(
        self,
        *,
        fetch_limit: int,
        restrict_to_unrestricted_categories: bool,
        only_free: bool,
        sort: PromptSort,
        **filters,
    ):
        return self._prompts.list_published(
            skip=0,
            limit=fetch_limit,
            sort=sort,
            restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            only_free=only_free,
            **filters,
        )

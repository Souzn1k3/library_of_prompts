import { cache } from "react";

import {
  fetchCategories,
  fetchLearningCourse,
  fetchPromptBySlug,
  fetchRelatedPromptsBySlug,
} from "@/lib/api";
import { appRoute, LEARNING_FOUNDATIONS_COURSE_SLUG } from "@/lib/constants/routes";
import { getTranslation, type Language } from "@/lib/i18n";
import type { Category, PromptDetail, PromptListItem } from "@/lib/types";

export type PromptPageData = {
  prompt: PromptDetail;
  category: Category | undefined;
  related: PromptListItem[];
  foundationsCourseTitle: string;
  foundationsCourseHref: string;
};

export const getPromptBySlugCached = cache(
  async (slug: string, accessToken: string | null | undefined, language: Language) =>
    fetchPromptBySlug(slug, accessToken, language),
);

export async function loadPromptPageData({
  slug,
  accessToken,
  language,
}: {
  slug: string;
  accessToken: string | null | undefined;
  language: Language;
}): Promise<PromptPageData> {
  const prompt = await getPromptBySlugCached(slug, accessToken, language);
  const [categories, related, foundationsCourse] = await Promise.all([
    fetchCategories(accessToken, language),
    fetchRelatedPromptsBySlug(slug, { limit: 4, accessToken, language }).catch(() => [] as PromptListItem[]),
    fetchLearningCourse(LEARNING_FOUNDATIONS_COURSE_SLUG, accessToken, language).catch(() => null),
  ]);

  return {
    prompt,
    category: categories.find((item) => item.id === prompt.category_id),
    related,
    foundationsCourseTitle: foundationsCourse?.title ?? getTranslation(language, "learn.course"),
    foundationsCourseHref:
      foundationsCourse?.resume_href ?? appRoute.learnCourse(LEARNING_FOUNDATIONS_COURSE_SLUG),
  };
}

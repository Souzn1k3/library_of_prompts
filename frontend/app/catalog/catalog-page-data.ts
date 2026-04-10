import {
  ApiRequestError,
  fetchCategories,
  fetchDiscoverySections,
  fetchLearningCatalog,
  fetchPromptDiscoveryFilters,
  fetchPrompts,
} from "@/lib/api";
import { getTranslation, type Language } from "@/lib/i18n";
import type {
  Category,
  DiscoverySections,
  LearningCatalog,
  LearningCourseCard,
  PromptDiscoveryFilters,
  PromptListItem,
} from "@/lib/types";

function firstParam(v: string | string[] | undefined): string | undefined {
  if (typeof v === "string") return v;
  if (Array.isArray(v) && v.length > 0) return v[0];
  return undefined;
}

function multiParam(v: string | string[] | undefined): string[] | undefined {
  if (typeof v === "string") return v ? [v] : undefined;
  if (Array.isArray(v) && v.length > 0) return v;
  return undefined;
}

export type CatalogQueryState = {
  q: string | undefined;
  category_id: string | undefined;
  technique: string | undefined;
  difficulty: string | undefined;
  output_type: string | undefined;
  sort: string | undefined;
  use_case: string[] | undefined;
  model: string[] | undefined;
  tag: string[] | undefined;
  hasCustomFilters: boolean;
};

export type CatalogPageData = {
  query: CatalogQueryState;
  categories: Category[];
  prompts: PromptListItem[];
  recommendedCourses: LearningCourseCard[];
  discoveryFilters: PromptDiscoveryFilters;
  sections: DiscoverySections;
  error: string | null;
};

function selectRecommendedCourses(catalog: LearningCatalog | null, limit = 3): LearningCourseCard[] {
  if (!catalog || catalog.courses.length === 0 || limit <= 0) {
    return [];
  }

  const selected: LearningCourseCard[] = [];

  if (catalog.recommended_course_slug) {
    const recommended = catalog.courses.find((course) => course.slug === catalog.recommended_course_slug);
    if (recommended) {
      selected.push(recommended);
    }
  }

  for (const course of catalog.courses) {
    if (selected.length >= limit) {
      break;
    }
    if (!selected.some((item) => item.slug === course.slug)) {
      selected.push(course);
    }
  }

  return selected;
}

export function parseCatalogQuery(searchParams: Record<string, string | string[] | undefined>): CatalogQueryState {
  const q = firstParam(searchParams.q);
  const category_id = firstParam(searchParams.category_id);
  const technique = firstParam(searchParams.technique);
  const difficulty = firstParam(searchParams.difficulty);
  const output_type = firstParam(searchParams.output_type);
  const sort = firstParam(searchParams.sort);
  const use_case = multiParam(searchParams.use_case);
  const model = multiParam(searchParams.model);
  const tag = multiParam(searchParams.tag);

  return {
    q,
    category_id,
    technique,
    difficulty,
    output_type,
    sort,
    use_case,
    model,
    tag,
    hasCustomFilters: Boolean(
      q ||
      category_id ||
      technique ||
      difficulty ||
      output_type ||
      (use_case && use_case.length > 0) ||
      (model && model.length > 0) ||
      (tag && tag.length > 0) ||
      (sort && sort !== "relevance"),
    ),
  };
}

export async function loadCatalogPageData({
  query,
  accessToken,
  language,
}: {
  query: CatalogQueryState;
  accessToken?: string | null | undefined;
  language: Language;
}): Promise<CatalogPageData> {
  let categories: Category[] = [];
  let prompts: PromptListItem[] = [];
  let recommendedCourses: LearningCourseCard[] = [];
  let discoveryFilters: PromptDiscoveryFilters = {
    use_cases: [],
    model_compatibility: [],
    tags: [],
    difficulties: [],
    output_types: [],
    sorts: [],
  };
  let sections: DiscoverySections = { for_you: [], trending: [], best_for_beginners: [], most_saved: [] };
  let error: string | null = null;
  const fallbackSections: DiscoverySections = { for_you: [], trending: [], best_for_beginners: [], most_saved: [] };

  try {
    const [loadedCategories, loadedPrompts, loadedDiscoveryFilters, learningCatalog, loadedSections] = await Promise.all([
      fetchCategories(accessToken, language),
      fetchPrompts({
        limit: 24,
        q: query.q || undefined,
        category_id: query.category_id || undefined,
        technique: query.technique || undefined,
        difficulty: (query.difficulty as "beginner" | "intermediate" | "advanced" | undefined) || undefined,
        output_type: (query.output_type as "text" | "code" | "structured" | undefined) || undefined,
        use_case: query.use_case || undefined,
        model: query.model || undefined,
        tag: query.tag || undefined,
        sort:
          (query.sort as "relevance" | "trending" | "most_used" | "newest" | "most_saved" | undefined) || "relevance",
        accessToken,
        language,
      }),
      fetchPromptDiscoveryFilters(accessToken, language),
      query.hasCustomFilters ? Promise.resolve<LearningCatalog | null>(null) : fetchLearningCatalog(accessToken, language).catch(() => null),
      query.hasCustomFilters
        ? Promise.resolve(fallbackSections)
        : fetchDiscoverySections({ limit: 4, accessToken, language }).catch(() => fallbackSections),
    ]);
    categories = loadedCategories;
    prompts = loadedPrompts;
    discoveryFilters = loadedDiscoveryFilters;
    recommendedCourses = selectRecommendedCourses(learningCatalog);
    sections = loadedSections;
  } catch (e) {
    if (e instanceof ApiRequestError) {
      error = e.message;
    } else {
      error = getTranslation(language, "catalog.apiUnreachable");
    }
  }

  return {
    query,
    categories,
    prompts,
    recommendedCourses,
    discoveryFilters,
    sections,
    error,
  };
}

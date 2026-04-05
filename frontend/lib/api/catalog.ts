import { API_ENDPOINTS, apiPath } from "../constants/api";
import { withQuery } from "../http";
import type {
  Category,
  DiscoverySections,
  PromptDetail,
  PromptDifficulty,
  PromptDiscoveryFilters,
  PromptListItem,
  PromptOutputType,
  PromptRecommendationContext,
  PromptRecommendationResponse,
} from "../types";
import type { Language } from "../i18n";
import { localizePromptText, localizePromptTextList } from "../prompt-localization";
import { apiFetch } from "./transport";

export async function fetchCategories(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<Category[]> {
  return apiFetch<Category[]>(API_ENDPOINTS.categories, { accessToken, language });
}

export async function fetchPrompts(params?: {
  skip?: number;
  limit?: number;
  q?: string | null;
  contributor?: string | null;
  category_id?: string | null;
  technique?: string | null;
  difficulty?: PromptDifficulty | null;
  output_type?: PromptOutputType | null;
  use_case?: string[] | null;
  model?: string[] | null;
  tag?: string[] | null;
  sort?: "relevance" | "trending" | "most_used" | "newest" | "most_saved" | null;
  accessToken?: string | null;
  language?: Language | string | null;
}): Promise<PromptListItem[]> {
  const prompts = await apiFetch<PromptListItem[]>(
    withQuery(API_ENDPOINTS.prompts, {
      skip: params?.skip,
      limit: params?.limit,
      q: params?.q,
      contributor: params?.contributor,
      category_id: params?.category_id,
      technique: params?.technique,
      difficulty: params?.difficulty,
      output_type: params?.output_type,
      use_case: params?.use_case,
      model: params?.model,
      tag: params?.tag,
      sort: params?.sort,
    }),
    {
      accessToken: params?.accessToken,
      language: params?.language,
    },
  );
  return localizePromptTextList(prompts, params?.language);
}

export async function fetchPromptDiscoveryFilters(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<PromptDiscoveryFilters> {
  return apiFetch<PromptDiscoveryFilters>(API_ENDPOINTS.promptDiscoveryFilters, {
    accessToken,
    language,
  });
}

export async function fetchDiscoverySections(
  params?: {
    limit?: number;
    accessToken?: string | null;
    language?: Language | string | null;
  },
): Promise<DiscoverySections> {
  const sections = await apiFetch<DiscoverySections>(withQuery(API_ENDPOINTS.promptDiscoverySections, { limit: params?.limit }), {
    accessToken: params?.accessToken,
    language: params?.language,
  });
  return {
    ...sections,
    for_you: sections.for_you ? localizePromptTextList(sections.for_you, params?.language) : undefined,
    trending: localizePromptTextList(sections.trending, params?.language),
    best_for_beginners: localizePromptTextList(sections.best_for_beginners, params?.language),
    most_saved: localizePromptTextList(sections.most_saved, params?.language),
  };
}

export async function fetchRelatedPromptsBySlug(
  slug: string,
  params?: {
    limit?: number;
    accessToken?: string | null;
    language?: Language | string | null;
  },
): Promise<PromptListItem[]> {
  const prompts = await apiFetch<PromptListItem[]>(
    withQuery(apiPath.promptRelatedBySlug(slug), {
      limit: params?.limit,
    }),
    {
      accessToken: params?.accessToken,
      language: params?.language,
    },
  );
  return localizePromptTextList(prompts, params?.language);
}

export async function fetchPromptRecommendations(
  params?: {
    context?: PromptRecommendationContext;
    limit?: number;
    prompt_slug?: string | null;
    lesson_slug?: string | null;
    accessToken?: string | null;
    language?: Language | string | null;
  },
): Promise<PromptRecommendationResponse> {
  const response = await apiFetch<PromptRecommendationResponse>(withQuery(API_ENDPOINTS.promptRecommendations, {
    context: params?.context,
    limit: params?.limit,
    prompt_slug: params?.prompt_slug,
    lesson_slug: params?.lesson_slug,
  }), {
    accessToken: params?.accessToken,
    language: params?.language,
  });
  return {
    ...response,
    items: localizePromptTextList(response.items, params?.language),
  };
}

export async function fetchPromptBySlug(
  slug: string,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<PromptDetail> {
  const prompt = await apiFetch<PromptDetail>(apiPath.promptBySlug(slug), {
    accessToken,
    language,
  });
  return localizePromptText(prompt, language);
}

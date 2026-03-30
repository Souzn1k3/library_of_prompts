import type {
  BillingStatus,
  Category,
  ContributorProfile,
  ContributorTopItem,
  DiscoverySections,
  LessonDetail,
  LessonListItem,
  PopularLessonItem,
  PlanRecord,
  PromptDiscoveryFilters,
  PromptDifficulty,
  PromptDetail,
  PromptListItem,
  PromptOutputType,
  PromptRecommendationContext,
  PromptRecommendationResponse,
} from "./types";
import { getClientLanguage, getTranslation, normalizeLanguage, type Language } from "./i18n";
import { extractApiErrorMessage, parseJson, withQuery } from "./http";

type NextFetchInit = RequestInit & {
  next?: { revalidate?: number; tags?: string[] };
};

type ApiFetchInit = NextFetchInit & {
  accessToken?: string | null;
  language?: Language | string | null;
};

/**
 * Browser uses NEXT_PUBLIC_API_URL. Server components in Docker should set API_URL
 * to the internal service URL (e.g. http://api:8000) while keeping NEXT_PUBLIC_API_URL
 * for the public origin the browser calls.
 */
export function getApiBaseUrl(): string {
  const fallbackLocalApiUrl = "http://localhost:8000";

  if (typeof window === "undefined") {
    return (
      process.env.API_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      fallbackLocalApiUrl
    );
  }

  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // Keep frontend/backend on the same host in local dev so SameSite=Lax auth cookies work.
  const hostname = window.location.hostname || "localhost";
  const host = hostname.includes(":") ? `[${hostname}]` : hostname;
  return `http://${host}:8000`;
}

export class ApiRequestError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.body = body;
  }
}

async function apiFetch<T>(path: string, init?: ApiFetchInit): Promise<T> {
  const url = `${getApiBaseUrl()}${path}`;
  const { accessToken, language, ...fetchInit } = init ?? {};
  const isAuthedRequest = Boolean(accessToken);
  const activeLanguage = normalizeLanguage(
    language ?? (typeof window !== "undefined" ? getClientLanguage() : undefined),
  );
  const includeCredentials = typeof window !== "undefined";
  let res: Response;
  try {
    res = await fetch(url, {
      ...fetchInit,
      cache: fetchInit.cache ?? (isAuthedRequest ? "no-store" : undefined),
      credentials: includeCredentials ? "include" : fetchInit.credentials,
      headers: {
        Accept: "application/json",
        "Accept-Language": activeLanguage,
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...(fetchInit.headers ?? {}),
      },
      next: isAuthedRequest ? undefined : fetchInit.next ?? { revalidate: 30 },
    });
  } catch {
    const message = extractApiErrorMessage(
      undefined,
      0,
      getTranslation(activeLanguage, "api.requestFailed"),
      activeLanguage,
    );
    throw new ApiRequestError(message, 0, null);
  }

  const data = await parseJson<unknown>(res);

  if (!res.ok) {
    const message = extractApiErrorMessage(
      data,
      res.status,
      getTranslation(activeLanguage, "api.requestFailed"),
      activeLanguage,
    );
    throw new ApiRequestError(message, res.status, data);
  }

  return data as T;
}

export async function fetchCategories(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<Category[]> {
  return apiFetch<Category[]>("/api/v1/categories", { accessToken, language });
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
  return apiFetch<PromptListItem[]>(
    withQuery("/api/v1/prompts", {
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
}

export async function fetchPromptDiscoveryFilters(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<PromptDiscoveryFilters> {
  return apiFetch<PromptDiscoveryFilters>("/api/v1/prompts/discovery-filters", {
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
  return apiFetch<DiscoverySections>(withQuery("/api/v1/prompts/discovery-sections", { limit: params?.limit }), {
    accessToken: params?.accessToken,
    language: params?.language,
  });
}

export async function fetchRelatedPromptsBySlug(
  slug: string,
  params?: {
    limit?: number;
    accessToken?: string | null;
    language?: Language | string | null;
  },
): Promise<PromptListItem[]> {
  return apiFetch<PromptListItem[]>(
    withQuery(`/api/v1/prompts/by-slug/${encodeURIComponent(slug)}/related`, {
      limit: params?.limit,
    }),
    {
      accessToken: params?.accessToken,
      language: params?.language,
    },
  );
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
  return apiFetch<PromptRecommendationResponse>(withQuery("/api/v1/prompts/recommendations", {
    context: params?.context,
    limit: params?.limit,
    prompt_slug: params?.prompt_slug,
    lesson_slug: params?.lesson_slug,
  }), {
    accessToken: params?.accessToken,
    language: params?.language,
  });
}

export async function fetchPromptBySlug(
  slug: string,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<PromptDetail> {
  return apiFetch<PromptDetail>(`/api/v1/prompts/by-slug/${encodeURIComponent(slug)}`, {
    accessToken,
    language,
  });
}

export async function fetchTopContributors(
  params?: {
    limit?: number;
    accessToken?: string | null;
    language?: Language | string | null;
  },
): Promise<ContributorTopItem[]> {
  return apiFetch<ContributorTopItem[]>(withQuery("/api/v1/contributors/top", { limit: params?.limit }), {
    accessToken: params?.accessToken,
    language: params?.language,
  });
}

export async function fetchContributorProfile(
  slug: string,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<ContributorProfile> {
  return apiFetch<ContributorProfile>(`/api/v1/contributors/${encodeURIComponent(slug)}`, {
    accessToken,
    language,
  });
}

export async function fetchPlans(language?: Language | string | null): Promise<PlanRecord[]> {
  return apiFetch<PlanRecord[]>("/api/v1/billing/plans", { language });
}

export async function fetchBillingStatus(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<BillingStatus> {
  return apiFetch<BillingStatus>("/api/v1/billing/subscription", {
    accessToken,
    language,
    cache: "no-store",
  });
}

export async function fetchLessons(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<LessonListItem[]> {
  return apiFetch<LessonListItem[]>("/api/v1/lessons", { accessToken, language });
}

export async function fetchPopularLessons(
  params?: {
    limit?: number;
    accessToken?: string | null;
    language?: Language | string | null;
  },
): Promise<PopularLessonItem[]> {
  return apiFetch<PopularLessonItem[]>(withQuery("/api/v1/lessons/popular", { limit: params?.limit }), {
    accessToken: params?.accessToken,
    language: params?.language,
  });
}

export async function fetchLessonBySlug(
  slug: string,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<LessonDetail> {
  return apiFetch<LessonDetail>(`/api/v1/lessons/by-slug/${encodeURIComponent(slug)}`, {
    accessToken,
    language,
  });
}

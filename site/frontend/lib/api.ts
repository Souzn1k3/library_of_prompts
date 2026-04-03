import type {
  Category,
  LessonDetail,
  LessonListItem,
  PlanRecord,
  PromptDetail,
  PromptListItem,
} from "./types";

type NextFetchInit = RequestInit & {
  next?: { revalidate?: number; tags?: string[] };
};

/**
 * Browser uses NEXT_PUBLIC_API_URL. Server components in Docker should set API_URL
 * to the internal service URL (e.g. http://api:8000) while keeping NEXT_PUBLIC_API_URL
 * for the public origin the browser calls.
 */
export function getApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return (
      process.env.API_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      "http://127.0.0.1:8000"
    );
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
}

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
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

async function apiFetch<T>(path: string, init?: NextFetchInit): Promise<T> {
  const url = `${getApiBaseUrl()}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
    next: init?.next ?? { revalidate: 30 },
  });

  const data = await parseJson<unknown>(res);

  if (!res.ok) {
    const message =
      typeof data === "object" && data && "message" in data
        ? String((data as { message: unknown }).message)
        : `Request failed (${res.status})`;
    throw new ApiRequestError(message, res.status, data);
  }

  return data as T;
}

export async function fetchCategories(): Promise<Category[]> {
  return apiFetch<Category[]>("/api/v1/categories");
}

export async function fetchPrompts(params?: {
  skip?: number;
  limit?: number;
  q?: string | null;
  category_id?: string | null;
  technique?: string | null;
}): Promise<PromptListItem[]> {
  const sp = new URLSearchParams();
  if (params?.skip != null) sp.set("skip", String(params.skip));
  if (params?.limit != null) sp.set("limit", String(params.limit));
  if (params?.q) sp.set("q", params.q);
  if (params?.category_id) sp.set("category_id", params.category_id);
  if (params?.technique) sp.set("technique", params.technique);
  const q = sp.toString();
  return apiFetch<PromptListItem[]>(`/api/v1/prompts${q ? `?${q}` : ""}`);
}

export async function fetchPromptBySlug(slug: string): Promise<PromptDetail> {
  return apiFetch<PromptDetail>(`/api/v1/prompts/by-slug/${encodeURIComponent(slug)}`);
}

export async function fetchPlans(): Promise<PlanRecord[]> {
  return apiFetch<PlanRecord[]>("/api/v1/billing/plans");
}

export async function fetchLessons(): Promise<LessonListItem[]> {
  return apiFetch<LessonListItem[]>("/api/v1/lessons");
}

export async function fetchLessonBySlug(slug: string): Promise<LessonDetail> {
  return apiFetch<LessonDetail>(`/api/v1/lessons/by-slug/${encodeURIComponent(slug)}`);
}

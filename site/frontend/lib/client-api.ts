import { ApiRequestError, getApiBaseUrl } from "./api";
import { getToken } from "./auth";
import type { PromptListItem, TokenResponse, UserProfile } from "./types";

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
}

export async function loginRequest(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${getApiBaseUrl()}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ email, password }),
    cache: "no-store",
  });
  const data = await parseJson<unknown>(res);
  if (!res.ok) {
    const message =
      typeof data === "object" && data && "message" in data
        ? String((data as { message: unknown }).message)
        : `Request failed (${res.status})`;
    throw new ApiRequestError(message, res.status, data);
  }
  return data as TokenResponse;
}

export async function registerRequest(
  email: string,
  password: string,
  displayName: string,
): Promise<TokenResponse> {
  const res = await fetch(`${getApiBaseUrl()}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ email, password, display_name: displayName }),
    cache: "no-store",
  });
  const data = await parseJson<unknown>(res);
  if (!res.ok) {
    const message =
      typeof data === "object" && data && "message" in data
        ? String((data as { message: unknown }).message)
        : `Request failed (${res.status})`;
    throw new ApiRequestError(message, res.status, data);
  }
  return data as TokenResponse;
}

async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
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

export async function fetchMe(): Promise<UserProfile> {
  return authFetch<UserProfile>("/api/v1/users/me");
}

export async function fetchSavedPrompts(): Promise<PromptListItem[]> {
  return authFetch<PromptListItem[]>("/api/v1/users/me/saved-prompts");
}

export async function savePrompt(promptId: string): Promise<void> {
  const res = await fetch(`${getApiBaseUrl()}/api/v1/users/me/saved-prompts/${promptId}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const data = await parseJson<unknown>(res);
    const message =
      typeof data === "object" && data && "message" in data
        ? String((data as { message: unknown }).message)
        : `Request failed (${res.status})`;
    throw new ApiRequestError(message, res.status, data);
  }
}

export async function submitPrompt(body: {
  slug: string;
  title: string;
  body: string;
  summary?: string | null;
  category_id: string;
  technique: string;
}): Promise<{ id: string; slug: string; status: string; moderation_state: string }> {
  return authFetch(`/api/v1/contributions/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function unsavePrompt(promptId: string): Promise<void> {
  const res = await fetch(`${getApiBaseUrl()}/api/v1/users/me/saved-prompts/${promptId}`, {
    method: "DELETE",
    headers: {
      Accept: "application/json",
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const data = await parseJson<unknown>(res);
    const message =
      typeof data === "object" && data && "message" in data
        ? String((data as { message: unknown }).message)
        : `Request failed (${res.status})`;
    throw new ApiRequestError(message, res.status, data);
  }
}

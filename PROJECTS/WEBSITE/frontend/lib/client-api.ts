import { ApiRequestError, getApiBaseUrl } from "./api";
import { emitAuthStateChange } from "./auth";
import { getClientLanguage, getTranslation, type Language } from "./i18n";
import { extractApiErrorMessage, parseJson, withQuery } from "./http";
import type {
  AuthorSubmission,
  BillingStatus,
  CheckoutSessionResult,
  ContributorProfile,
  ContributorTopItem,
  MissionCurrentRead,
  MissionListRead,
  MissionRead,
  WalletRead,
  StoreItem,
  PurchaseResult,
  OnboardingGoal,
  OnboardingProfile,
  OnboardingRole,
  OnboardingStarterPack,
  PromptListItem,
  PromptRecommendationContext,
  PromptRecommendationResponse,
  UserProfile,
} from "./types";

let refreshInFlight: Promise<boolean> | null = null;

function networkError(language: Language): ApiRequestError {
  return new ApiRequestError(
    extractApiErrorMessage(undefined, 0, getTranslation(language, "api.requestFailed"), language),
    0,
    null,
  );
}

function requestHeaders(language: string, initHeaders?: HeadersInit): HeadersInit {
  return {
    Accept: "application/json",
    "Accept-Language": language,
    ...(initHeaders ?? {}),
  };
}

function jsonInit(method: "POST" | "PUT" | "DELETE", body?: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  };
}

async function refreshSession(language: string): Promise<boolean> {
  if (refreshInFlight) {
    return refreshInFlight;
  }
  refreshInFlight = (async () => {
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/v1/auth/refresh`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Accept-Language": language,
        },
        credentials: "include",
        cache: "no-store",
      });
      if (!res.ok) {
        emitAuthStateChange({ reason: "refresh" });
        return false;
      }
      await parseJson<unknown>(res);
      return true;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

async function authFetchRaw(path: string, init?: RequestInit, canRetry = true): Promise<Response> {
  const language = getClientLanguage();
  const url = `${getApiBaseUrl()}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: requestHeaders(language, init?.headers),
      credentials: "include",
      cache: "no-store",
    });
  } catch {
    throw networkError(language);
  }

  if (response.status === 401 && canRetry) {
    const refreshed = await refreshSession(language);
    if (refreshed) {
      return authFetchRaw(path, init, false);
    }
  }

  if (response.status === 401) {
    emitAuthStateChange({ reason: "expired" });
  }

  return response;
}

async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const language = getClientLanguage();
  const res = await authFetchRaw(path, init);
  const data = await parseJson<unknown>(res);
  if (!res.ok) {
    const message = extractApiErrorMessage(
      data,
      res.status,
      getTranslation(language, "api.requestFailed"),
      language,
    );
    throw new ApiRequestError(message, res.status, data);
  }
  return data as T;
}

async function authFetchNoContent(path: string, init?: RequestInit): Promise<void> {
  const language = getClientLanguage();
  const res = await authFetchRaw(path, init);
  if (!res.ok) {
    const data = await parseJson<unknown>(res);
    const message = extractApiErrorMessage(
      data,
      res.status,
      getTranslation(language, "api.requestFailed"),
      language,
    );
    throw new ApiRequestError(message, res.status, data);
  }
}

async function optionalAuthJsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const language = getClientLanguage();
  let res: Response;
  try {
    res = await fetch(`${getApiBaseUrl()}${path}`, {
      ...init,
      headers: requestHeaders(language, init?.headers),
      credentials: "include",
      cache: "no-store",
    });
  } catch {
    throw networkError(language);
  }
  const data = await parseJson<unknown>(res);
  if (!res.ok) {
    const message = extractApiErrorMessage(
      data,
      res.status,
      getTranslation(language, "api.requestFailed"),
      language,
    );
    throw new ApiRequestError(message, res.status, data);
  }
  return data as T;
}

export async function loginRequest(email: string, password: string): Promise<void> {
  await optionalAuthJsonFetch<unknown>("/api/v1/auth/login", jsonInit("POST", { email, password }));
}

export async function registerRequest(
  email: string,
  password: string,
  displayName: string,
): Promise<void> {
  await optionalAuthJsonFetch<unknown>(
    "/api/v1/auth/register",
    jsonInit("POST", { email, password, display_name: displayName }),
  );
}

export async function logoutRequest(): Promise<void> {
  try {
    await authFetchNoContent("/api/v1/auth/logout", jsonInit("POST", {}));
  } finally {
    emitAuthStateChange({ reason: "logout" });
  }
}

export async function fetchMe(): Promise<UserProfile> {
  return authFetch<UserProfile>("/api/v1/users/me");
}

export async function fetchBillingStatus(): Promise<BillingStatus> {
  return authFetch<BillingStatus>("/api/v1/billing/subscription");
}

export async function fetchOnboardingProfile(): Promise<OnboardingProfile> {
  return authFetch<OnboardingProfile>("/api/v1/onboarding/profile");
}

export async function updateOnboardingProfile(body: {
  role: OnboardingRole;
  goal: OnboardingGoal;
  ai_context: string;
}): Promise<OnboardingProfile> {
  return authFetch<OnboardingProfile>("/api/v1/onboarding/profile", jsonInit("PUT", body));
}

export async function skipOnboarding(): Promise<OnboardingProfile> {
  return authFetch<OnboardingProfile>("/api/v1/onboarding/skip", jsonInit("POST", {}));
}

export async function fetchOnboardingStarterPack(): Promise<OnboardingStarterPack> {
  return authFetch<OnboardingStarterPack>("/api/v1/onboarding/starter-pack");
}

export async function completeOnboardingFirstWin(body: {
  prompt_id: string;
  action: string;
}): Promise<OnboardingProfile> {
  return authFetch<OnboardingProfile>("/api/v1/onboarding/first-win", jsonInit("POST", body));
}

export async function fetchCurrentMission(): Promise<MissionCurrentRead> {
  return authFetch<MissionCurrentRead>("/api/v1/missions/current");
}

export async function fetchMissions(): Promise<MissionListRead> {
  return authFetch<MissionListRead>("/api/v1/missions");
}

export async function fetchMissionBySlug(slug: string): Promise<MissionRead> {
  return authFetch<MissionRead>(`/api/v1/missions/${encodeURIComponent(slug)}`);
}

export async function fetchWallet(): Promise<WalletRead> {
  return authFetch<WalletRead>("/api/v1/wallet");
}

export async function walletCheckIn(): Promise<WalletRead> {
  return authFetch<WalletRead>("/api/v1/wallet/check-in", {
    method: "POST",
  });
}

export async function fetchStoreItems(): Promise<StoreItem[]> {
  return authFetch<StoreItem[]>("/api/v1/store");
}

export async function purchaseStoreItem(slug: string, clientToken?: string): Promise<PurchaseResult> {
  return authFetch<PurchaseResult>(
    `/api/v1/store/${encodeURIComponent(slug)}/purchase`,
    jsonInit("POST", { client_token: clientToken ?? null }),
  );
}

export async function completeLesson(slug: string): Promise<void> {
  return authFetchNoContent(`/api/v1/lessons/by-slug/${encodeURIComponent(slug)}/complete`, {
    method: "POST",
  });
}

export async function createCheckoutSession(tier: string): Promise<CheckoutSessionResult> {
  return authFetch<CheckoutSessionResult>("/api/v1/billing/checkout/session", jsonInit("POST", { tier }));
}

export async function createBillingPortalSession(): Promise<{ url: string }> {
  return authFetch<{ url: string }>("/api/v1/billing/portal", jsonInit("POST", {}));
}

export async function fetchSavedPrompts(): Promise<PromptListItem[]> {
  return authFetch<PromptListItem[]>("/api/v1/users/me/saved-prompts");
}

export async function fetchMySubmissions(): Promise<AuthorSubmission[]> {
  return authFetch<AuthorSubmission[]>("/api/v1/users/me/submissions");
}

export async function fetchTopContributors(limit = 12): Promise<ContributorTopItem[]> {
  return optionalAuthJsonFetch<ContributorTopItem[]>(withQuery("/api/v1/contributors/top", { limit }));
}

export async function fetchPromptRecommendations(params?: {
  context?: PromptRecommendationContext;
  limit?: number;
  prompt_slug?: string | null;
  lesson_slug?: string | null;
}): Promise<PromptRecommendationResponse> {
  return authFetch<PromptRecommendationResponse>(withQuery("/api/v1/prompts/recommendations", {
    context: params?.context,
    limit: params?.limit,
    prompt_slug: params?.prompt_slug,
    lesson_slug: params?.lesson_slug,
  }));
}

export async function fetchContributorProfile(slug: string): Promise<ContributorProfile> {
  return optionalAuthJsonFetch<ContributorProfile>(
    `/api/v1/contributors/${encodeURIComponent(slug)}`,
  );
}

export async function savePrompt(promptId: string): Promise<void> {
  return authFetchNoContent(`/api/v1/users/me/saved-prompts/${promptId}`, {
    method: "POST",
  });
}

export async function submitPrompt(body: {
  slug: string;
  title: string;
  body: string;
  summary?: string | null;
  category_id: string;
  technique: string;
  difficulty?: "beginner" | "intermediate" | "advanced" | null;
  output_type?: "text" | "code" | "structured" | null;
  use_cases?: string[];
  model_compatibility?: string[];
  tags?: string[];
}): Promise<{ id: string; slug: string; status: string; moderation_state: string; auto_approved?: boolean }> {
  return authFetch("/api/v1/contributions/submit", jsonInit("POST", body));
}

export async function unsavePrompt(promptId: string): Promise<void> {
  return authFetchNoContent(`/api/v1/users/me/saved-prompts/${promptId}`, {
    method: "DELETE",
  });
}

export async function trackPromptCopy(promptId: string): Promise<void> {
  return authFetchNoContent(`/api/v1/prompts/${promptId}/events/copy`, {
    method: "POST",
  });
}

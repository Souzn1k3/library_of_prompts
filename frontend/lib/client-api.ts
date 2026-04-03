import { ApiRequestError, getApiBaseUrl } from "./api";
import { emitAuthStateChange } from "./auth";
import { API_ENDPOINTS, apiPath } from "./constants/api";
import { getClientLanguage, getTranslation, type Language } from "./i18n";
import { extractApiErrorMessage, parseJson, withQuery } from "./http";
import type {
  AuthorSubmission,
  BillingStatus,
  CheckoutSessionResult,
  ContributorProfile,
  ContributorTopItem,
  EconomyAction,
  MarketplaceOverview,
  OnboardingFirstWinResult,
  MissionCurrentRead,
  MissionListRead,
  MissionRead,
  PromptMarketplacePurchase,
  PromptReview,
  PromptActionResult,
  WalletRead,
  StoreItem,
  PurchaseResult,
  OnboardingGoal,
  OnboardingProfile,
  OnboardingRole,
  OnboardingStarterPack,
  LessonCompletionResult,
  LearningStepSubmitResponse,
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
      const res = await fetch(`${getApiBaseUrl()}${API_ENDPOINTS.auth.refresh}`, {
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
  await optionalAuthJsonFetch<unknown>(API_ENDPOINTS.auth.login, jsonInit("POST", { email, password }));
}

export async function registerRequest(
  email: string,
  password: string,
  displayName: string,
): Promise<void> {
  await optionalAuthJsonFetch<unknown>(
    API_ENDPOINTS.auth.register,
    jsonInit("POST", { email, password, display_name: displayName }),
  );
}

export async function logoutRequest(): Promise<void> {
  try {
    await authFetchNoContent(API_ENDPOINTS.auth.logout, jsonInit("POST", {}));
  } finally {
    emitAuthStateChange({ reason: "logout" });
  }
}

export async function fetchMe(): Promise<UserProfile> {
  return authFetch<UserProfile>(API_ENDPOINTS.usersMe);
}

export async function fetchBillingStatus(): Promise<BillingStatus> {
  return authFetch<BillingStatus>(API_ENDPOINTS.billingSubscription);
}

export async function fetchMarketplaceOverview(): Promise<MarketplaceOverview> {
  return authFetch<MarketplaceOverview>(API_ENDPOINTS.marketplaceMe);
}

export async function fetchOnboardingProfile(): Promise<OnboardingProfile> {
  return authFetch<OnboardingProfile>(API_ENDPOINTS.onboardingProfile);
}

export async function updateOnboardingProfile(body: {
  role: OnboardingRole;
  goal: OnboardingGoal;
  ai_context: string;
}): Promise<OnboardingProfile> {
  return authFetch<OnboardingProfile>(API_ENDPOINTS.onboardingProfile, jsonInit("PUT", body));
}

export async function skipOnboarding(): Promise<OnboardingProfile> {
  return authFetch<OnboardingProfile>(API_ENDPOINTS.onboardingSkip, jsonInit("POST", {}));
}

export async function fetchOnboardingStarterPack(): Promise<OnboardingStarterPack> {
  return authFetch<OnboardingStarterPack>(API_ENDPOINTS.onboardingStarterPack);
}

export async function completeOnboardingFirstWin(body: {
  prompt_id: string;
  action: string;
}): Promise<OnboardingFirstWinResult> {
  return authFetch<OnboardingFirstWinResult>(API_ENDPOINTS.onboardingFirstWin, jsonInit("POST", body));
}

export async function fetchCurrentMission(): Promise<MissionCurrentRead> {
  return authFetch<MissionCurrentRead>(API_ENDPOINTS.missionsCurrent);
}

export async function fetchMissions(): Promise<MissionListRead> {
  return authFetch<MissionListRead>(API_ENDPOINTS.missions);
}

export async function fetchMissionBySlug(slug: string): Promise<MissionRead> {
  return authFetch<MissionRead>(apiPath.missionBySlug(slug));
}

export async function fetchWallet(): Promise<WalletRead> {
  return authFetch<WalletRead>(API_ENDPOINTS.wallet);
}

export async function walletCheckIn(): Promise<WalletRead> {
  return authFetch<WalletRead>(API_ENDPOINTS.walletCheckIn, {
    method: "POST",
  });
}

export async function fetchStoreItems(): Promise<StoreItem[]> {
  return authFetch<StoreItem[]>(API_ENDPOINTS.store);
}

export async function purchaseStoreItem(slug: string, clientToken?: string): Promise<PurchaseResult> {
  return authFetch<PurchaseResult>(
    apiPath.storePurchaseBySlug(slug),
    jsonInit("POST", { client_token: clientToken ?? null }),
  );
}

export async function completeLesson(slug: string): Promise<LessonCompletionResult> {
  return authFetch<LessonCompletionResult>(apiPath.lessonCompleteBySlug(slug), {
    method: "POST",
  });
}

export async function createCheckoutSession(tier: string): Promise<CheckoutSessionResult> {
  return authFetch<CheckoutSessionResult>(API_ENDPOINTS.billingCheckoutSession, jsonInit("POST", { tier }));
}

export async function createBillingPortalSession(): Promise<{ url: string }> {
  return authFetch<{ url: string }>(API_ENDPOINTS.billingPortal, jsonInit("POST", {}));
}

export async function fetchSavedPrompts(): Promise<PromptListItem[]> {
  return authFetch<PromptListItem[]>(API_ENDPOINTS.usersSavedPrompts);
}

export async function fetchMySubmissions(): Promise<AuthorSubmission[]> {
  return authFetch<AuthorSubmission[]>(API_ENDPOINTS.usersSubmissions);
}

export async function fetchTopContributors(limit = 12): Promise<ContributorTopItem[]> {
  return optionalAuthJsonFetch<ContributorTopItem[]>(withQuery(API_ENDPOINTS.contributorsTop, { limit }));
}

export async function fetchPromptRecommendations(params?: {
  context?: PromptRecommendationContext;
  limit?: number;
  prompt_slug?: string | null;
  lesson_slug?: string | null;
}): Promise<PromptRecommendationResponse> {
  return authFetch<PromptRecommendationResponse>(withQuery(API_ENDPOINTS.promptRecommendations, {
    context: params?.context,
    limit: params?.limit,
    prompt_slug: params?.prompt_slug,
    lesson_slug: params?.lesson_slug,
  }));
}

export async function fetchContributorProfile(slug: string): Promise<ContributorProfile> {
  return optionalAuthJsonFetch<ContributorProfile>(
    apiPath.contributorBySlug(slug),
  );
}

export async function buyPromptWithLumens(
  promptId: string,
  clientToken?: string,
): Promise<{ purchase: PromptMarketplacePurchase }> {
  return authFetch<{ purchase: PromptMarketplacePurchase }>(
    apiPath.marketplacePromptBuyWithLumens(promptId),
    jsonInit("POST", { client_token: clientToken ?? null }),
  );
}

export async function createPromptCheckoutSession(
  promptId: string,
  clientToken?: string,
  urls?: { success_url?: string; cancel_url?: string },
): Promise<CheckoutSessionResult & { purchase_id: string }> {
  return authFetch<CheckoutSessionResult & { purchase_id: string }>(
    API_ENDPOINTS.marketplacePromptCheckoutSession,
    jsonInit("POST", {
      prompt_id: promptId,
      client_token: clientToken ?? null,
      success_url: urls?.success_url ?? null,
      cancel_url: urls?.cancel_url ?? null,
    }),
  );
}

export async function upsertPromptReview(
  promptId: string,
  body: { rating: number; text?: string | null },
): Promise<PromptReview> {
  return authFetch<PromptReview>(
    apiPath.marketplacePromptReview(promptId),
    jsonInit("PUT", body),
  );
}

export async function savePrompt(promptId: string): Promise<EconomyAction> {
  return authFetch<EconomyAction>(apiPath.userSavedPromptById(promptId), {
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
  price_rub?: number | null;
}): Promise<{ id: string; slug: string; status: string; moderation_state: string; auto_approved?: boolean }> {
  return authFetch(API_ENDPOINTS.contributionsSubmit, jsonInit("POST", body));
}

export async function unsavePrompt(promptId: string): Promise<void> {
  return authFetchNoContent(apiPath.userSavedPromptById(promptId), {
    method: "DELETE",
  });
}

export async function trackPromptCopy(promptId: string): Promise<PromptActionResult> {
  return authFetch<PromptActionResult>(apiPath.promptEventCopy(promptId), {
    method: "POST",
  });
}

export async function trackPromptApply(promptId: string): Promise<PromptActionResult> {
  return authFetch<PromptActionResult>(apiPath.promptEventApply(promptId), {
    method: "POST",
  });
}

export async function submitLearningStep(
  courseSlug: string,
  lessonSlug: string,
  stepSlug: string,
  answer: Record<string, unknown> | null,
): Promise<LearningStepSubmitResponse> {
  return authFetch<LearningStepSubmitResponse>(
    apiPath.learningStepSubmit(courseSlug, lessonSlug, stepSlug),
    jsonInit("POST", { answer }),
  );
}

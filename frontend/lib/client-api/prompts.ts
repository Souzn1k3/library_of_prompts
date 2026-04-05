import { API_ENDPOINTS, apiPath } from "../constants/api";
import { withQuery } from "../http";
import { getClientLanguage } from "../i18n";
import { localizePromptTextList } from "../prompt-localization";
import type {
  AuthorSubmission,
  EconomyAction,
  PromptActionResult,
  PromptListItem,
  PromptRecommendationContext,
  PromptRecommendationResponse,
} from "../types";
import { authFetch, authFetchNoContent, jsonInit, optionalAuthJsonFetch } from "./transport";

export async function fetchSavedPrompts(): Promise<PromptListItem[]> {
  const prompts = await authFetch<PromptListItem[]>(API_ENDPOINTS.usersSavedPrompts);
  return localizePromptTextList(prompts, getClientLanguage());
}

export async function fetchMySubmissions(): Promise<AuthorSubmission[]> {
  return authFetch<AuthorSubmission[]>(API_ENDPOINTS.usersSubmissions);
}

export async function fetchPromptRecommendations(params?: {
  context?: PromptRecommendationContext;
  limit?: number;
  prompt_slug?: string | null;
  lesson_slug?: string | null;
}): Promise<PromptRecommendationResponse> {
  const response = await authFetch<PromptRecommendationResponse>(withQuery(API_ENDPOINTS.promptRecommendations, {
    context: params?.context,
    limit: params?.limit,
    prompt_slug: params?.prompt_slug,
    lesson_slug: params?.lesson_slug,
  }));
  return {
    ...response,
    items: localizePromptTextList(response.items, getClientLanguage()),
  };
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
  return optionalAuthJsonFetch<PromptActionResult>(apiPath.promptEventCopy(promptId), {
    method: "POST",
  });
}

export async function trackPromptApply(promptId: string): Promise<PromptActionResult> {
  return optionalAuthJsonFetch<PromptActionResult>(apiPath.promptEventApply(promptId), {
    method: "POST",
  });
}

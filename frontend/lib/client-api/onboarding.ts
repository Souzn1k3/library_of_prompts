import { API_ENDPOINTS } from "../constants/api";
import { getClientLanguage } from "../i18n";
import { localizePromptSummary, localizePromptTitle } from "../prompt-localization";
import type {
  OnboardingFirstWinResult,
  OnboardingGoal,
  OnboardingProfile,
  OnboardingRole,
  OnboardingStarterPack,
} from "../types";
import { authFetch, jsonInit } from "./transport";

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
  const language = getClientLanguage();
  const pack = await authFetch<OnboardingStarterPack>(API_ENDPOINTS.onboardingStarterPack);
  return {
    ...pack,
    prompts: pack.prompts.map((prompt) => ({
      ...prompt,
      title: localizePromptTitle(prompt.slug, prompt.title, language),
      summary: localizePromptSummary(prompt.slug, prompt.summary, language),
    })),
    action: pack.action
      ? {
        ...pack.action,
        prompt_title: localizePromptTitle(pack.action.prompt_slug, pack.action.prompt_title, language),
      }
      : null,
  };
}

export async function completeOnboardingFirstWin(body: {
  prompt_id: string;
  action: string;
}): Promise<OnboardingFirstWinResult> {
  return authFetch<OnboardingFirstWinResult>(API_ENDPOINTS.onboardingFirstWin, jsonInit("POST", body));
}

"use client";

import { ApiRequestError } from "@/lib/api";
import { fetchOnboardingProfile, fetchOnboardingStarterPack } from "@/lib/client-api";
import type { TranslationKey } from "@/lib/i18n";
import type { OnboardingProfile, OnboardingStarterPack } from "@/lib/types";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

export type OnboardingWizardBootstrap = {
  profile: OnboardingProfile;
  starter: OnboardingStarterPack;
  firstWinDone: boolean;
};

export async function loadOnboardingWizardBootstrap(): Promise<OnboardingWizardBootstrap> {
  const [profile, starter] = await Promise.all([
    fetchOnboardingProfile(),
    fetchOnboardingStarterPack(),
  ]);
  return {
    profile,
    starter,
    firstWinDone: Boolean(profile.first_win_completed_at),
  };
}

export function mapOnboardingLoadError(error: unknown, t: Translate): string | null {
  if (error instanceof ApiRequestError && error.status === 401) {
    return null;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return t("api.requestFailed");
}

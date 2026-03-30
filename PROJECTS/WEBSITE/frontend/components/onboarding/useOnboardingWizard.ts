"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { ApiRequestError } from "@/lib/api";
import {
  completeOnboardingFirstWin,
  fetchOnboardingProfile,
  fetchOnboardingStarterPack,
  skipOnboarding,
  updateOnboardingProfile,
} from "@/lib/client-api";
import { trackEvent } from "@/lib/analytics";
import type {
  OnboardingGoal,
  OnboardingProfile,
  OnboardingRole,
  OnboardingStarterPack,
} from "@/lib/types";

import { getContextOptions, getGoalOptions, getRoleOptions } from "./options";

export function useOnboardingWizard(status: AuthStatus) {
  const { t, language } = useI18n();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<OnboardingProfile | null>(null);
  const [starter, setStarter] = useState<OnboardingStarterPack | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [step, setStep] = useState(0);
  const [role, setRole] = useState<OnboardingRole | null>(null);
  const [goal, setGoal] = useState<OnboardingGoal | null>(null);
  const [aiContext, setAiContext] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [skipPending, setSkipPending] = useState(false);
  const [firstWinDone, setFirstWinDone] = useState(false);
  const [firstWinPending, setFirstWinPending] = useState(false);

  const roleOptions = useMemo(() => getRoleOptions(t), [t]);
  const goalOptions = useMemo(() => getGoalOptions(t), [t]);
  const contextOptions = useMemo(() => getContextOptions(t), [t]);

  useEffect(() => {
    if (status !== "authenticated") {
      setLoading(false);
      setLoadError(null);
      setProfile(null);
      setStarter(null);
      return;
    }

    setLoading(true);
    setLoadError(null);
    Promise.all([fetchOnboardingProfile(), fetchOnboardingStarterPack()])
      .then(([profileData, starterPack]) => {
        setProfile(profileData);
        setRole(profileData.role);
        setGoal(profileData.goal);
        setAiContext(profileData.ai_context);
        setStarter(starterPack);
        setFirstWinDone(Boolean(profileData.first_win_completed_at));
        setLoadError(null);
        setLoading(false);
      })
      .catch((e) => {
        if (e instanceof ApiRequestError && e.status === 401) {
          setLoading(false);
          return;
        }
        setLoadError(e instanceof Error ? e.message : t("api.requestFailed"));
        setLoading(false);
      });
  }, [language, loadAttempt, status, t]);

  useEffect(() => {
    if (!profile?.needs_onboarding) return;
    trackEvent({
      eventName: "onboarding_started",
      page: "/onboarding",
      feature: "onboarding_wizard",
      onceKey: "onboarding_started",
      metadata: {
        has_profile: Boolean(profile),
      },
    });
  }, [profile]);

  const progress = useMemo(() => Math.min(3, step + 1), [step]);

  async function completeOnboardingFlow() {
    if (!role || !goal || !aiContext) {
      setError(t("onboardingWizard.selectAllSteps"));
      return;
    }
    setError(null);
    setPending(true);
    try {
      const profileData = await updateOnboardingProfile({ role, goal, ai_context: aiContext });
      const starterPack = await fetchOnboardingStarterPack();
      setProfile(profileData);
      setStarter(starterPack);
      setStep(3);
      trackEvent({
        eventName: "onboarding_completed",
        page: "/onboarding",
        feature: "onboarding_wizard",
        onceKey: "onboarding_completed",
        metadata: {
          role,
          goal,
          ai_context: aiContext,
        },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : t("onboardingWizard.saveFailed"));
    } finally {
      setPending(false);
    }
  }

  async function skipFlow() {
    setSkipPending(true);
    try {
      await skipOnboarding();
      router.push("/dashboard");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("onboardingWizard.skipFailed"));
    } finally {
      setSkipPending(false);
    }
  }

  async function completeFirstWin() {
    if (!starter?.action) return;
    setFirstWinPending(true);
    setError(null);
    try {
      await navigator.clipboard.writeText(starter.action.prompt_body);
      const profileData = await completeOnboardingFirstWin({
        prompt_id: starter.action.prompt_id,
        action: "copy_prompt",
      });
      setProfile(profileData);
      setFirstWinDone(true);
      trackEvent({
        eventName: "onboarding_first_action",
        page: "/onboarding",
        feature: "first_win",
        onceKey: `onboarding_first_action:${starter.action.prompt_id}`,
        metadata: {
          prompt_id: starter.action.prompt_id,
          action: "copy_prompt",
        },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : t("onboardingWizard.firstWinFailed"));
    } finally {
      setFirstWinPending(false);
    }
  }

  return {
    loading,
    profile,
    starter,
    error,
    loadError,
    step,
    role,
    goal,
    aiContext,
    pending,
    skipPending,
    firstWinDone,
    firstWinPending,
    roleOptions,
    goalOptions,
    contextOptions,
    progress,
    needsWizard: profile?.needs_onboarding ?? true,
    retryLoad: () => setLoadAttempt((value) => value + 1),
    selectRole: (value: OnboardingRole) => setRole(value),
    selectGoal: (value: OnboardingGoal) => setGoal(value),
    selectAiContext: (value: string) => setAiContext(value),
    goBack: () => setStep((value) => Math.max(0, value - 1)),
    goNext: () => setStep((value) => Math.min(2, value + 1)),
    completeOnboardingFlow,
    skipFlow,
    completeFirstWin,
  };
}

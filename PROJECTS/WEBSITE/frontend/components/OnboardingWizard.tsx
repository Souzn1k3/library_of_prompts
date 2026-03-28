"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
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

export function OnboardingWizard() {
  const { status } = useAuth();
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

  const roleOptions = useMemo(
    () => [
      {
        value: "student",
        label: t("onboardingWizard.roleStudentLabel"),
        hint: t("onboardingWizard.roleStudentHint"),
      },
      {
        value: "developer",
        label: t("onboardingWizard.roleDeveloperLabel"),
        hint: t("onboardingWizard.roleDeveloperHint"),
      },
      {
        value: "other",
        label: t("onboardingWizard.roleOtherLabel"),
        hint: t("onboardingWizard.roleOtherHint"),
      },
    ],
    [t],
  );

  const goalOptions = useMemo(
    () => [
      {
        value: "learning",
        label: t("onboardingWizard.goalLearningLabel"),
        hint: t("onboardingWizard.goalLearningHint"),
      },
      {
        value: "solving_tasks",
        label: t("onboardingWizard.goalSolvingLabel"),
        hint: t("onboardingWizard.goalSolvingHint"),
      },
      {
        value: "productivity",
        label: t("onboardingWizard.goalProductivityLabel"),
        hint: t("onboardingWizard.goalProductivityHint"),
      },
    ],
    [t],
  );

  const contextOptions = useMemo(
    () => [
      {
        value: "chatgpt",
        label: t("onboardingWizard.contextGeneralLabel"),
        hint: t("onboardingWizard.contextGeneralHint"),
      },
      {
        value: "code_assistant",
        label: t("onboardingWizard.contextCodeLabel"),
        hint: t("onboardingWizard.contextCodeHint"),
      },
      {
        value: "school",
        label: t("onboardingWizard.contextSchoolLabel"),
        hint: t("onboardingWizard.contextSchoolHint"),
      },
      {
        value: "work",
        label: t("onboardingWizard.contextWorkLabel"),
        hint: t("onboardingWizard.contextWorkHint"),
      },
    ],
    [t],
  );

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

  if (status === "loading") {
    return <p className="text-sm text-zinc-500">{t("onboardingWizard.loading")}</p>;
  }

  if (status === "unauthenticated") {
    return (
      <p className="text-sm text-zinc-600">
        {t("onboardingWizard.signInPrefix")}{" "}
        <Link href="/login" className="font-medium text-zinc-900 underline">
          {t("onboardingWizard.signInLink")}
        </Link>{" "}
        {t("onboardingWizard.signInSuffix")}
      </p>
    );
  }

  if (loading) {
    return <p className="text-sm text-zinc-500">{t("onboardingWizard.loading")}</p>;
  }

  if (loadError) {
    return (
      <div className="space-y-3 rounded-[1.5rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p>{loadError}</p>
        <button
          type="button"
          onClick={() => setLoadAttempt((value) => value + 1)}
          className="rounded-full border border-amber-300 bg-white px-3 py-1.5 text-xs font-semibold text-amber-900 transition hover:border-amber-400"
        >
          {t("dashboard.retry")}
        </button>
      </div>
    );
  }

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

  const needsWizard = profile?.needs_onboarding ?? true;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
          {t("onboardingWizard.activationSetup")}{" "}
          {needsWizard ? t("onboardingWizard.stepCounter", { step: progress }) : ""}
        </p>
        <button
          type="button"
          onClick={skipFlow}
          disabled={skipPending}
          className="text-sm text-zinc-600 underline disabled:opacity-60"
        >
          {skipPending ? t("onboardingWizard.skipping") : t("onboardingWizard.skipForNow")}
        </button>
      </div>

      {needsWizard && step < 3 ? (
        <div className="pv-panel space-y-4 px-5 py-5">
          {step === 0 ? (
            <OptionStep
              title={t("onboardingWizard.stepRoleTitle")}
              subtitle={t("onboardingWizard.stepRoleSubtitle")}
              options={roleOptions}
              selected={role}
              onSelect={(value) => setRole(value as OnboardingRole)}
            />
          ) : null}
          {step === 1 ? (
            <OptionStep
              title={t("onboardingWizard.stepGoalTitle")}
              subtitle={t("onboardingWizard.stepGoalSubtitle")}
              options={goalOptions}
              selected={goal}
              onSelect={(value) => setGoal(value as OnboardingGoal)}
            />
          ) : null}
          {step === 2 ? (
            <OptionStep
              title={t("onboardingWizard.stepContextTitle")}
              subtitle={t("onboardingWizard.stepContextSubtitle")}
              options={contextOptions}
              selected={aiContext}
              onSelect={setAiContext}
            />
          ) : null}

          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={() => setStep((v) => Math.max(0, v - 1))}
              disabled={step === 0 || pending}
              className="pv-button-secondary disabled:opacity-50"
            >
              {t("onboardingWizard.back")}
            </button>
            {step < 2 ? (
              <button
                type="button"
                onClick={() => setStep((v) => Math.min(2, v + 1))}
                disabled={
                  pending ||
                  (step === 0 && !role) ||
                  (step === 1 && !goal)
                }
                className="pv-button-primary disabled:opacity-60"
              >
                {t("onboardingWizard.continue")}
              </button>
            ) : (
              <button
                type="button"
                onClick={completeOnboardingFlow}
                disabled={pending || !aiContext}
                className="pv-button-primary disabled:opacity-60"
              >
                {pending ? t("onboardingWizard.preparing") : t("onboardingWizard.finishSetup")}
              </button>
            )}
          </div>
        </div>
      ) : null}

      {!needsWizard || step >= 3 ? (
        <div className="space-y-5">
          <div className="rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
            {t("onboardingWizard.readyBody")}
          </div>

          {starter?.action ? (
            <section className="pv-panel space-y-3 px-5 py-5">
              <h2 className="text-lg font-semibold text-zinc-900">{t("onboardingWizard.firstWinTitle")}</h2>
              <p className="text-sm text-zinc-600">{starter.action.instruction}</p>
              <div className="rounded-[1.25rem] border border-zinc-200 bg-zinc-50/90 p-3">
                <p className="text-sm font-medium text-zinc-900">{starter.action.prompt_title}</p>
                <pre className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap text-xs text-zinc-700">
                  {starter.action.prompt_body}
                </pre>
              </div>
              {!firstWinDone ? (
                <button
                  type="button"
                  onClick={completeFirstWin}
                  disabled={firstWinPending}
                  className="pv-button-primary disabled:opacity-60"
                >
                  {firstWinPending ? t("onboardingWizard.completing") : t("onboardingWizard.completeFirstWin")}
                </button>
              ) : (
                <div className="rounded-[1.25rem] border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
                  {t("onboardingWizard.firstWinDone")}
                </div>
              )}
              <Link
                href={`/prompt/${encodeURIComponent(starter.action.prompt_slug)}`}
                className="inline-block text-sm font-medium text-zinc-900 underline"
              >
                {t("onboardingWizard.openPromptPage")}
              </Link>
            </section>
          ) : null}

          <section className="pv-panel space-y-3 px-5 py-5">
            <h2 className="text-lg font-semibold text-zinc-900">{t("onboardingWizard.recommendedPromptsTitle")}</h2>
            {starter?.prompts?.length ? (
              <ul className="space-y-2">
                {starter.prompts.slice(0, 5).map((prompt) => (
                  <li key={prompt.id}>
                    <Link
                      href={`/prompt/${encodeURIComponent(prompt.slug)}`}
                      className="block rounded-[1.25rem] border border-zinc-200 bg-zinc-50/90 px-3 py-3 transition hover:border-zinc-300"
                    >
                      <p className="text-sm font-medium text-zinc-900">{prompt.title}</p>
                      {prompt.summary ? <p className="text-xs text-zinc-600">{prompt.summary}</p> : null}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-zinc-500">{t("onboardingWizard.noPromptRecommendations")}</p>
            )}
          </section>

          <section className="pv-panel px-5 py-5">
            <h2 className="text-lg font-semibold text-zinc-900">{t("onboardingWizard.recommendedLessonTitle")}</h2>
            {starter?.lesson ? (
              <div className="mt-2 space-y-1">
                <Link
                  href={`/learn/${encodeURIComponent(starter.lesson.slug)}`}
                  className="text-sm font-medium text-zinc-900 underline"
                >
                  {starter.lesson.title}
                </Link>
                <p className="text-xs text-zinc-600">
                  {t("onboardingWizard.minimumTier")}: {starter.lesson.min_tier}
                  {starter.lesson.locked
                    ? ` · ${t("onboardingWizard.currentlyLocked")}`
                    : ` · ${t("onboardingWizard.availableNow")}`}
                </p>
              </div>
            ) : (
              <p className="mt-2 text-sm text-zinc-500">{t("onboardingWizard.noLesson")}</p>
            )}
          </section>

          <div className="flex flex-wrap gap-3">
            <Link
              href="/dashboard"
              className="pv-button-primary"
            >
              {t("onboardingWizard.goDashboard")}
            </Link>
            <Link
              href="/catalog"
              className="pv-button-secondary"
            >
              {t("onboardingWizard.browseCatalog")}
            </Link>
          </div>
        </div>
      ) : null}

      {error ? (
        <div className="rounded-[1.25rem] border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </div>
      ) : null}
    </div>
  );
}

function OptionStep({
  title,
  subtitle,
  options,
  selected,
  onSelect,
}: {
  title: string;
  subtitle: string;
  options: Array<{ value: string; label: string; hint: string }>;
  selected: string | null;
  onSelect: (value: string) => void;
}) {
  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold text-zinc-900">{title}</h2>
        <p className="text-sm text-zinc-600">{subtitle}</p>
      </div>
      <div className="grid gap-2">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onSelect(option.value)}
            className={`rounded-[1.25rem] border px-3 py-3 text-left transition ${
              selected === option.value
                ? "border-[var(--pv-brand)] bg-[var(--pv-brand)] text-white"
                : "border-zinc-200 bg-white text-zinc-900 hover:border-zinc-400"
            }`}
          >
            <p className="text-sm font-medium">{option.label}</p>
            <p className={`text-xs ${selected === option.value ? "text-zinc-200" : "text-zinc-600"}`}>
              {option.hint}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import type { OnboardingOption } from "@/components/onboarding/options";
import type {
  OnboardingGoal,
  OnboardingRole,
  OnboardingStarterPack,
} from "@/lib/types";

type OnboardingWizardViewProps = {
  status: AuthStatus;
  loading: boolean;
  starter: OnboardingStarterPack | null;
  error: string | null;
  loadError: string | null;
  step: number;
  role: OnboardingRole | null;
  goal: OnboardingGoal | null;
  aiContext: string | null;
  pending: boolean;
  skipPending: boolean;
  firstWinDone: boolean;
  firstWinPending: boolean;
  roleOptions: OnboardingOption<OnboardingRole>[];
  goalOptions: OnboardingOption<OnboardingGoal>[];
  contextOptions: OnboardingOption[];
  progress: number;
  needsWizard: boolean;
  retryLoad: () => void;
  selectRole: (value: OnboardingRole) => void;
  selectGoal: (value: OnboardingGoal) => void;
  selectAiContext: (value: string) => void;
  goBack: () => void;
  goNext: () => void;
  completeOnboardingFlow: () => Promise<void>;
  skipFlow: () => Promise<void>;
  completeFirstWin: () => Promise<void>;
};

export function OnboardingWizardView({
  status,
  loading,
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
  needsWizard,
  retryLoad,
  selectRole,
  selectGoal,
  selectAiContext,
  goBack,
  goNext,
  completeOnboardingFlow,
  skipFlow,
  completeFirstWin,
}: OnboardingWizardViewProps) {
  const { t } = useI18n();

  if (status === "loading") {
    return <p className="text-sm text-zinc-500">{t("onboardingWizard.loading")}</p>;
  }

  if (status === "unauthenticated") {
    return (
      <div className="pv-empty-state text-sm text-zinc-600">
        {t("onboardingWizard.signInPrefix")}{" "}
        <Link href="/login" className="font-medium text-zinc-900 underline">
          {t("onboardingWizard.signInLink")}
        </Link>{" "}
        {t("onboardingWizard.signInSuffix")}
      </div>
    );
  }

  if (loading) {
    return <p className="text-sm text-zinc-500">{t("onboardingWizard.loading")}</p>;
  }

  if (loadError) {
    return (
      <div className="pv-alert pv-alert-warning space-y-3">
        <p>{loadError}</p>
        <button type="button" onClick={retryLoad} className="pv-button-secondary !w-auto">
          {t("dashboard.retry")}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            {t("onboardingWizard.activationSetup")}{" "}
            {needsWizard ? t("onboardingWizard.stepCounter", { step: progress }) : ""}
          </p>
          {needsWizard ? (
            <div className="flex gap-2">
              {Array.from({ length: 3 }).map((_, index) => (
                <span
                  key={`step-${index + 1}`}
                  className={`h-2 rounded-full transition-all ${
                    index < progress ? "w-10 bg-[var(--pv-brand)]" : "w-6 bg-slate-200"
                  }`}
                />
              ))}
            </div>
          ) : null}
        </div>
        <button
          type="button"
          onClick={skipFlow}
          disabled={skipPending}
          className="pv-button-ghost !w-auto px-0 py-0 text-sm text-zinc-600 disabled:opacity-60"
        >
          {skipPending ? t("onboardingWizard.skipping") : t("onboardingWizard.skipForNow")}
        </button>
      </div>

      {needsWizard && step < 3 ? (
        <div className="pv-hero space-y-5 px-5 py-5 sm:px-6">
          {step === 0 ? (
            <OptionStep
              title={t("onboardingWizard.stepRoleTitle")}
              subtitle={t("onboardingWizard.stepRoleSubtitle")}
              options={roleOptions}
              selected={role}
              onSelect={(value) => selectRole(value as OnboardingRole)}
            />
          ) : null}
          {step === 1 ? (
            <OptionStep
              title={t("onboardingWizard.stepGoalTitle")}
              subtitle={t("onboardingWizard.stepGoalSubtitle")}
              options={goalOptions}
              selected={goal}
              onSelect={(value) => selectGoal(value as OnboardingGoal)}
            />
          ) : null}
          {step === 2 ? (
            <OptionStep
              title={t("onboardingWizard.stepContextTitle")}
              subtitle={t("onboardingWizard.stepContextSubtitle")}
              options={contextOptions}
              selected={aiContext}
              onSelect={selectAiContext}
            />
          ) : null}

          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <button
              type="button"
              onClick={goBack}
              disabled={step === 0 || pending}
              className="pv-button-secondary disabled:opacity-50"
            >
              {t("onboardingWizard.back")}
            </button>
            {step < 2 ? (
              <button
                type="button"
                onClick={goNext}
                disabled={pending || (step === 0 && !role) || (step === 1 && !goal)}
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
          <div className="pv-alert pv-alert-success">{t("onboardingWizard.readyBody")}</div>

          {starter?.action ? (
            <section className="pv-hero space-y-4 px-5 py-5 sm:px-6">
              <div className="space-y-2">
                <p className="pv-kicker">{t("onboardingWizard.firstWinTitle")}</p>
                <h2 className="text-2xl font-semibold tracking-[-0.04em] text-zinc-900">
                  {starter.action.prompt_title}
                </h2>
                <p className="text-sm text-zinc-600">{starter.action.instruction}</p>
              </div>
              <div className="rounded-[1.25rem] border border-zinc-200 bg-white/85 p-3">
                <pre className="max-h-56 overflow-auto whitespace-pre-wrap text-xs text-zinc-700">
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
                  {firstWinPending
                    ? t("onboardingWizard.completing")
                    : t("onboardingWizard.completeFirstWin")}
                </button>
              ) : (
                <div className="pv-alert pv-alert-success">{t("onboardingWizard.firstWinDone")}</div>
              )}
              <Link
                href={`/prompt/${encodeURIComponent(starter.action.prompt_slug)}`}
                className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]"
              >
                {t("onboardingWizard.openPromptPage")}
                <span aria-hidden="true">↗</span>
              </Link>
            </section>
          ) : null}

          <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
            <section className="pv-panel space-y-3 px-5 py-5">
              <h2 className="text-lg font-semibold text-zinc-900">
                {t("onboardingWizard.recommendedPromptsTitle")}
              </h2>
              {starter?.prompts?.length ? (
                <ul className="space-y-2">
                  {starter.prompts.slice(0, 5).map((prompt) => (
                    <li key={prompt.id}>
                      <Link
                        href={`/prompt/${encodeURIComponent(prompt.slug)}`}
                        className="block rounded-[1.25rem] border border-zinc-200 bg-zinc-50/90 px-3 py-3 transition hover:border-zinc-300"
                      >
                        <p className="text-sm font-medium text-zinc-900">{prompt.title}</p>
                        {prompt.summary ? (
                          <p className="text-xs text-zinc-600">{prompt.summary}</p>
                        ) : null}
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-zinc-500">{t("onboardingWizard.noPromptRecommendations")}</p>
              )}
            </section>

            <section className="pv-panel px-5 py-5">
              <h2 className="text-lg font-semibold text-zinc-900">
                {t("onboardingWizard.recommendedLessonTitle")}
              </h2>
              {starter?.lesson ? (
                <div className="mt-3 space-y-2">
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
          </div>

          <div className="flex flex-wrap gap-3">
            <Link href="/dashboard" className="pv-button-primary">
              {t("onboardingWizard.goDashboard")}
            </Link>
            <Link href="/catalog" className="pv-button-secondary">
              {t("onboardingWizard.browseCatalog")}
            </Link>
          </div>
        </div>
      ) : null}

      {error ? <div className="pv-alert pv-alert-error">{error}</div> : null}
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
        <h2 className="text-xl font-semibold tracking-[-0.03em] text-zinc-900">{title}</h2>
        <p className="text-sm leading-relaxed text-zinc-600">{subtitle}</p>
      </div>
      <div className="grid gap-2">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onSelect(option.value)}
            className={`rounded-[1.25rem] border px-4 py-4 text-left transition ${
              selected === option.value
                ? "border-[var(--pv-brand)] bg-[linear-gradient(135deg,var(--pv-brand),#4d7dff)] text-white shadow-[0_18px_34px_rgba(37,92,255,0.2)]"
                : "border-zinc-200 bg-white text-zinc-900 hover:-translate-y-0.5 hover:border-[var(--pv-border-strong)]"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{option.label}</p>
                <p
                  className={`mt-1 text-xs leading-relaxed ${
                    selected === option.value ? "text-zinc-200" : "text-zinc-600"
                  }`}
                >
                  {option.hint}
                </p>
              </div>
              <span
                className={`mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] ${
                  selected === option.value
                    ? "border-white/60 bg-white/15 text-white"
                    : "border-zinc-300 text-zinc-400"
                }`}
              >
                {selected === option.value ? "✓" : ""}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

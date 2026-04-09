"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { EconomyActionBanner } from "@/components/ui/EconomyActionBanner";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import type { EconomyAction, OnboardingStarterPack } from "@/lib/types";

type OnboardingWizardReadySectionProps = {
  starter: OnboardingStarterPack | null;
  firstWinDone: boolean;
  firstWinPending: boolean;
  firstWinEconomy: EconomyAction | null;
  completeFirstWin: () => Promise<void>;
};

export function OnboardingWizardReadySection({
  starter,
  firstWinDone,
  firstWinPending,
  firstWinEconomy,
  completeFirstWin,
}: OnboardingWizardReadySectionProps) {
  const { t } = useI18n();

  return (
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
              onClick={() => void completeFirstWin()}
              disabled={firstWinPending}
              className="pv-button-primary disabled:opacity-60"
            >
              {firstWinPending
                ? t("onboardingWizard.completing")
                : t("onboardingWizard.completeFirstWin")}
            </button>
          ) : (
            <div className="space-y-3">
              <div className="pv-alert pv-alert-success">{t("onboardingWizard.firstWinDone")}</div>
              <EconomyActionBanner summary={firstWinEconomy} />
            </div>
          )}
          <Link
            href={appRoute.promptBySlug(starter.action.prompt_slug)}
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
                    href={appRoute.promptBySlug(prompt.slug)}
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
          <h2 className="text-lg font-semibold text-zinc-900">
            {t("onboardingWizard.recommendedLessonTitle")}
          </h2>
          {starter?.lesson ? (
            <div className="mt-3 space-y-2">
              <Link href={appRoute.learnBySlug(starter.lesson.slug)} className="text-sm font-medium text-zinc-900 underline">
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
        <Link href={APP_ROUTES.dashboard} className="pv-button-primary">
          {t("onboardingWizard.goDashboard")}
        </Link>
        <Link href={APP_ROUTES.catalog} className="pv-button-secondary">
          {t("onboardingWizard.browseCatalog")}
        </Link>
      </div>
    </div>
  );
}

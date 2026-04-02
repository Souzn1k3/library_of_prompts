"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import type { MissionPresentation } from "@/lib/missionPresentation";
import type { WalletRead } from "@/lib/types";

type HeroAction = {
  href: string;
  label: string;
};

type DashboardMissionHeroProps = {
  currentMission: MissionPresentation | null;
  needsOnboarding: boolean;
  primaryAction: HeroAction;
  savedPromptsCount: number;
  savedPromptsPreviewTitle: string | null;
  submissionCount: number;
  latestSubmissionTitle: string | null;
  wallet: WalletRead | null;
  balanceDelta: number | null;
};

export function DashboardMissionHero({
  currentMission,
  needsOnboarding,
  primaryAction,
  savedPromptsCount,
  savedPromptsPreviewTitle,
  submissionCount,
  latestSubmissionTitle,
  wallet,
  balanceDelta,
}: DashboardMissionHeroProps) {
  const { t } = useI18n();
  const cardTitle = needsOnboarding
    ? t("dashboard.finishOnboardingTitle")
    : currentMission?.title ?? t("dashboard.heroNoMissionTitle");
  const savedPromptsHref = savedPromptsCount > 0 ? "/dashboard#saved" : "/catalog";
  const savedPromptsAction = savedPromptsCount > 0 ? t("dashboard.savedPrompts") : t("home.explorePrompts");
  const submissionsHref = submissionCount > 0 ? "/dashboard#submissions" : "/submit";
  const submissionsAction = submissionCount > 0 ? t("dashboard.mySubmissions") : t("dashboard.submitAnother");

  return (
    <PageIntro
      eyebrow={t("dashboard.title")}
      title={t("dashboard.title")}
      description={t("dashboard.subtitle")}
    >
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="pv-card-muted flex h-full min-h-[11.5rem] flex-col gap-4 border-[rgba(37,92,255,0.12)] bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(239,244,255,0.92))] p-4 shadow-[0_16px_36px_rgba(37,92,255,0.06)] sm:p-5">
          <h2 className="line-clamp-3 text-lg font-bold tracking-[-0.03em] text-zinc-950 sm:text-xl">
            {cardTitle}
          </h2>

          <div className="mt-auto border-t border-[rgba(15,23,42,0.08)] pt-3">
            <Link href={primaryAction.href} className="pv-inline-link flex w-full justify-between">
              {primaryAction.label}
              <span aria-hidden="true">↗</span>
            </Link>
          </div>
        </div>

        <DashboardMetricCard
          eyebrow={t("dashboard.savedPrompts")}
          value={savedPromptsCount}
          body={savedPromptsPreviewTitle ?? t("home.explorePrompts")}
          href={savedPromptsHref}
          actionLabel={savedPromptsAction}
        />

        <DashboardMetricCard
          eyebrow={t("nav.wallet")}
          value={
            typeof wallet?.balance === "number"
              ? `${wallet.balance} ${wallet.currency_symbol ?? "LMN"}`
              : `— ${wallet?.currency_symbol ?? "LMN"}`
          }
          body={
            balanceDelta && balanceDelta !== 0
              ? `${balanceDelta > 0 ? "+" : ""}${balanceDelta} ${wallet?.currency_symbol ?? "LMN"}`
              : t("dashboard.walletSummaryBody")
          }
          href="/wallet"
          actionLabel={t("dashboard.openWallet")}
        />

        <DashboardMetricCard
          eyebrow={t("dashboard.mySubmissions")}
          value={submissionCount}
          body={latestSubmissionTitle ?? t("dashboard.submitAnother")}
          href={submissionsHref}
          actionLabel={submissionsAction}
        />
      </div>
    </PageIntro>
  );
}

function DashboardMetricCard({
  eyebrow,
  value,
  body,
  href,
  actionLabel,
}: {
  eyebrow: string;
  value: number | string;
  body: string;
  href: string;
  actionLabel: string;
}) {
  return (
    <div className="pv-card-muted flex h-full min-h-[11.5rem] flex-col gap-3 p-4 sm:p-5">
      <p className="pv-kicker">{eyebrow}</p>
      <div className="space-y-2">
        <p className="text-[clamp(2.1rem,4.2vw,2.8rem)] font-extrabold tracking-[-0.08em] text-zinc-950">
          {value}
        </p>
        <p className="line-clamp-2 text-sm leading-relaxed text-zinc-600">{body}</p>
      </div>
      <div className="mt-auto border-t border-[rgba(15,23,42,0.08)] pt-3">
        <Link href={href} className="pv-inline-link flex w-full justify-between">
          {actionLabel}
          <span aria-hidden="true">↗</span>
        </Link>
      </div>
    </div>
  );
}

import { useMemo } from "react";

import { buildWorkspaceCards } from "@/components/dashboard/dashboardWorkspaceCards";
import { WorkspaceMapCard } from "@/components/dashboard/WorkspaceMapCard";
import type { TranslationKey } from "@/lib/i18n";
import type { BillingStatus, LearningMyModules, WalletRead } from "@/lib/types";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type DashboardWorkspaceSectionProps = {
  t: Translate;
  locale: string;
  savedPromptsCount: number;
  lastSavedPromptAt: string | null | undefined;
  submissionsCount: number;
  rejectedSubmissionsCount: number;
  pendingSubmissionsCount: number;
  lastSubmissionAt: string | null | undefined;
  needsOnboarding: boolean;
  learningMy: LearningMyModules | null;
  wallet: WalletRead | null;
  walletPendingAmount: number;
  billing: BillingStatus | null;
  localizedBillingStatus: string | null;
};

export function DashboardWorkspaceSection({
  t,
  locale,
  savedPromptsCount,
  lastSavedPromptAt,
  submissionsCount,
  rejectedSubmissionsCount,
  pendingSubmissionsCount,
  lastSubmissionAt,
  needsOnboarding,
  learningMy,
  wallet,
  walletPendingAmount,
  billing,
  localizedBillingStatus,
}: DashboardWorkspaceSectionProps) {
  const cards = useMemo(
    () =>
      buildWorkspaceCards({
        t,
        locale,
        savedPromptsCount,
        lastSavedPromptAt,
        submissionsCount,
        rejectedSubmissionsCount,
        pendingSubmissionsCount,
        lastSubmissionAt,
        needsOnboarding,
        learningMy,
        wallet,
        walletPendingAmount,
        billing,
        localizedBillingStatus,
      }),
    [
      t,
      locale,
      savedPromptsCount,
      lastSavedPromptAt,
      submissionsCount,
      rejectedSubmissionsCount,
      pendingSubmissionsCount,
      lastSubmissionAt,
      needsOnboarding,
      learningMy,
      wallet,
      walletPendingAmount,
      billing,
      localizedBillingStatus,
    ],
  );

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {t("dashboard.workspaceNavTitle")}
          </h2>
          <p className="mt-2 text-sm text-zinc-600">{t("dashboard.workspaceNavBody")}</p>
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {cards.map((card) => (
          <WorkspaceMapCard
            key={`${card.href}:${card.title}`}
            title={card.title}
            description={card.description}
            href={card.href}
            statusLabel={card.statusLabel}
            statusTone={card.statusTone}
            lastVisitLabel={card.lastVisitLabel}
            actionLabel={card.actionLabel}
          />
        ))}
      </div>
    </section>
  );
}

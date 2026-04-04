import { WorkspaceMapCard } from "@/components/dashboard/WorkspaceMapCard";
import { APP_ROUTES } from "@/lib/constants/routes";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import type { TranslationKey } from "@/lib/i18n";
import type { BillingStatus, LearningMyModules, WalletRead } from "@/lib/types";

import { formatVisitLabel } from "@/components/dashboard/helpers";

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
  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-copy">
        <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">
          {t("dashboard.workspaceNavTitle")}
        </h2>
        <p className="mt-2 text-sm text-zinc-600">{t("dashboard.workspaceNavBody")}</p>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <WorkspaceMapCard
          title={t("dashboard.navSectionPromptsTitle")}
          description={t("dashboard.navSectionPromptsBody")}
          href={APP_ROUTES.catalog}
          statusLabel={
            savedPromptsCount > 0
              ? t("dashboard.navStatusSavedCount", { count: savedPromptsCount })
              : t("dashboard.navStatusNew")
          }
          statusTone={savedPromptsCount > 0 ? "success" : "neutral"}
          lastVisitLabel={formatVisitLabel(lastSavedPromptAt, locale, t)}
          actionLabel={t("dashboard.navOpenSection")}
        />

        <WorkspaceMapCard
          title={t("dashboard.navSectionSubmissionsTitle")}
          description={t("dashboard.navSectionSubmissionsBody")}
          href={`${APP_ROUTES.dashboard}#submissions`}
          statusLabel={
            rejectedSubmissionsCount > 0
              ? t("dashboard.navStatusNeedsAttention", { count: rejectedSubmissionsCount })
              : pendingSubmissionsCount > 0
                ? t("dashboard.navStatusPendingReviewCount", { count: pendingSubmissionsCount })
                : submissionsCount > 0
                  ? t("dashboard.navStatusNoChanges")
                  : t("dashboard.navStatusNew")
          }
          statusTone={
            rejectedSubmissionsCount > 0 || pendingSubmissionsCount > 0
              ? "warning"
              : submissionsCount > 0
                ? "info"
                : "neutral"
          }
          lastVisitLabel={formatVisitLabel(lastSubmissionAt, locale, t)}
          actionLabel={t("dashboard.navOpenSection")}
        />

        <WorkspaceMapCard
          title={t("dashboard.navSectionLearningTitle")}
          description={t("dashboard.navSectionLearningBody")}
          href={APP_ROUTES.learnMy}
          statusLabel={
            needsOnboarding
              ? t("dashboard.navStatusOnboarding")
              : (learningMy?.active_courses.length ?? 0) > 0
                ? t("dashboard.navStatusActiveCourses", {
                    count: learningMy?.active_courses.length ?? 0,
                  })
                : (learningMy?.completed_courses.length ?? 0) > 0
                  ? t("dashboard.navStatusCompletedCourses", {
                      count: learningMy?.completed_courses.length ?? 0,
                    })
                  : t("dashboard.navStatusNew")
          }
          statusTone={
            needsOnboarding
              ? "warning"
              : (learningMy?.active_courses.length ?? 0) > 0
                ? "success"
                : "neutral"
          }
          lastVisitLabel={formatVisitLabel(
            learningMy?.active_courses[0]?.last_activity_at ?? learningMy?.completed_courses[0]?.completed_at,
            locale,
            t,
          )}
          actionLabel={t("dashboard.navOpenSection")}
        />

        <WorkspaceMapCard
          title={t("dashboard.navSectionStoreTitle")}
          description={t("dashboard.navSectionStoreBody")}
          href={APP_ROUTES.store}
          statusLabel={
            typeof wallet?.balance === "number" && wallet.balance > 0
              ? t("dashboard.navStatusBalance", {
                  count: wallet.balance,
                  symbol: TOKEN_SHORT_CODE,
                })
              : t("dashboard.navStatusNew")
          }
          statusTone={typeof wallet?.balance === "number" && wallet.balance > 0 ? "info" : "neutral"}
          lastVisitLabel={formatVisitLabel(wallet?.recent_purchases[0]?.created_at, locale, t)}
          actionLabel={t("dashboard.navOpenSection")}
        />

        <WorkspaceMapCard
          title={t("dashboard.navSectionWalletTitle")}
          description={t("dashboard.navSectionWalletBody")}
          href={APP_ROUTES.wallet}
          statusLabel={
            walletPendingAmount > 0
              ? t("dashboard.navStatusPendingBonuses", {
                  count: walletPendingAmount,
                  symbol: TOKEN_SHORT_CODE,
                })
              : typeof wallet?.balance === "number"
                ? t("dashboard.navStatusNoChanges")
                : t("dashboard.navStatusNew")
          }
          statusTone={
            walletPendingAmount > 0
              ? "warning"
              : typeof wallet?.balance === "number"
                ? "info"
                : "neutral"
          }
          lastVisitLabel={formatVisitLabel(wallet?.recent[0]?.created_at, locale, t)}
          actionLabel={t("dashboard.navOpenSection")}
        />

        <WorkspaceMapCard
          title={t("dashboard.navSectionProfileTitle")}
          description={t("dashboard.navSectionProfileBody")}
          href={APP_ROUTES.profile}
          statusLabel={
            billing?.status === "active" || billing?.status === "trialing"
              ? t("dashboard.navStatusSubscriptionActive")
              : localizedBillingStatus ?? t("dashboard.navStatusNoChanges")
          }
          statusTone={
            billing?.status === "active" || billing?.status === "trialing"
              ? "success"
              : "neutral"
          }
          lastVisitLabel={formatVisitLabel(billing?.updated_at, locale, t)}
          actionLabel={t("dashboard.navOpenSection")}
        />
      </div>
    </section>
  );
}

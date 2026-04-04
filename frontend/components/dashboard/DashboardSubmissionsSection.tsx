import Link from "next/link";

import { SubmissionStateBadge } from "@/components/dashboard/SubmissionStateBadge";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { formatDateTime } from "@/lib/formatters";
import type { TranslationKey } from "@/lib/i18n";
import type { AuthorSubmission } from "@/lib/types";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type DashboardSubmissionsSectionProps = {
  t: Translate;
  locale: string;
  submissions: AuthorSubmission[];
};

export function DashboardSubmissionsSection({
  t,
  locale,
  submissions,
}: DashboardSubmissionsSectionProps) {
  return (
    <section id="submissions" className="pv-panel pv-section-anchor px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("dashboard.mySubmissions")}</h2>
        </div>
        <Link href={APP_ROUTES.submit} className="pv-inline-link">
          {t("dashboard.submitAnother")}
          <span aria-hidden="true">↗</span>
        </Link>
      </div>
      {submissions.length === 0 ? (
        <div className="pv-empty-state mt-6 text-sm text-zinc-600">{t("dashboard.noSubmissions")}</div>
      ) : (
        <div className="mt-6 space-y-3">
          {submissions.slice(0, 4).map((submission) => (
            <div key={submission.id} className="pv-card-muted p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                {submission.moderation_state === "approved" ? (
                  <Link
                    href={appRoute.promptBySlug(submission.slug)}
                    className="text-sm font-semibold text-zinc-900 underline"
                  >
                    {submission.title}
                  </Link>
                ) : (
                  <p className="text-sm font-semibold text-zinc-900">{submission.title}</p>
                )}
                <SubmissionStateBadge state={submission.moderation_state} />
              </div>
              <p className="mt-2 text-xs text-zinc-500">
                {t("dashboard.createdAt")} {formatDateTime(submission.created_at, locale)}
              </p>
              {submission.moderation_notes ? (
                <p className="mt-2 text-sm text-zinc-600">{submission.moderation_notes}</p>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

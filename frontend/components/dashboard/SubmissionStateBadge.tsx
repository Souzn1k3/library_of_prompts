"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { AuthorSubmission } from "@/lib/types";

type SubmissionStateBadgeProps = {
  state: AuthorSubmission["moderation_state"];
};

export function SubmissionStateBadge({ state }: SubmissionStateBadgeProps) {
  const { t } = useI18n();
  if (state === "approved") {
    return <span className="pv-badge-success">{t("dashboard.statusApproved")}</span>;
  }
  if (state === "rejected") {
    return <span className="pv-badge-danger">{t("dashboard.statusRejected")}</span>;
  }
  if (state === "pending") {
    return <span className="pv-badge-warning">{t("dashboard.statusPending")}</span>;
  }
  return <span className="pv-badge">{t("dashboard.statusDraft")}</span>;
}

"use client";

import Link from "next/link";
import { useMemo } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { MissionDetailHeader } from "@/components/missions/detail/MissionDetailHeader";
import { MissionDetailLinkedContentAside } from "@/components/missions/detail/MissionDetailLinkedContentAside";
import { MissionDetailStepsSection } from "@/components/missions/detail/MissionDetailStepsSection";
import { useMissionDetailData } from "@/components/missions/detail/useMissionDetailData";
import { trackEvent } from "@/lib/analytics";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { getMissionPresentation } from "@/lib/missionPresentation";
import type { MissionRead } from "@/lib/types";

type MissionDetailClientProps = {
  slug: string;
  initialMission?: MissionRead | null;
  initialError?: string | null;
  initialSignedOut?: boolean;
};

export function MissionDetailClient({
  slug,
  initialMission = null,
  initialError = null,
  initialSignedOut = false,
}: MissionDetailClientProps) {
  const { t, language } = useI18n();
  const { mission, error, isSignedOut, loading, retry } = useMissionDetailData({
    slug,
    language,
    loadFailedMessage: t("missionDetail.loadFailed"),
    initialMission,
    initialError,
    initialSignedOut,
  });

  const missionView = useMemo(
    () => (mission ? getMissionPresentation(language, mission) : null),
    [language, mission],
  );

  const currentMission = missionView?.mission ?? null;
  const nextStep = useMemo(() => {
    if (!missionView) {
      return null;
    }
    if (missionView.nextStep?.href === appRoute.missionBySlug(missionView.mission.slug)) {
      return null;
    }
    return missionView.nextStep;
  }, [missionView]);

  function trackNextStep() {
    if (!nextStep || !currentMission) {
      return;
    }
    trackEvent({
      eventName: "mission_next_step_clicked",
      page: appRoute.missionBySlug(currentMission.slug),
      feature: "mission_detail",
      metadata: {
        mission_id: currentMission.id,
        mission_slug: currentMission.slug,
        status: currentMission.status,
        progress_count: currentMission.progress_count,
        required_count: currentMission.required_count,
        action: nextStep.action,
        href: nextStep.href,
      },
    });
  }

  if (isSignedOut) {
    return (
      <p className="text-sm text-zinc-600">
        {t("missionDetail.signInPrefix")}{" "}
        <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
          {t("missionDetail.signInLink")}
        </Link>{" "}
        {t("missionDetail.signInSuffix")}
      </p>
    );
  }

  if (error) {
    return (
      <div className="pv-alert pv-alert-warning space-y-3">
        <p>{error}</p>
        <button
          type="button"
          onClick={retry}
          className="pv-button-secondary !w-auto"
        >
          {t("dashboard.retry")}
        </button>
      </div>
    );
  }

  if (loading || !missionView || !currentMission) {
    return <p className="text-sm text-zinc-500">{t("missionDetail.loading")}</p>;
  }

  return (
    <article className="space-y-5">
      <MissionDetailHeader missionView={missionView} nextStep={nextStep} onNextStepClick={trackNextStep} />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <MissionDetailStepsSection missionView={missionView} />
        <MissionDetailLinkedContentAside mission={currentMission} />
      </div>
    </article>
  );
}

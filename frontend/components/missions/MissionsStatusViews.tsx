"use client";

import Link from "next/link";

import { PageIntro } from "@/components/navigation/PageIntro";
import { APP_ROUTES } from "@/lib/constants/routes";
import type { TranslationKey } from "@/lib/i18n";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type MissionsStatusViewProps = {
  t: Translate;
};

export function MissionsUnauthenticatedView({ t }: MissionsStatusViewProps) {
  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow={t("nav.missions")}
        title={t("missions.title")}
        description={t("missions.subtitle")}
        hint={t("missions.guestHint")}
        actions={
          <>
            <Link href={APP_ROUTES.login} className="pv-button-primary">
              {t("nav.login")}
            </Link>
            <Link href={APP_ROUTES.catalog} className="pv-inline-link">
              {t("home.explorePrompts")}
              <span aria-hidden="true">↗</span>
            </Link>
          </>
        }
      />
      <div className="pv-empty-state text-sm text-zinc-600">
        {t("missions.signInPrefix")}{" "}
        <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
          {t("missions.signInLink")}
        </Link>{" "}
        {t("missions.signInSuffix")}
      </div>
    </div>
  );
}

type MissionsErrorViewProps = MissionsStatusViewProps & {
  error: string;
  onReload: () => void;
};

export function MissionsErrorView({ t, error, onReload }: MissionsErrorViewProps) {
  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow={t("nav.missions")}
        title={t("missions.title")}
        description={t("missions.subtitle")}
        hint={t("economy.loopBody")}
      />
      <div className="pv-alert pv-alert-warning space-y-3">
        <p>{error}</p>
        <button type="button" onClick={onReload} className="pv-button-secondary !w-auto">
          {t("dashboard.retry")}
        </button>
      </div>
    </div>
  );
}

export function MissionsLoadingView({ t }: MissionsStatusViewProps) {
  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow={t("nav.missions")}
        title={t("missions.title")}
        description={t("missions.subtitle")}
        hint={t("economy.loopBody")}
      />
      <p className="text-sm text-zinc-500">{t("missions.loading")}</p>
    </div>
  );
}

export function MissionsEmptyView({ t }: MissionsStatusViewProps) {
  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow={t("nav.missions")}
        title={t("missions.title")}
        description={t("missions.subtitle")}
        hint={t("economy.loopBody")}
        actions={
          <>
            <Link href={APP_ROUTES.catalog} className="pv-button-primary">
              {t("home.explorePrompts")}
            </Link>
            <Link href={APP_ROUTES.dashboard} className="pv-button-secondary">
              {t("nav.dashboard")}
            </Link>
          </>
        }
      />
      <div className="pv-empty-state text-sm text-zinc-600">{t("missions.empty")}</div>
    </div>
  );
}

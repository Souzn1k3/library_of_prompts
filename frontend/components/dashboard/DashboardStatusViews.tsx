"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { PageIntro } from "@/components/navigation/PageIntro";
import { APP_ROUTES } from "@/lib/constants/routes";

type DashboardTranslate = (
  key: string,
  params?: Record<string, string | number | null | undefined>,
) => string;

type DashboardStatusViewProps = {
  t: DashboardTranslate;
  sectionTitle: ReactNode;
};

export function DashboardLoadingView({ t, sectionTitle }: DashboardStatusViewProps) {
  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow={sectionTitle}
        title={t("dashboard.title")}
        titleClassName="text-2xl font-bold tracking-[-0.04em] sm:text-2xl"
        description={t("dashboard.subtitle")}
      />
      <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>
    </div>
  );
}

export function DashboardUnauthenticatedView({ t, sectionTitle }: DashboardStatusViewProps) {
  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow={sectionTitle}
        title={t("dashboard.title")}
        titleClassName="text-2xl font-bold tracking-[-0.04em] sm:text-2xl"
        description={t("dashboard.subtitle")}
        hint={(
          <>
            {t("dashboard.signinPrefix")}{" "}
            <span className="font-semibold text-zinc-950">{t("dashboard.signinLink")}</span>{" "}
            {t("dashboard.signinSuffix")}
          </>
        )}
        actions={(
          <>
            <Link href={APP_ROUTES.login} className="pv-button-primary">
              {t("nav.login")}
            </Link>
            <Link href={APP_ROUTES.signup} className="pv-button-secondary">
              {t("nav.signup")}
            </Link>
            <Link href={APP_ROUTES.catalog} className="pv-inline-link">
              {t("home.explorePrompts")}
              <span aria-hidden="true">↗</span>
            </Link>
          </>
        )}
      />

      <div className="pv-empty-state text-sm text-zinc-600">
        {t("dashboard.signinPrefix")}{" "}
        <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
          {t("dashboard.signinLink")}
        </Link>{" "}
        {t("dashboard.signinSuffix")}
      </div>
    </div>
  );
}

type DashboardErrorViewProps = DashboardStatusViewProps & {
  error: string;
  onReload: () => void;
};

export function DashboardErrorView({ t, sectionTitle, error, onReload }: DashboardErrorViewProps) {
  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow={sectionTitle}
        title={t("dashboard.title")}
        titleClassName="text-2xl font-bold tracking-[-0.04em] sm:text-2xl"
        description={t("dashboard.subtitle")}
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

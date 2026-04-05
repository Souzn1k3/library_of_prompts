"use client";

import Link from "next/link";

import { PageIntro } from "@/components/navigation/PageIntro";
import { APP_ROUTES } from "@/lib/constants/routes";

import type { TranslateFn } from "./presentation";

type StoreBreadcrumb = Array<{ label: string; href?: string }>;

type StoreStatusViewProps = {
  breadcrumbs: StoreBreadcrumb;
  t: TranslateFn;
};

export function StoreLoadingView({ breadcrumbs, t }: StoreStatusViewProps) {
  return (
    <div className="space-y-6">
      <PageIntro
        breadcrumbs={breadcrumbs}
        eyebrow={t("nav.store")}
        title={t("store.title")}
        description={t("store.subtitle")}
        hint={t("economy.loopBody")}
      />
      <p className="text-sm text-zinc-500">{t("missions.loading")}</p>
    </div>
  );
}

export function StoreUnauthenticatedView({ breadcrumbs, t }: StoreStatusViewProps) {
  return (
    <div className="space-y-6">
      <PageIntro
        breadcrumbs={breadcrumbs}
        eyebrow={t("nav.store")}
        title={t("store.title")}
        description={t("store.subtitle")}
        hint={t("store.guestHint")}
        actions={
          <>
            <Link href={APP_ROUTES.login} className="pv-button-primary">
              {t("nav.login")}
            </Link>
            <Link href={APP_ROUTES.signup} className="pv-button-secondary">
              {t("nav.signup")}
            </Link>
          </>
        }
      />
      <div className="pv-empty-state text-sm text-zinc-600">
        {t("store.signInPrefix")}{" "}
        <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
          {t("store.signInLink")}
        </Link>{" "}
        {t("store.signInSuffix")}
      </div>
    </div>
  );
}

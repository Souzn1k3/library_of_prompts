"use client";

import Link from "next/link";

import { PageIntro } from "@/components/navigation/PageIntro";
import { APP_ROUTES } from "@/lib/constants/routes";
import type { WalletTranslate } from "@/components/wallet/walletPresentation";

type WalletBreadcrumb = Array<{ label: string; href?: string }>;

type WalletStatusViewProps = {
  breadcrumbs: WalletBreadcrumb;
  t: WalletTranslate;
};

export function WalletLoadingView({ breadcrumbs, t }: WalletStatusViewProps) {
  return (
    <div className="space-y-6">
      <PageIntro
        breadcrumbs={breadcrumbs}
        eyebrow={t("nav.wallet")}
        title={t("wallet.title")}
        description={t("wallet.subtitle")}
        hint={t("economy.loopBody")}
      />
      <p className="text-sm text-zinc-500">{t("missions.loading")}</p>
    </div>
  );
}

export function WalletUnauthenticatedView({ breadcrumbs, t }: WalletStatusViewProps) {
  return (
    <div className="space-y-6">
      <PageIntro
        breadcrumbs={breadcrumbs}
        eyebrow={t("nav.wallet")}
        title={t("wallet.title")}
        description={t("wallet.subtitle")}
        hint={t("wallet.guestHint")}
        actions={(
          <>
            <Link href={APP_ROUTES.login} className="pv-button-primary">
              {t("nav.login")}
            </Link>
            <Link href={APP_ROUTES.signup} className="pv-button-secondary">
              {t("nav.signup")}
            </Link>
          </>
        )}
      />
      <div className="pv-empty-state text-sm text-zinc-600">
        {t("wallet.signInPrefix")}{" "}
        <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
          {t("wallet.signInLink")}
        </Link>{" "}
        {t("wallet.signInSuffix")}
      </div>
    </div>
  );
}

type WalletErrorViewProps = WalletStatusViewProps & {
  error: string;
  onReload: () => void;
  onCheckIn: () => void;
};

export function WalletErrorView({ breadcrumbs, t, error, onReload, onCheckIn }: WalletErrorViewProps) {
  return (
    <div className="space-y-6">
      <PageIntro
        breadcrumbs={breadcrumbs}
        eyebrow={t("nav.wallet")}
        title={t("wallet.title")}
        description={t("wallet.subtitle")}
        hint={t("economy.loopBody")}
      />
      <div className="pv-alert pv-alert-warning space-y-3">
        <p>{error}</p>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={onReload} className="pv-button-secondary !w-auto">
            {t("wallet.refresh")}
          </button>
          <button type="button" onClick={onCheckIn} className="pv-button-primary !w-auto">
            {t("wallet.checkinCta")}
          </button>
        </div>
      </div>
    </div>
  );
}

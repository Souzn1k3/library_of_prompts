"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import { APP_ROUTES } from "@/lib/constants/routes";

type ProfileIntroProps = {
  authenticated: boolean;
};

export function ProfileIntro({ authenticated }: ProfileIntroProps) {
  const { t } = useI18n();

  return (
    <PageIntro
      breadcrumbs={[
        {
          label: t("nav.dashboard"),
          href: authenticated ? APP_ROUTES.dashboard : undefined,
        },
        { label: t("footer.account") },
        { label: t("profile.title") },
      ]}
      eyebrow={t("profile.title")}
      title={t("profile.title")}
      description={t("profile.subtitle")}
      actions={
        authenticated ? (
          <>
            <Link href={APP_ROUTES.dashboard} className="pv-button-primary">
              {t("nav.dashboard")}
            </Link>
            <Link href={APP_ROUTES.pricing} className="pv-button-secondary">
              {t("nav.billing")}
            </Link>
            <Link href={APP_ROUTES.wallet} className="pv-button-secondary">
              {t("nav.wallet")}
            </Link>
          </>
        ) : (
          <>
            <Link href={APP_ROUTES.login} className="pv-button-primary">
              {t("nav.login")}
            </Link>
            <Link href={APP_ROUTES.signup} className="pv-button-secondary">
              {t("nav.signup")}
            </Link>
          </>
        )
      }
    />
  );
}

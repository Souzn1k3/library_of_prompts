"use client";

import Link from "next/link";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { getTierTranslationKey } from "@/lib/i18n";

export function ProfileClient() {
  const { status, user } = useAuth();
  const { t } = useI18n();

  if (status === "loading") {
    return <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>;
  }

  if (status === "unauthenticated" || !user) {
    return (
      <p className="text-sm text-zinc-600">
        {t("profile.signInPrefix")}{" "}
        <Link href="/login" className="font-medium text-zinc-900 underline">
          {t("profile.signInLink")}
        </Link>{" "}
        {t("profile.signInSuffix")}
      </p>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
      <section className="pv-panel px-6 py-6 sm:px-7">
        <p className="pv-kicker">{t("profile.accountTitle")}</p>
        <h2 className="mt-3 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{user.display_name}</h2>
        <dl className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="rounded-[1.5rem] border border-zinc-200 bg-white/75 p-4">
            <dt className="pv-kicker">{t("profile.emailLabel")}</dt>
            <dd className="mt-3 font-medium text-zinc-900">{user.email}</dd>
          </div>
          <div className="rounded-[1.5rem] border border-zinc-200 bg-white/75 p-4">
            <dt className="pv-kicker">{t("profile.memberSince")}</dt>
            <dd className="mt-3 font-medium text-zinc-900">{new Date(user.created_at).toLocaleDateString()}</dd>
          </div>
        </dl>
      </section>

      <div className="space-y-6">
        <section className="pv-panel px-6 py-6">
          <p className="pv-kicker">{t("profile.membershipTitle")}</p>
          <div className="mt-4 space-y-3 text-sm text-zinc-600">
            <p>
              {t("profile.planLabel")}:{" "}
              <span className="font-medium text-zinc-900">{t(getTierTranslationKey(user.plan_tier))}</span>
            </p>
            <p>
              {t("profile.creditsLabel")}:{" "}
              <span className="font-medium text-zinc-900">{user.mission_credits ?? 0}</span>
            </p>
          </div>
          <Link href="/pricing" className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand)]">
            {t("footer.pricing")}
            <span aria-hidden="true">↗</span>
          </Link>
        </section>

        <section className="pv-panel px-6 py-6">
          <p className="pv-kicker">{t("profile.actionsTitle")}</p>
          <div className="mt-4 flex flex-wrap gap-3">
            <QuickLink href="/dashboard" label={t("profile.openDashboard")} />
            <QuickLink href="/wallet" label={t("profile.openWallet")} />
            <QuickLink href="/store" label={t("profile.openStore")} />
            <QuickLink href="/onboarding" label={t("profile.finishOnboarding")} />
          </div>
        </section>
      </div>
    </div>
  );
}

function QuickLink({ href, label }: { href: string; label: string }) {
  return (
    <Link href={href} className="pv-button-secondary">
      {label}
    </Link>
  );
}

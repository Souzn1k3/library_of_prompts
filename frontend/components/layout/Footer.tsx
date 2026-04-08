"use client";

import { useMemo } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { FooterBrandBlock } from "@/components/layout/footer/FooterBrandBlock";
import { FooterSections } from "@/components/layout/footer/FooterSections";
import { FooterSocialLinks } from "@/components/layout/footer/FooterSocialLinks";
import { getFooterSections, getSocialLinks } from "@/components/layout/footer/footerData";

export function Footer() {
  const { status } = useAuth();
  const { t } = useI18n();
  const sections = useMemo(() => getFooterSections(status, t), [status, t]);
  const socialLinks = useMemo(() => getSocialLinks(t), [t]);

  return (
    <footer className="mt-16 border-t border-[var(--pv-border)] bg-[var(--pv-bg)]">
      <div className="mx-auto w-full max-w-[1280px] px-4 sm:px-6 lg:px-8">
        <div className="grid gap-10 py-12 sm:py-14 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1.95fr)] lg:gap-16">
          <FooterBrandBlock brandName={t("brand.name")} description={t("footer.description")} />
          <FooterSections
            sections={sections}
            status={status}
            accountLoadingLabel={t("footer.accountLoading")}
          />
        </div>

        <div className="flex flex-col gap-6 border-t border-[var(--pv-border)] py-6 md:flex-row md:items-center md:justify-between">
          <div className="min-w-0 space-y-2">
            <p className="text-sm font-medium text-slate-900">
              © {new Date().getFullYear()} {t("brand.name")}
            </p>
            <p className="text-sm text-slate-500">{t("footer.rights")}</p>
          </div>
          <FooterSocialLinks socialLinks={socialLinks} label={t("footer.socials")} />
        </div>
      </div>
    </footer>
  );
}

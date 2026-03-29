"use client";

import Link from "next/link";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";

type FooterLink = {
  href: string;
  label: string;
  external?: boolean;
};

type FooterSection = {
  id: string;
  title: string;
  links: FooterLink[];
};

const linkClassName =
  "inline-flex items-center gap-2 text-sm leading-6 text-slate-300 transition hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/50 focus-visible:ring-offset-2 focus-visible:ring-offset-transparent";

export function Footer() {
  const { status } = useAuth();
  const { t } = useI18n();

  const sections: FooterSection[] = [
    {
      id: "core",
      title: t("footer.product"),
      links: [
        { href: "/catalog", label: t("nav.catalog") },
        { href: "/learn", label: t("nav.learn") },
        { href: "/missions", label: t("nav.missions") },
        { href: "/pricing", label: t("nav.plans") },
      ],
    },
    {
      id: "economy",
      title: t("nav.economy"),
      links: [
        { href: "/wallet", label: t("nav.wallet") },
        { href: "/store", label: t("nav.store") },
        { href: "/missions", label: t("nav.missions") },
      ],
    },
    {
      id: "account",
      title: t("footer.account"),
      links:
        status === "authenticated"
          ? [
              { href: "/dashboard", label: t("nav.dashboard") },
              { href: "/profile", label: t("nav.profile") },
              { href: "/pricing", label: t("nav.billing") },
              { href: "/submit", label: t("submit.pageTitle") },
            ]
          : [
              { href: "/login", label: t("nav.login") },
              { href: "/signup", label: t("nav.signup") },
              { href: "/pricing", label: t("nav.plans") },
            ],
    },
  ];

  return (
    <footer className="w-full border-t border-white/10 bg-slate-950 px-4 pb-8 pt-8 sm:px-6 lg:px-8 lg:pb-10">
      <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <div className="space-y-3">
          <p className="max-w-[35rem] text-sm leading-relaxed text-slate-300">{t("footer.description")}</p>
          <p className="max-w-[35rem] text-sm leading-relaxed text-slate-300">{t("footer.projectNote")}</p>
        </div>

        <div className="grid gap-8 sm:grid-cols-3">
          {sections.map((section) => (
            <nav key={section.id} aria-labelledby={`footer-${section.id}`} className="space-y-3">
              <h3 id={`footer-${section.id}`} className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                {section.title}
              </h3>
              {section.id === "account" && status === "loading" ? (
                <div className="space-y-2">
                  <span className="block h-4 w-24 rounded-full bg-white/10" aria-hidden />
                  <span className="block h-4 w-20 rounded-full bg-white/10" aria-hidden />
                </div>
              ) : (
                <ul className="space-y-2">
                  {section.links.map((link) => (
                    <li key={`${section.id}-${link.href}`}>
                      <FooterLinkItem link={link} />
                    </li>
                  ))}
                </ul>
              )}
            </nav>
          ))}
        </div>
      </div>

      <div className="mt-8 flex flex-col gap-3 border-t border-white/10 pt-5 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <p>
            © {new Date().getFullYear()} Prompts Vault. {t("footer.rights")}
          </p>
          <p>{t("footer.audience")}</p>
        </div>

        <a
          href="https://t.me/prompts_souz_bot"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-2 text-sm font-semibold text-white transition hover:text-slate-200"
        >
          {t("footer.telegramBot")}
          <span aria-hidden="true">↗</span>
        </a>
      </div>
    </footer>
  );
}

function FooterLinkItem({ link }: { link: FooterLink }) {
  if (link.external) {
    return (
      <a href={link.href} target="_blank" rel="noreferrer" className={linkClassName}>
        <span>{link.label}</span>
      </a>
    );
  }

  return (
    <Link href={link.href} className={linkClassName}>
      <span>{link.label}</span>
    </Link>
  );
}

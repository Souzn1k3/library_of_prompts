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
  "inline-flex items-center gap-2 text-sm leading-6 text-zinc-600 transition hover:text-zinc-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2 focus-visible:ring-offset-transparent";

export function Footer() {
  const { status } = useAuth();
  const { t } = useI18n();

  const sections: FooterSection[] = [
    {
      id: "product",
      title: t("footer.product"),
      links: [
        { href: "/catalog", label: t("nav.catalog") },
        { href: "/learn", label: t("nav.learn") },
        { href: "/missions", label: t("nav.missions") },
        { href: "/pricing", label: t("nav.plans") },
      ],
    },
    {
      id: "resources",
      title: t("footer.resources"),
      links: [
        { href: "/learn", label: t("footer.guides") },
        {
          href: "/catalog?technique=chain_of_thought&sort=most_used",
          label: t("footer.promptTechniques"),
        },
        { href: "/submit", label: t("footer.contribute") },
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
              { href: "/wallet", label: t("nav.wallet") },
              { href: "/store", label: t("nav.store") },
            ]
          : [
              { href: "/login", label: t("nav.login") },
              { href: "/signup", label: t("nav.signup") },
            ],
    },
  ];

  return (
    <footer className="mt-6 border-t border-[var(--pv-border)] px-4 pb-6 pt-8 sm:px-6 lg:px-8 lg:pb-8">
      <div className="mx-auto w-full max-w-[1280px]">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
          <div className="space-y-3">
            <p className="text-base font-semibold tracking-[-0.03em] text-zinc-950">{t("brand.name")}</p>
            <p className="max-w-md text-sm leading-relaxed text-zinc-600">{t("footer.description")}</p>
            <Link href="/catalog" className="pv-inline-link">
              {t("home.explorePrompts")}
              <span aria-hidden="true">↗</span>
            </Link>
          </div>

          <div className="grid gap-8 sm:grid-cols-3">
            {sections.map((section) => (
              <nav key={section.id} aria-labelledby={`footer-${section.id}`} className="space-y-3">
                <h3 id={`footer-${section.id}`} className="pv-kicker">
                  {section.title}
                </h3>
                {section.id === "account" && status === "loading" ? (
                  <div className="space-y-2">
                    <span className="block h-4 w-24 rounded-full bg-zinc-200/80" aria-hidden />
                    <span className="block h-4 w-20 rounded-full bg-zinc-200/70" aria-hidden />
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

        <div className="mt-8 flex flex-col gap-3 border-t border-[var(--pv-border)] pt-5 text-xs text-zinc-500 sm:flex-row sm:items-center sm:justify-between">
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
            className="inline-flex items-center gap-2 text-sm font-medium text-zinc-700 transition hover:text-zinc-950"
          >
            {t("footer.telegramBot")}
            <span aria-hidden="true">↗</span>
          </a>
        </div>
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

"use client";

import type { ComponentPropsWithoutRef, ReactNode } from "react";
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

type SocialLink = {
  id: string;
  href: string;
  label: string;
  icon: (props: ComponentPropsWithoutRef<"svg">) => ReactNode;
};

const footerLinkClassName =
  "inline-flex w-fit items-center rounded-md text-sm leading-6 text-slate-600 transition hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--pv-brand)]";

const footerSectionClassName = "min-w-0 space-y-4";
const footerListClassName = "space-y-2.5";

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
      id: "resources",
      title: t("footer.resources"),
      links: [
        { href: "/learn", label: t("footer.guides") },
        { href: "/catalog", label: t("footer.promptTechniques") },
      ],
    },
    {
      id: "company",
      title: t("footer.company"),
      links: [
        { href: "/", label: t("footer.about") },
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
            ]
          : [
              { href: "/login", label: t("nav.login") },
              { href: "/signup", label: t("nav.signup") },
            ],
    },
  ];

  const socialLinks: SocialLink[] = [
    {
      id: "telegram",
      href: "https://t.me/prompts_souz_bot",
      label: t("footer.telegramBot"),
      icon: TelegramIcon,
    },
    {
      id: "instagram",
      href: "https://instagram.com",
      label: "Instagram",
      icon: InstagramIcon,
    },
    {
      id: "tiktok",
      href: "https://www.tiktok.com",
      label: "TikTok",
      icon: TikTokIcon,
    },
    {
      id: "youtube",
      href: "https://www.youtube.com",
      label: "YouTube",
      icon: YouTubeIcon,
    },
  ];

  return (
    <footer className="mt-16 border-t border-slate-200/80 bg-[rgba(244,247,252,0.96)]">
      <div className="mx-auto w-full max-w-[1280px] px-4 sm:px-6 lg:px-8">
        <div className="grid gap-10 py-12 sm:py-14 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1.95fr)] lg:gap-16">
          <div className="min-w-0 max-w-sm space-y-7">
            <Link href="/" className="inline-flex w-fit items-center gap-4 rounded-2xl">
              <span
                className="flex h-12 w-12 items-center justify-center rounded-2xl text-sm font-bold tracking-[0.18em] text-white shadow-[0_18px_38px_rgba(37,92,255,0.22)]"
                style={{
                  background:
                    "linear-gradient(135deg, var(--pv-brand) 0%, #5b84ff 60%, var(--pv-accent) 100%)",
                }}
              >
                PV
              </span>
              <span className="block text-lg font-semibold tracking-[-0.04em] text-slate-950">
                {t("brand.name")}
              </span>
            </Link>

            <p className="max-w-xs text-sm leading-6 text-slate-600">{t("footer.description")}</p>
          </div>

          <div className="grid min-w-0 gap-x-8 gap-y-10 sm:grid-cols-2 xl:grid-cols-4">
            {sections.map((section) => (
              <nav key={section.id} aria-labelledby={`footer-${section.id}`} className={footerSectionClassName}>
                <h3
                  id={`footer-${section.id}`}
                  className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500"
                >
                  {section.title}
                </h3>
                {section.id === "account" && status === "loading" ? (
                  <div className={footerListClassName} aria-label={t("footer.accountLoading")} role="status">
                    <span className="block h-4 w-24 rounded-full bg-slate-200/80" aria-hidden="true" />
                    <span className="block h-4 w-20 rounded-full bg-slate-200/70" aria-hidden="true" />
                  </div>
                ) : (
                  <ul className={footerListClassName}>
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

        <div className="flex flex-col gap-6 border-t border-slate-200/80 py-6 md:flex-row md:items-center md:justify-between">
          <div className="min-w-0 space-y-2">
            <p className="text-sm font-medium text-slate-900">
              © {new Date().getFullYear()} {t("brand.name")}
            </p>
            <p className="text-sm text-slate-500">{t("footer.rights")}</p>
          </div>

          <div className="flex flex-wrap items-center gap-3" aria-label={t("footer.socials")}>
            {socialLinks.map((link) => {
              const Icon = link.icon;

              return (
                <a
                  key={link.id}
                  href={link.href}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={link.label}
                  title={link.label}
                  className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white/80 text-slate-500 shadow-[0_10px_24px_rgba(15,23,42,0.05)] transition hover:-translate-y-0.5 hover:border-[var(--pv-border-strong)] hover:text-[var(--pv-brand)] hover:shadow-[0_16px_30px_rgba(37,92,255,0.12)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--pv-brand)]"
                >
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </a>
              );
            })}
          </div>
        </div>
      </div>
    </footer>
  );
}

function FooterLinkItem({ link }: { link: FooterLink }) {
  if (link.external) {
    return (
      <a href={link.href} target="_blank" rel="noreferrer" className={footerLinkClassName}>
        <span>{link.label}</span>
      </a>
    );
  }

  return (
    <Link href={link.href} className={footerLinkClassName}>
      <span>{link.label}</span>
    </Link>
  );
}

function TelegramIcon(props: ComponentPropsWithoutRef<"svg">) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="m21.2 4.8-2.7 13.1c-.2 1-1 1.2-1.8.8l-4.2-3.1-2 1.9c-.2.2-.4.4-.8.4l.3-4.4 8.1-7.4c.4-.3-.1-.5-.6-.2l-10 6.3-4.3-1.4c-.9-.3-.9-.9.2-1.4L19.5 4c.8-.3 1.5.2 1.7.8Z" />
    </svg>
  );
}

function InstagramIcon(props: ComponentPropsWithoutRef<"svg">) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <rect x="3.75" y="3.75" width="16.5" height="16.5" rx="4.25" />
      <circle cx="12" cy="12" r="3.75" />
      <circle cx="17.15" cy="6.85" r="0.9" fill="currentColor" stroke="none" />
    </svg>
  );
}

function TikTokIcon(props: ComponentPropsWithoutRef<"svg">) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M14 4.25c.5 1.6 1.6 2.9 3 3.7 1 .6 2 .9 3 .9" />
      <path d="M14 4.25v10.6a4.35 4.35 0 1 1-4.35-4.35c.55 0 1.07.1 1.55.29" />
    </svg>
  );
}

function YouTubeIcon(props: ComponentPropsWithoutRef<"svg">) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M20.5 7.6c-.2-1-.9-1.8-1.9-2C16.9 5.2 14.5 5 12 5S7.1 5.2 5.4 5.6c-1 .2-1.7 1-1.9 2C3.2 9.1 3 10.5 3 12s.2 2.9.5 4.4c.2 1 .9 1.8 1.9 2 1.7.4 4.1.6 6.6.6s4.9-.2 6.6-.6c1-.2 1.7-1 1.9-2 .3-1.5.5-2.9.5-4.4s-.2-2.9-.5-4.4Z" />
      <path d="m10 9.5 5 2.5-5 2.5V9.5Z" fill="currentColor" stroke="none" />
    </svg>
  );
}

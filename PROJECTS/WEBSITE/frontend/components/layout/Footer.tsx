"use client";

import type { JSX } from "react";
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

type IconProps = {
  className?: string;
};

type FooterSocialLink = {
  href: string;
  label: string;
  icon: (props: IconProps) => JSX.Element;
  placeholder?: boolean;
};

const linkClassName =
  "inline-flex items-center gap-2 text-sm leading-6 text-zinc-600 transition-colors duration-200 hover:text-zinc-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-100";

const socialLinkClassName =
  "flex size-9 items-center justify-center rounded-full border border-zinc-200/80 bg-white/80 text-zinc-500 shadow-sm shadow-zinc-950/5 transition-all duration-200 hover:border-zinc-300 hover:bg-white hover:text-zinc-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-100";

export function Footer() {
  const { status } = useAuth();
  const { t } = useI18n();

  const productLinks: FooterLink[] = [
    { href: "/catalog", label: t("nav.catalog") },
    { href: "/learn", label: t("footer.learning") },
    { href: "/missions", label: t("nav.missions") },
    { href: "/plans", label: t("footer.pricing") },
  ];

  const resourceLinks: FooterLink[] = [
    { href: "/learn", label: t("footer.guides") },
    {
      href: "/catalog?technique=chain_of_thought&sort=most_used",
      label: t("footer.promptTechniques"),
    },
    {
      href: "https://t.me/prompts_souz_bot",
      label: t("footer.telegramBot"),
      external: true,
    },
  ];

  const companyLinks: FooterLink[] = [
    { href: "/", label: t("footer.about") },
    { href: "/submit", label: t("footer.contribute") },
  ];

  const accountLinks: FooterLink[] =
    status === "authenticated"
      ? [{ href: "/dashboard", label: t("nav.dashboard") }]
      : [
          { href: "/login", label: t("nav.login") },
          { href: "/signup", label: t("nav.signup") },
        ];

  const sections: FooterSection[] = [
    { id: "product", title: t("footer.product"), links: productLinks },
    { id: "resources", title: t("footer.resources"), links: resourceLinks },
    { id: "company", title: t("footer.company"), links: companyLinks },
    { id: "account", title: t("footer.account"), links: accountLinks },
  ];

  const socialLinks: FooterSocialLink[] = [
    { href: "#", label: "Telegram", icon: TelegramIcon, placeholder: true },
    { href: "#", label: "Instagram", icon: InstagramIcon, placeholder: true },
    { href: "#", label: "TikTok", icon: TikTokIcon, placeholder: true },
    { href: "#", label: "YouTube", icon: YouTubeIcon, placeholder: true },
  ];

  return (
    <footer className="border-t border-zinc-200/90 bg-gradient-to-b from-zinc-100/80 via-zinc-50 to-white shadow-[inset_0_1px_0_rgba(255,255,255,0.78)]">
      <div className="mx-auto w-full max-w-5xl px-4 pb-6 pt-14 sm:pt-16">
        <div className="grid gap-12 border-b border-zinc-200/80 pb-10 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,2.9fr)]">
          <div className="space-y-5">
            <Link
              href="/"
              className="inline-flex items-center text-sm font-semibold tracking-tight text-zinc-950 transition hover:text-zinc-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-100"
            >
              <span>{t("brand.name")}</span>
            </Link>
            <p className="max-w-sm text-sm leading-6 text-zinc-600">{t("footer.description")}</p>
          </div>

          <div className="grid gap-8 sm:grid-cols-2 xl:grid-cols-4">
            {sections.map((section) => (
              <nav
                key={section.id}
                aria-labelledby={`footer-${section.id}-heading`}
                className="space-y-4"
              >
                <h2
                  id={`footer-${section.id}-heading`}
                  className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500"
                >
                  {section.title}
                </h2>
                <ul className="space-y-3">
                  {section.id === "account" && status === "loading" ? (
                    <>
                      <li>
                        <span className="sr-only">{t("footer.accountLoading")}</span>
                        <span className="block h-4 w-24 rounded bg-zinc-200/80" aria-hidden />
                      </li>
                      <li>
                        <span className="block h-4 w-20 rounded bg-zinc-200/70" aria-hidden />
                      </li>
                    </>
                  ) : (
                    section.links.map((link) => (
                      <li key={`${section.id}-${link.href}`}>
                        <FooterLinkItem link={link} />
                      </li>
                    ))
                  )}
                </ul>
              </nav>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-5 pt-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-1.5 text-xs text-zinc-500">
            <p>
              © {new Date().getFullYear()} Prompts Vault. {t("footer.rights")}
            </p>
            <p>{t("footer.audience")}</p>
          </div>

          <div className="flex flex-col gap-3 sm:items-end">
            <span className="text-[0.68rem] font-semibold uppercase tracking-[0.22em] text-zinc-400">
              {t("footer.socials")}
            </span>
            <nav aria-label={t("footer.socials")}>
              <ul className="flex items-center gap-2.5">
                {socialLinks.map((link) => (
                  <li key={link.label}>
                    <FooterSocialLinkItem link={link} />
                  </li>
                ))}
              </ul>
            </nav>
          </div>
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

function FooterSocialLinkItem({ link }: { link: FooterSocialLink }) {
  const Icon = link.icon;
  const externalProps = link.placeholder ? {} : { target: "_blank", rel: "noreferrer" };

  return (
    <a
      href={link.href}
      aria-label={link.label}
      title={link.label}
      aria-disabled={link.placeholder || undefined}
      onClick={link.placeholder ? (event) => event.preventDefault() : undefined}
      className={socialLinkClassName}
      {...externalProps}
    >
      <Icon className="size-4" />
      <span className="sr-only">{link.label}</span>
    </a>
  );
}

function TelegramIcon({ className = "size-4" }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={`${className} -translate-x-px`}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21.5 4.2 3.9 10.9c-1.2.4-1.2 1.1-.2 1.4l4.5 1.4 1.7 5c.2.7.1.9.9.9.5 0 .8-.2 1.2-.6l2.4-2.3 4.8 3.5c.9.5 1.5.3 1.7-.8l3.1-14.1c.3-1.2-.4-1.8-1.5-1.3Z" />
      <path d="m8.1 13.4 10.8-7.1" />
    </svg>
  );
}

function InstagramIcon({ className = "size-4" }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3.75" y="3.75" width="16.5" height="16.5" rx="4.5" />
      <circle cx="12" cy="12" r="3.85" />
      <circle cx="17.2" cy="6.8" r="0.95" fill="currentColor" stroke="none" />
    </svg>
  );
}

function TikTokIcon({ className = "size-4" }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M14.1 4.5c.7 1.8 2.3 3.2 4.2 3.8" />
      <path d="M14.1 4.5v10a3.9 3.9 0 1 1-3.9-3.9" />
    </svg>
  );
}

function YouTubeIcon({ className = "size-4" }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20.3 8.9a3.1 3.1 0 0 0-2.2-2.2c-1.6-.4-4.1-.7-6.1-.7s-4.5.3-6.1.7a3.1 3.1 0 0 0-2.2 2.2c-.4 1.3-.6 2.6-.6 3.8s.2 2.5.6 3.8a3.1 3.1 0 0 0 2.2 2.2c1.6.4 4.1.7 6.1.7s4.5-.3 6.1-.7a3.1 3.1 0 0 0 2.2-2.2c.4-1.3.6-2.6.6-3.8s-.2-2.5-.6-3.8Z" />
      <path d="m10 9.4 5.1 3-5.1 3Z" fill="currentColor" stroke="none" />
    </svg>
  );
}

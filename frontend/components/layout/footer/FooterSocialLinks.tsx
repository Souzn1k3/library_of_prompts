"use client";

import type { SocialLink } from "@/components/layout/footer/footerTypes";

type FooterSocialLinksProps = {
  socialLinks: SocialLink[];
  label: string;
};

export function FooterSocialLinks({ socialLinks, label }: FooterSocialLinksProps) {
  return (
    <div className="flex flex-wrap items-center gap-3" aria-label={label}>
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
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-[0.7rem] border border-[var(--pv-border)] bg-[var(--pv-surface-strong)] text-slate-500 transition hover:border-[var(--pv-border-strong)] hover:text-[var(--pv-brand)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--pv-brand)]"
          >
            <Icon className="h-5 w-5" aria-hidden="true" />
          </a>
        );
      })}
    </div>
  );
}

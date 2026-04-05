"use client";

import Link from "next/link";

import type { FooterLink, FooterSection } from "@/components/layout/footer/footerTypes";

const footerLinkClassName =
  "inline-flex w-fit items-center rounded-md text-sm leading-6 text-slate-600 transition hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--pv-brand)]";

const footerSectionClassName = "min-w-0 space-y-4";
const footerListClassName = "space-y-2.5";

type FooterSectionsProps = {
  sections: FooterSection[];
  status: string;
  accountLoadingLabel: string;
};

export function FooterSections({ sections, status, accountLoadingLabel }: FooterSectionsProps) {
  return (
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
            <div className={footerListClassName} aria-label={accountLoadingLabel} role="status">
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

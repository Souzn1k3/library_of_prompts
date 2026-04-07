"use client";

import Link from "next/link";

type FooterBrandBlockProps = {
  brandName: string;
  description: string;
};

export function FooterBrandBlock({ brandName, description }: FooterBrandBlockProps) {
  return (
    <div className="min-w-0 max-w-sm space-y-7">
      <Link href="/" className="inline-flex w-fit items-center gap-4 rounded-2xl">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl border border-[rgba(29,78,216,0.24)] bg-[var(--pv-brand)] text-sm font-bold tracking-[0.18em] text-white">
          PV
        </span>
        <span className="block text-lg font-semibold tracking-[-0.04em] text-slate-950">
          {brandName}
        </span>
      </Link>

      <p className="max-w-xs text-sm leading-6 text-slate-600">{description}</p>
    </div>
  );
}

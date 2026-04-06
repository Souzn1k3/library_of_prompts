"use client";

import Link from "next/link";
import type { ReactNode } from "react";

type DashboardOpsCardProps = {
  eyebrow: string;
  summary: ReactNode;
  body: string;
  href: string;
  actionLabel: string;
  className?: string;
};

export function DashboardOpsCard({
  eyebrow,
  summary,
  body,
  href,
  actionLabel,
  className,
}: DashboardOpsCardProps) {
  return (
    <div className={`pv-card pv-card-hover-lift flex h-full min-h-[12rem] flex-col gap-3 p-4 sm:p-5 ${className ?? ""}`}>
      <p className="pv-kicker">{eyebrow}</p>
      <div className="space-y-2">
        {summary}
        <p className="text-sm leading-relaxed text-zinc-600">{body}</p>
      </div>
      <div className="mt-auto border-t border-[rgba(15,23,42,0.08)] pt-3">
        <Link href={href} className="pv-inline-link flex w-full justify-between">
          {actionLabel}
          <span aria-hidden="true">↗</span>
        </Link>
      </div>
    </div>
  );
}

export function DashboardMiniMetric({
  label,
  value,
  className,
}: {
  label: string;
  value: number;
  className?: string;
}) {
  return (
    <div
      className={`flex items-center justify-between gap-3 rounded-xl border border-[rgba(15,23,42,0.08)] bg-white/85 px-2.5 py-2 ${className ?? ""}`}
    >
      <p className="text-xs font-semibold tracking-[0.01em] text-zinc-600">{label}</p>
      <p className="text-base font-bold tracking-[-0.04em] leading-none text-zinc-950">{value}</p>
    </div>
  );
}

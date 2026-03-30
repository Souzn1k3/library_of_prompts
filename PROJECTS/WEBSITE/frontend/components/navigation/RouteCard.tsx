import Link from "next/link";
import type { ReactNode } from "react";

type RouteCardProps = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description: ReactNode;
  href: string;
  actionLabel: ReactNode;
  badge?: ReactNode;
  active?: boolean;
  visual?: ReactNode;
  tone?: "neutral" | "earn" | "balance" | "spend";
};

export function RouteCard({
  eyebrow,
  title,
  description,
  href,
  actionLabel,
  badge,
  active = false,
  visual,
  tone = "neutral",
}: RouteCardProps) {
  return (
    <Link
      href={href}
      className={`pv-card-muted pv-route-card flex h-full flex-col gap-5 p-5 sm:p-6 ${
        active ? "border-[var(--pv-border-strong)] bg-white shadow-[0_16px_36px_rgba(37,92,255,0.08)]" : ""
      }`}
      data-active={active ? "true" : "false"}
      data-tone={tone}
    >
      <div className="space-y-4">
        {eyebrow ? <p className="pv-kicker">{eyebrow}</p> : null}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 space-y-4">
            {visual ? <div className="pv-route-card-media">{visual}</div> : null}
            <p className="text-lg font-semibold tracking-[-0.035em] text-zinc-950">{title}</p>
          </div>
          {badge ? <div className="shrink-0 pt-1">{badge}</div> : null}
        </div>
        <p className="text-sm leading-relaxed text-zinc-600">{description}</p>
      </div>
      <span className="pv-route-card-action pv-inline-link mt-auto">
        {actionLabel}
        <span aria-hidden="true">↗</span>
      </span>
    </Link>
  );
}

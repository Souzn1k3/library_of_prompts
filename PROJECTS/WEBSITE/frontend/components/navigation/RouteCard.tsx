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
};

export function RouteCard({
  eyebrow,
  title,
  description,
  href,
  actionLabel,
  badge,
  active = false,
}: RouteCardProps) {
  return (
    <Link
      href={href}
      className={`pv-card-muted flex h-full flex-col gap-4 p-4 ${
        active ? "border-[var(--pv-border-strong)] bg-white shadow-[0_16px_36px_rgba(37,92,255,0.08)]" : ""
      }`}
    >
      <div className="space-y-2">
        {eyebrow ? <p className="pv-kicker">{eyebrow}</p> : null}
        <div className="flex items-start justify-between gap-3">
          <p className="text-base font-semibold tracking-[-0.03em] text-zinc-950">{title}</p>
          {badge ? <div className="shrink-0">{badge}</div> : null}
        </div>
        <p className="text-sm leading-relaxed text-zinc-600">{description}</p>
      </div>
      <span className="pv-inline-link mt-auto">
        {actionLabel}
        <span aria-hidden="true">↗</span>
      </span>
    </Link>
  );
}

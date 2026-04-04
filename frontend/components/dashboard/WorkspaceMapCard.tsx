import Link from "next/link";

export type WorkspaceStatusTone = "neutral" | "info" | "success" | "warning";

type WorkspaceMapCardProps = {
  title: string;
  description: string;
  href: string;
  statusLabel: string;
  statusTone: WorkspaceStatusTone;
  lastVisitLabel: string;
  actionLabel: string;
};

function workspaceStatusClass(tone: WorkspaceStatusTone): string {
  switch (tone) {
    case "success":
      return "pv-badge-success";
    case "warning":
      return "pv-badge-warning";
    case "info":
      return "pv-chip-brand";
    default:
      return "pv-badge";
  }
}

export function WorkspaceMapCard({
  title,
  description,
  href,
  statusLabel,
  statusTone,
  lastVisitLabel,
  actionLabel,
}: WorkspaceMapCardProps) {
  return (
    <Link href={href} className="pv-card-muted pv-card-hover-lift flex h-full min-h-[12rem] flex-col gap-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-lg font-semibold tracking-[-0.035em] text-zinc-950">{title}</h3>
        <span className={workspaceStatusClass(statusTone)}>{statusLabel}</span>
      </div>
      <p className="text-sm leading-relaxed text-zinc-600">{description}</p>
      <p className="text-xs text-zinc-500">{lastVisitLabel}</p>
      <span className="pv-inline-link mt-auto flex w-full items-center justify-between border-t border-[rgba(15,23,42,0.07)] pt-3">
        {actionLabel}
        <span aria-hidden="true">↗</span>
      </span>
    </Link>
  );
}

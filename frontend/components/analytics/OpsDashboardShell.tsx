import Link from "next/link";
import type { ReactNode } from "react";

type OpsTabKey = "growth" | "revenue" | "gtm";

type OpsDashboardHeroProps = {
  kicker: string;
  title: string;
  subtitle: string;
  windowDays: number;
  updatedAt: string;
  activeTab: OpsTabKey;
};

type OpsEmptyStep = {
  label: string;
  body: string;
};

type OpsEmptyAction = {
  href: string;
  label: string;
  tone?: "primary" | "secondary";
};

type OpsDashboardEmptyStateProps = {
  kicker: string;
  title: string;
  message: string;
  steps: OpsEmptyStep[];
  actions: OpsEmptyAction[];
};

type OpsTableSectionProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
};

const TABS: Array<{ key: OpsTabKey; href: string; label: string }> = [
  { key: "growth", href: "/growth", label: "Growth" },
  { key: "revenue", href: "/revenue", label: "Revenue" },
  { key: "gtm", href: "/gtm", label: "GTM" },
];

export function OpsDashboardHero({
  kicker,
  title,
  subtitle,
  windowDays,
  updatedAt,
  activeTab,
}: OpsDashboardHeroProps) {
  return (
    <section className="pv-hero px-6 py-7 sm:px-8 sm:py-8">
      <p className="pv-kicker">{kicker}</p>
      <h1 className="pv-title max-w-4xl text-zinc-950">{title}</h1>
      <p className="mt-3 pv-lead max-w-3xl">{subtitle}</p>
      <p className="mt-3 text-sm font-medium text-zinc-600">
        Window: {windowDays}d · Updated: {new Date(updatedAt).toLocaleString()}
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {TABS.map((tab) => (
          <Link
            key={tab.key}
            href={tab.href}
            className={`pv-nav-pill !min-h-0 !px-3 !py-1.5 !text-xs ${activeTab === tab.key ? "pv-nav-pill-active" : ""}`}
          >
            {tab.label}
          </Link>
        ))}
      </div>
    </section>
  );
}

export function OpsDashboardEmptyState({
  kicker,
  title,
  message,
  steps,
  actions,
}: OpsDashboardEmptyStateProps) {
  return (
    <div className="pv-page-sm">
      <section className="pv-hero px-6 py-7 sm:px-8 sm:py-8">
        <p className="pv-kicker">{kicker}</p>
        <h1 className="pv-title max-w-4xl text-zinc-950">{title}</h1>
        <p className="mt-3 pv-lead max-w-3xl">{message}</p>
      </section>
      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Next step to unlock analytics</h2>
          <p className="mt-2 text-sm text-zinc-600">
            Run product loop events and billing actions. This dashboard updates automatically after ingestion.
          </p>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          {steps.map((step) => (
            <article key={step.label} className="pv-analytics-card">
              <p className="pv-analytics-label">{step.label}</p>
              <p className="mt-2 text-sm text-zinc-700">{step.body}</p>
            </article>
          ))}
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          {actions.map((action) => (
            <Link
              key={`${action.href}:${action.label}`}
              href={action.href}
              className={`${action.tone === "primary" ? "pv-button-primary" : "pv-button-secondary"} !w-auto`}
            >
              {action.label}
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

export function OpsTableSection({ title, subtitle, children }: OpsTableSectionProps) {
  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-copy">
        <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">{title}</h2>
        {subtitle ? <p className="mt-2 text-sm text-zinc-600">{subtitle}</p> : null}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

export function OpsTableEmptyRow({ colSpan, label }: { colSpan: number; label: string }) {
  return (
    <tr>
      <td className="pv-analytics-table-empty" colSpan={colSpan}>
        {label}
      </td>
    </tr>
  );
}

import { ApiRequestError, fetchGrowthDashboard } from "@/lib/api";
import { getServerAccessToken } from "@/lib/server-auth";
import {
  OpsDashboardEmptyState,
  OpsDashboardHero,
  OpsTableEmptyRow,
  OpsTableSection,
} from "@/components/analytics/OpsDashboardShell";

function metric(value: number | null, suffix = "%"): string {
  if (value === null || value === undefined) {
    return "n/a";
  }
  if (!Number.isFinite(value)) {
    return "0";
  }
  if (!suffix) {
    return `${value.toFixed(2)}`;
  }
  return `${value.toFixed(2)}${suffix}`;
}

export default async function GrowthDashboardPage() {
  const token = await getServerAccessToken();

  let dashboard = null;
  let error: string | null = null;
  try {
    dashboard = await fetchGrowthDashboard(token, { windowDays: 28 });
  } catch (cause) {
    if (cause instanceof ApiRequestError) {
      error = `Growth dashboard unavailable (${cause.status})`;
    } else {
      error = "Growth dashboard unavailable";
    }
  }

  if (!dashboard) {
    return (
      <OpsDashboardEmptyState
        kicker="Growth OS"
        title="Growth Operating Dashboard"
        message={error ?? "No growth data available yet."}
        steps={[
          { label: "1. Run scenarios", body: "Generate activity from home workbench or catalog flows." },
          { label: "2. Activate billing", body: "Enable plan tracking to unlock conversion and paywall metrics." },
          { label: "3. Re-open dashboard", body: "Return here after activity to review activation and retention." },
        ]}
        actions={[
          { href: "/pricing?tier=starter", label: "Upgrade plan", tone: "primary" },
          { href: "/dashboard", label: "Open dashboard" },
          { href: "/catalog", label: "Run scenarios" },
        ]}
      />
    );
  }

  const metrics = dashboard.metrics;

  return (
    <div className="pv-page-sm">
      <OpsDashboardHero
        kicker="Growth OS"
        title="Growth Operating Dashboard"
        subtitle={`Activation, retention, and upgrade conversion for the last ${metrics.window_days} days.`}
        windowDays={metrics.window_days}
        updatedAt={metrics.computed_at}
        activeTab="growth"
      />

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        <article className="pv-analytics-card">
          <p className="pv-analytics-label">Activation</p>
          <p className="pv-analytics-value">{metric(metrics.activation_rate)}</p>
        </article>
        <article className="pv-analytics-card">
          <p className="pv-analytics-label">D1 Retention</p>
          <p className="pv-analytics-value">{metric(metrics.d1_retention)}</p>
        </article>
        <article className="pv-analytics-card">
          <p className="pv-analytics-label">D7 Retention</p>
          <p className="pv-analytics-value">{metric(metrics.d7_retention)}</p>
        </article>
        <article className="pv-analytics-card">
          <p className="pv-analytics-label">Free → Paid</p>
          <p className="pv-analytics-value">{metric(metrics.free_to_paid_conversion)}</p>
        </article>
        <article className="pv-analytics-card">
          <p className="pv-analytics-label">Upgrade Intent</p>
          <p className="pv-analytics-value">{metric(metrics.upgrade_intent_rate)}</p>
        </article>
        <article className="pv-analytics-card">
          <p className="pv-analytics-label">LTV Proxy</p>
          <p className="pv-analytics-value">{metric(metrics.ltv_proxy_usd, "$")}</p>
        </article>
      </div>

      <OpsTableSection
        title="Funnel"
        subtitle="Spot where users drop before their first paid conversion."
      >
        <div className="grid gap-2 md:grid-cols-5">
          {dashboard.funnel.steps.map((step) => (
            <article key={step.key} className="pv-analytics-card">
              <div className="pv-analytics-label">{step.label}</div>
              <div className="pv-analytics-value">{step.users}</div>
              <div className="pv-analytics-meta">
                Conv from prev: {metric(step.conversion_from_prev)}
              </div>
            </article>
          ))}
        </div>
      </OpsTableSection>

      <OpsTableSection
        title="Cohorts"
        subtitle="Weekly retention and paid conversion benchmark."
      >
        <div className="pv-analytics-table-wrap">
          <table className="pv-analytics-table">
            <thead>
              <tr>
                <th>Week</th>
                <th>Users</th>
                <th>D1</th>
                <th>D7</th>
                <th>Paid 30d</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.cohorts.length ? (
                dashboard.cohorts.map((cohort) => (
                  <tr key={cohort.cohort_week_start}>
                    <td>{cohort.cohort_week_start}</td>
                    <td>{cohort.users}</td>
                    <td>{metric(cohort.d1_retention)}</td>
                    <td>
                      {cohort.d7_retention == null ? "n/a" : metric(cohort.d7_retention)}
                    </td>
                    <td>
                      {cohort.paid_30d_conversion == null ? "n/a" : metric(cohort.paid_30d_conversion)}
                    </td>
                  </tr>
                ))
              ) : (
                <OpsTableEmptyRow colSpan={5} label="No cohort rows in the selected window." />
              )}
            </tbody>
          </table>
        </div>
      </OpsTableSection>

      <OpsTableSection title="Experiment Performance" subtitle="Conversion and D7 retention by active growth experiments.">
        <div className="pv-analytics-table-wrap">
          <table className="pv-analytics-table">
            <thead>
              <tr>
                <th>Experiment</th>
                <th>Variant</th>
                <th>Users</th>
                <th>Conversion</th>
                <th>D7 retention</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.experiments.length ? (
                dashboard.experiments.flatMap((experiment) =>
                  experiment.variants.map((variant) => (
                    <tr key={`${experiment.key}:${variant.variant}`}>
                      <td>{experiment.key}</td>
                      <td>{variant.variant}</td>
                      <td>{variant.users}</td>
                      <td>{metric(variant.conversion)}</td>
                      <td>{metric(variant.retention_d7)}</td>
                    </tr>
                  )),
                )
              ) : (
                <OpsTableEmptyRow colSpan={5} label="No experiment data captured yet." />
              )}
            </tbody>
          </table>
        </div>
      </OpsTableSection>

      <OpsTableSection title="Rollout Flags" subtitle="Current flag rollout configuration and eligibility target.">
        <div className="grid gap-3 md:grid-cols-3">
          {dashboard.rollout_flags.length ? (
            dashboard.rollout_flags.map((flag) => (
              <article key={flag.key} className="pv-analytics-card">
                <p className="pv-analytics-label">{flag.key}</p>
                <p className="mt-2 text-sm font-semibold text-zinc-900">{flag.target}</p>
                <p className="pv-analytics-meta">
                  Rollout: {flag.rollout_percent}% · {flag.enabled ? "enabled" : "disabled"}
                </p>
                <p className="mt-2 text-xs text-zinc-500">{flag.reason}</p>
              </article>
            ))
          ) : (
            <article className="pv-analytics-card md:col-span-3">
              <p className="text-sm text-zinc-600">No rollout flags configured.</p>
            </article>
          )}
        </div>
      </OpsTableSection>
    </div>
  );
}

import { ApiRequestError, fetchRevenueDashboard } from "@/lib/api";
import { getServerAccessToken } from "@/lib/server-auth";
import {
  OpsDashboardEmptyState,
  OpsDashboardHero,
  OpsTableEmptyRow,
  OpsTableSection,
} from "@/components/analytics/OpsDashboardShell";

function pct(value: number | null): string {
  if (value === null || value === undefined) {
    return "n/a";
  }
  return `${value.toFixed(2)}%`;
}

function usd(value: number | null): string {
  if (value === null || value === undefined) {
    return "n/a";
  }
  return `$${value.toFixed(2)}`;
}

export default async function RevenuePage() {
  const token = await getServerAccessToken();

  let dashboard = null;
  let error: string | null = null;
  try {
    dashboard = await fetchRevenueDashboard(token, { windowDays: 30 });
  } catch (cause) {
    if (cause instanceof ApiRequestError) {
      error = `Revenue dashboard unavailable (${cause.status})`;
    } else {
      error = "Revenue dashboard unavailable";
    }
  }

  if (!dashboard) {
    return (
      <OpsDashboardEmptyState
        kicker="Revenue OS"
        title="Revenue OS Dashboard"
        message={error ?? "No revenue data available yet."}
        steps={[
          { label: "1. Billing setup", body: "Activate a paid tier to start subscription tracking." },
          { label: "2. Traffic flow", body: "Drive catalog traffic and first prompt actions." },
          { label: "3. Conversion loop", body: "Return to inspect MRR, churn, and paywall performance." },
        ]}
        actions={[
          { href: "/pricing?tier=starter", label: "Upgrade plan", tone: "primary" },
          { href: "/dashboard", label: "Open dashboard" },
          { href: "/catalog", label: "Open catalog" },
        ]}
      />
    );
  }

  const h = dashboard.headline;
  return (
    <div className="pv-page-sm">
      <OpsDashboardHero
        kicker="Revenue OS"
        title="Revenue OS Dashboard"
        subtitle="MRR health, conversion quality, and monetization efficiency for the current window."
        windowDays={h.window_days}
        updatedAt={h.computed_at}
        activeTab="revenue"
      />

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">MRR</div>
          <div className="pv-analytics-value">{usd(h.mrr_usd)}</div>
        </article>
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">ARR</div>
          <div className="pv-analytics-value">{usd(h.arr_usd)}</div>
        </article>
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">ARPU</div>
          <div className="pv-analytics-value">{usd(h.arpu_usd)}</div>
        </article>
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">Free → Paid</div>
          <div className="pv-analytics-value">{pct(h.free_to_paid_conversion)}</div>
        </article>
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">Revenue / Active User</div>
          <div className="pv-analytics-value">{usd(h.revenue_per_user_usd)}</div>
        </article>
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">Churn</div>
          <div className="pv-analytics-value">{pct(h.churn_rate)}</div>
        </article>
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">LTV Proxy</div>
          <div className="pv-analytics-value">{usd(h.ltv_proxy_usd)}</div>
        </article>
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">Paying D30 Retention</div>
          <div className="pv-analytics-value">{pct(h.paying_user_retention_d30)}</div>
        </article>
      </div>

      <OpsTableSection title="Revenue Funnel" subtitle="Full path from acquisition to paid conversion.">
        <div className="grid gap-2 md:grid-cols-4 xl:grid-cols-7">
          {dashboard.funnel.steps.map((step) => (
            <article key={step.key} className="pv-analytics-card">
              <div className="pv-analytics-label">{step.label}</div>
              <div className="pv-analytics-value">{step.users}</div>
              <div className="pv-analytics-meta">Conv: {pct(step.conversion_from_prev)}</div>
            </article>
          ))}
        </div>
      </OpsTableSection>

      <OpsTableSection title="Revenue By Source" subtitle="MRR and conversion contribution per acquisition source.">
        <div className="pv-analytics-table-wrap">
          <table className="pv-analytics-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Acquired</th>
                <th>Paid</th>
                <th>Conv</th>
                <th>MRR</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.revenue_by_source.length ? (
                dashboard.revenue_by_source.map((row) => (
                  <tr key={row.source}>
                    <td>{row.source}</td>
                    <td>{row.acquired_users}</td>
                    <td>{row.paid_users}</td>
                    <td>{pct(row.conversion_rate)}</td>
                    <td>{usd(row.mrr_usd)}</td>
                  </tr>
                ))
              ) : (
                <OpsTableEmptyRow colSpan={5} label="No source-attributed revenue in this window." />
              )}
            </tbody>
          </table>
        </div>
      </OpsTableSection>

      <OpsTableSection title="Paywall Performance" subtitle="Performance by paywall and pricing variants.">
        <div className="pv-analytics-table-wrap">
          <table className="pv-analytics-table">
            <thead>
              <tr>
                <th>Experiment</th>
                <th>Variant</th>
                <th>Views</th>
                <th>Interactions</th>
                <th>Paid</th>
                <th>Conv</th>
                <th>RPU</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.paywall_performance.length ? (
                dashboard.paywall_performance.map((row) => (
                  <tr key={`${row.experiment_key}:${row.variant}`}>
                    <td>{row.experiment_key}</td>
                    <td>{row.variant}</td>
                    <td>{row.views}</td>
                    <td>{row.interactions}</td>
                    <td>{row.paid_users}</td>
                    <td>{pct(row.conversion_rate)}</td>
                    <td>{usd(row.revenue_per_user_usd)}</td>
                  </tr>
                ))
              ) : (
                <OpsTableEmptyRow colSpan={7} label="No paywall experiments were observed." />
              )}
            </tbody>
          </table>
        </div>
      </OpsTableSection>

      <OpsTableSection title="Funnel By Source" subtitle="Contribution flow from acquisition to paid by source.">
        <div className="pv-analytics-table-wrap">
          <table className="pv-analytics-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Acquired</th>
                <th>Paid</th>
                <th>Conv</th>
                <th>ARR</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.funnel_by_source.length ? (
                dashboard.funnel_by_source.map((row) => (
                  <tr key={`source-funnel-${row.source}`}>
                    <td>{row.source}</td>
                    <td>{row.acquired_users}</td>
                    <td>{row.paid_users}</td>
                    <td>{pct(row.conversion_rate)}</td>
                    <td>{usd(row.arr_usd)}</td>
                  </tr>
                ))
              ) : (
                <OpsTableEmptyRow colSpan={5} label="No source funnel rows for this period." />
              )}
            </tbody>
          </table>
        </div>
      </OpsTableSection>

      <OpsTableSection title="Top Cohorts" subtitle="Revenue quality by signup week, source, and plan tier.">
        <div className="pv-analytics-table-wrap">
          <table className="pv-analytics-table">
            <thead>
              <tr>
                <th>Week</th>
                <th>Source</th>
                <th>Plan</th>
                <th>Users</th>
                <th>Paid</th>
                <th>Revenue</th>
                <th>D30 Retention</th>
                <th>Conv Lag</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.cohorts.length ? (
                dashboard.cohorts.slice(0, 12).map((row, index) => (
                  <tr key={`${row.cohort_week_start}:${row.source}:${row.plan_tier}:${index}`}>
                    <td>{row.cohort_week_start}</td>
                    <td>{row.source}</td>
                    <td>{row.plan_tier}</td>
                    <td>{row.users}</td>
                    <td>{row.paid_users}</td>
                    <td>{usd(row.revenue_usd)}</td>
                    <td>{pct(row.retention_d30)}</td>
                    <td>{row.conversion_lag_days == null ? "n/a" : `${row.conversion_lag_days.toFixed(1)}d`}</td>
                  </tr>
                ))
              ) : (
                <OpsTableEmptyRow colSpan={8} label="No cohort rows available." />
              )}
            </tbody>
          </table>
        </div>
      </OpsTableSection>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Churn Signals</h2>
          <p className="mt-2 text-sm text-zinc-600">
            Risk counters for immediate retention actions and reactivation campaigns.
          </p>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <article className="pv-analytics-card">
            <div className="pv-analytics-label">At Risk</div>
            <div className="pv-analytics-value">{dashboard.churn_signals.churn_risk_users}</div>
          </article>
          <article className="pv-analytics-card">
            <div className="pv-analytics-label">Canceled</div>
            <div className="pv-analytics-value">{dashboard.churn_signals.canceled_users}</div>
          </article>
          <article className="pv-analytics-card">
            <div className="pv-analytics-label">Inactive Paying</div>
            <div className="pv-analytics-value">{dashboard.churn_signals.inactive_paying_users}</div>
          </article>
        </div>
      </section>
    </div>
  );
}

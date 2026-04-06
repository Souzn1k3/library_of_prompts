import Link from "next/link";

import { ApiRequestError, fetchRevenueDashboard } from "@/lib/api";
import { getServerAccessToken } from "@/lib/server-auth";

function pct(value: number): string {
  return `${value.toFixed(2)}%`;
}

function usd(value: number): string {
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
      <div className="pv-page-sm">
        <section className="pv-hero px-6 py-7 sm:px-8 sm:py-8">
          <p className="pv-kicker">Revenue OS</p>
          <h1 className="pv-title max-w-4xl text-zinc-950">Revenue OS Dashboard</h1>
          <p className="mt-3 pv-lead max-w-3xl">{error ?? "No revenue data available yet."}</p>
        </section>
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-copy">
            <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Enable revenue tracking</h2>
            <p className="mt-2 text-sm text-zinc-600">
              Revenue analytics appears after billing activation and user acquisition events.
            </p>
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-3">
            <article className="pv-analytics-card">
              <p className="pv-analytics-label">Billing setup</p>
              <p className="mt-2 text-sm text-zinc-700">Activate a paid tier to start subscription tracking.</p>
            </article>
            <article className="pv-analytics-card">
              <p className="pv-analytics-label">Traffic flow</p>
              <p className="mt-2 text-sm text-zinc-700">Drive catalog traffic and first prompt actions.</p>
            </article>
            <article className="pv-analytics-card">
              <p className="pv-analytics-label">Conversion loop</p>
              <p className="mt-2 text-sm text-zinc-700">Return to inspect MRR, churn, and paywall performance.</p>
            </article>
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            <Link href="/pricing?tier=starter" className="pv-button-primary !w-auto">Upgrade plan</Link>
            <Link href="/dashboard" className="pv-button-secondary !w-auto">Open dashboard</Link>
            <Link href="/catalog" className="pv-button-secondary !w-auto">Open catalog</Link>
          </div>
        </section>
      </div>
    );
  }

  const h = dashboard.headline;
  return (
    <div className="pv-page-sm">
      <section className="pv-hero px-6 py-7 sm:px-8 sm:py-8">
        <p className="pv-kicker">Revenue OS</p>
        <h1 className="pv-title max-w-4xl text-zinc-950">Revenue OS Dashboard</h1>
        <p className="mt-3 pv-lead max-w-3xl">
          MRR health, conversion quality, and monetization efficiency for the current window.
        </p>
        <p className="mt-3 text-sm font-medium text-zinc-600">
          Window: {h.window_days}d · Updated: {new Date(h.computed_at).toLocaleString()}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href="/growth" className="pv-nav-pill !min-h-0 !px-3 !py-1.5 !text-xs">
            Growth
          </Link>
          <Link href="/revenue" className="pv-nav-pill pv-nav-pill-active !min-h-0 !px-3 !py-1.5 !text-xs">
            Revenue
          </Link>
          <Link href="/gtm" className="pv-nav-pill !min-h-0 !px-3 !py-1.5 !text-xs">
            GTM
          </Link>
        </div>
      </section>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">MRR</div>
          <div className="pv-analytics-value">{usd(h.mrr_usd)}</div>
        </article>
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">ARR</div>
          <div className="pv-analytics-value">{usd(h.arr_usd)}</div>
        </article>
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">Free → Paid</div>
          <div className="pv-analytics-value">{pct(h.free_to_paid_conversion)}</div>
        </article>
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">Churn</div>
          <div className="pv-analytics-value">{pct(h.churn_rate)}</div>
        </article>
        <article className="pv-analytics-card">
          <div className="pv-analytics-label">LTV Proxy</div>
          <div className="pv-analytics-value">{usd(h.ltv_proxy_usd)}</div>
        </article>
      </div>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Revenue Funnel</h2>
          <p className="mt-2 text-sm text-zinc-600">Full path from acquisition to paid conversion.</p>
        </div>
        <div className="mt-5 grid gap-2 md:grid-cols-4 xl:grid-cols-7">
          {dashboard.funnel.steps.map((step) => (
            <article key={step.key} className="pv-analytics-card">
              <div className="pv-analytics-label">{step.label}</div>
              <div className="pv-analytics-value">{step.users}</div>
              <div className="pv-analytics-meta">Conv: {pct(step.conversion_from_prev)}</div>
            </article>
          ))}
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Revenue By Source</h2>
        </div>
        <div className="pv-analytics-table-wrap mt-5">
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
              {dashboard.revenue_by_source.map((row) => (
                <tr key={row.source}>
                  <td>{row.source}</td>
                  <td>{row.acquired_users}</td>
                  <td>{row.paid_users}</td>
                  <td>{pct(row.conversion_rate)}</td>
                  <td>{usd(row.mrr_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Paywall Performance</h2>
        </div>
        <div className="pv-analytics-table-wrap mt-5">
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
              {dashboard.paywall_performance.map((row) => (
                <tr key={`${row.experiment_key}:${row.variant}`}>
                  <td>{row.experiment_key}</td>
                  <td>{row.variant}</td>
                  <td>{row.views}</td>
                  <td>{row.interactions}</td>
                  <td>{row.paid_users}</td>
                  <td>{pct(row.conversion_rate)}</td>
                  <td>{usd(row.revenue_per_user_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Top Cohorts</h2>
        </div>
        <div className="pv-analytics-table-wrap mt-5">
          <table className="pv-analytics-table">
            <thead>
              <tr>
                <th>Week</th>
                <th>Source</th>
                <th>Plan</th>
                <th>Users</th>
                <th>Paid</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.cohorts.slice(0, 10).map((row, index) => (
                <tr key={`${row.cohort_week_start}:${row.source}:${row.plan_tier}:${index}`}>
                  <td>{row.cohort_week_start}</td>
                  <td>{row.source}</td>
                  <td>{row.plan_tier}</td>
                  <td>{row.users}</td>
                  <td>{row.paid_users}</td>
                  <td>{usd(row.revenue_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

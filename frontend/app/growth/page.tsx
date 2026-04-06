import Link from "next/link";

import { ApiRequestError, fetchGrowthDashboard } from "@/lib/api";
import { getServerAccessToken } from "@/lib/server-auth";

function metric(value: number, suffix = "%"): string {
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
      <div className="pv-page-sm">
        <section className="pv-hero px-6 py-7 sm:px-8 sm:py-8">
          <p className="pv-kicker">Growth OS</p>
          <h1 className="pv-title max-w-4xl text-zinc-950">Growth Operating Dashboard</h1>
          <p className="mt-3 pv-lead max-w-3xl">{error ?? "No growth data available yet."}</p>
        </section>
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-copy">
            <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Next step to unlock analytics</h2>
            <p className="mt-2 text-sm text-zinc-600">
              Connect billing and run scenarios to populate this dashboard with live conversion data.
            </p>
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-3">
            <article className="pv-analytics-card">
              <p className="pv-analytics-label">1. Run scenarios</p>
              <p className="mt-2 text-sm text-zinc-700">Generate activity from home workbench or catalog flows.</p>
            </article>
            <article className="pv-analytics-card">
              <p className="pv-analytics-label">2. Activate billing</p>
              <p className="mt-2 text-sm text-zinc-700">Enable plan tracking to unlock conversion and paywall metrics.</p>
            </article>
            <article className="pv-analytics-card">
              <p className="pv-analytics-label">3. Re-open dashboard</p>
              <p className="mt-2 text-sm text-zinc-700">Return here after activity to review activation and retention.</p>
            </article>
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            <Link href="/pricing?tier=starter" className="pv-button-primary !w-auto">Upgrade plan</Link>
            <Link href="/dashboard" className="pv-button-secondary !w-auto">Open dashboard</Link>
            <Link href="/catalog" className="pv-button-secondary !w-auto">Run scenarios</Link>
          </div>
        </section>
      </div>
    );
  }

  const metrics = dashboard.metrics;

  return (
    <div className="pv-page-sm">
      <section className="pv-hero px-6 py-7 sm:px-8 sm:py-8">
        <p className="pv-kicker">Growth OS</p>
        <h1 className="pv-title max-w-4xl text-zinc-950">Growth Operating Dashboard</h1>
        <p className="mt-3 pv-lead max-w-3xl">
          Activation, retention, and upgrade conversion for the last {metrics.window_days} days.
        </p>
        <p className="mt-3 text-sm font-medium text-zinc-600">
          Window: {metrics.window_days}d · Updated: {new Date(metrics.computed_at).toLocaleString()}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href="/growth" className="pv-nav-pill pv-nav-pill-active !min-h-0 !px-3 !py-1.5 !text-xs">
            Growth
          </Link>
          <Link href="/revenue" className="pv-nav-pill !min-h-0 !px-3 !py-1.5 !text-xs">
            Revenue
          </Link>
          <Link href="/gtm" className="pv-nav-pill !min-h-0 !px-3 !py-1.5 !text-xs">
            GTM
          </Link>
        </div>
      </section>

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

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Funnel</h2>
          <p className="mt-2 text-sm text-zinc-600">Spot where users drop before their first paid conversion.</p>
        </div>
        <div className="mt-5 grid gap-2 md:grid-cols-5">
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
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Cohorts</h2>
          <p className="mt-2 text-sm text-zinc-600">Weekly retention and paid conversion benchmark.</p>
        </div>
        <div className="pv-analytics-table-wrap mt-5">
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
              {dashboard.cohorts.map((cohort) => (
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
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

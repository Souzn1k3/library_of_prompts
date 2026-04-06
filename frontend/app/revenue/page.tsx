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
      <section className="space-y-3">
        <h1 className="text-2xl font-semibold tracking-tight">Revenue OS Dashboard</h1>
        <p className="text-sm text-[var(--muted-foreground)]">{error ?? "No revenue data available yet."}</p>
      </section>
    );
  }

  const h = dashboard.headline;
  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Revenue OS Dashboard</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Window: {h.window_days}d · Updated: {new Date(h.computed_at).toLocaleString()}
        </p>
      </header>

      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-5">
        <article className="rounded-xl border p-3"><div className="text-xs text-[var(--muted-foreground)]">MRR</div><div className="text-xl font-semibold">{usd(h.mrr_usd)}</div></article>
        <article className="rounded-xl border p-3"><div className="text-xs text-[var(--muted-foreground)]">ARR</div><div className="text-xl font-semibold">{usd(h.arr_usd)}</div></article>
        <article className="rounded-xl border p-3"><div className="text-xs text-[var(--muted-foreground)]">Free → Paid</div><div className="text-xl font-semibold">{pct(h.free_to_paid_conversion)}</div></article>
        <article className="rounded-xl border p-3"><div className="text-xs text-[var(--muted-foreground)]">Churn</div><div className="text-xl font-semibold">{pct(h.churn_rate)}</div></article>
        <article className="rounded-xl border p-3"><div className="text-xs text-[var(--muted-foreground)]">LTV Proxy</div><div className="text-xl font-semibold">{usd(h.ltv_proxy_usd)}</div></article>
      </div>

      <section className="rounded-xl border p-4 space-y-2">
        <h2 className="text-lg font-semibold">Revenue Funnel</h2>
        <div className="grid gap-2 md:grid-cols-4 xl:grid-cols-7">
          {dashboard.funnel.steps.map((step) => (
            <article key={step.key} className="rounded-lg border p-3">
              <div className="text-xs text-[var(--muted-foreground)]">{step.label}</div>
              <div className="text-lg font-semibold">{step.users}</div>
              <div className="text-xs text-[var(--muted-foreground)]">Conv: {pct(step.conversion_from_prev)}</div>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-xl border p-4 space-y-2">
        <h2 className="text-lg font-semibold">Revenue By Source</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-[var(--muted-foreground)]">
                <th className="py-1 pr-4">Source</th>
                <th className="py-1 pr-4">Acquired</th>
                <th className="py-1 pr-4">Paid</th>
                <th className="py-1 pr-4">Conv</th>
                <th className="py-1 pr-4">MRR</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.revenue_by_source.map((row) => (
                <tr key={row.source}>
                  <td className="py-1 pr-4">{row.source}</td>
                  <td className="py-1 pr-4">{row.acquired_users}</td>
                  <td className="py-1 pr-4">{row.paid_users}</td>
                  <td className="py-1 pr-4">{pct(row.conversion_rate)}</td>
                  <td className="py-1 pr-4">{usd(row.mrr_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border p-4 space-y-2">
        <h2 className="text-lg font-semibold">Paywall Performance</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-[var(--muted-foreground)]">
                <th className="py-1 pr-4">Experiment</th>
                <th className="py-1 pr-4">Variant</th>
                <th className="py-1 pr-4">Views</th>
                <th className="py-1 pr-4">Interactions</th>
                <th className="py-1 pr-4">Paid</th>
                <th className="py-1 pr-4">Conv</th>
                <th className="py-1 pr-4">RPU</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.paywall_performance.map((row) => (
                <tr key={`${row.experiment_key}:${row.variant}`}>
                  <td className="py-1 pr-4">{row.experiment_key}</td>
                  <td className="py-1 pr-4">{row.variant}</td>
                  <td className="py-1 pr-4">{row.views}</td>
                  <td className="py-1 pr-4">{row.interactions}</td>
                  <td className="py-1 pr-4">{row.paid_users}</td>
                  <td className="py-1 pr-4">{pct(row.conversion_rate)}</td>
                  <td className="py-1 pr-4">{usd(row.revenue_per_user_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border p-4 space-y-2">
        <h2 className="text-lg font-semibold">Top Cohorts</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-[var(--muted-foreground)]">
                <th className="py-1 pr-4">Week</th>
                <th className="py-1 pr-4">Source</th>
                <th className="py-1 pr-4">Plan</th>
                <th className="py-1 pr-4">Users</th>
                <th className="py-1 pr-4">Paid</th>
                <th className="py-1 pr-4">Revenue</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.cohorts.slice(0, 10).map((row, index) => (
                <tr key={`${row.cohort_week_start}:${row.source}:${row.plan_tier}:${index}`}>
                  <td className="py-1 pr-4">{row.cohort_week_start}</td>
                  <td className="py-1 pr-4">{row.source}</td>
                  <td className="py-1 pr-4">{row.plan_tier}</td>
                  <td className="py-1 pr-4">{row.users}</td>
                  <td className="py-1 pr-4">{row.paid_users}</td>
                  <td className="py-1 pr-4">{usd(row.revenue_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}


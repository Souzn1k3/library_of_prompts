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
      <section className="space-y-3">
        <h1 className="text-2xl font-semibold tracking-tight">Growth Operating Dashboard</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          {error ?? "No growth data available yet."}
        </p>
      </section>
    );
  }

  const metrics = dashboard.metrics;

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Growth Operating Dashboard</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Window: {metrics.window_days}d · Updated: {new Date(metrics.computed_at).toLocaleString()}
        </p>
      </header>

      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <article className="rounded-xl border p-3">
          <div className="text-xs uppercase text-[var(--muted-foreground)]">Activation</div>
          <div className="mt-1 text-xl font-semibold">{metric(metrics.activation_rate)}</div>
        </article>
        <article className="rounded-xl border p-3">
          <div className="text-xs uppercase text-[var(--muted-foreground)]">D1 Retention</div>
          <div className="mt-1 text-xl font-semibold">{metric(metrics.d1_retention)}</div>
        </article>
        <article className="rounded-xl border p-3">
          <div className="text-xs uppercase text-[var(--muted-foreground)]">D7 Retention</div>
          <div className="mt-1 text-xl font-semibold">{metric(metrics.d7_retention)}</div>
        </article>
        <article className="rounded-xl border p-3">
          <div className="text-xs uppercase text-[var(--muted-foreground)]">Free → Paid</div>
          <div className="mt-1 text-xl font-semibold">{metric(metrics.free_to_paid_conversion)}</div>
        </article>
        <article className="rounded-xl border p-3">
          <div className="text-xs uppercase text-[var(--muted-foreground)]">Upgrade Intent</div>
          <div className="mt-1 text-xl font-semibold">{metric(metrics.upgrade_intent_rate)}</div>
        </article>
        <article className="rounded-xl border p-3">
          <div className="text-xs uppercase text-[var(--muted-foreground)]">LTV Proxy</div>
          <div className="mt-1 text-xl font-semibold">{metric(metrics.ltv_proxy_usd, "$")}</div>
        </article>
      </div>

      <section className="space-y-2 rounded-xl border p-4">
        <h2 className="text-lg font-semibold">Funnel</h2>
        <div className="grid gap-2 md:grid-cols-5">
          {dashboard.funnel.steps.map((step) => (
            <article key={step.key} className="rounded-lg border p-3">
              <div className="text-xs uppercase text-[var(--muted-foreground)]">{step.label}</div>
              <div className="mt-1 text-lg font-semibold">{step.users}</div>
              <div className="text-xs text-[var(--muted-foreground)]">
                Conv from prev: {metric(step.conversion_from_prev)}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="space-y-2 rounded-xl border p-4">
        <h2 className="text-lg font-semibold">Cohorts</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-[var(--muted-foreground)]">
                <th className="py-1 pr-4">Week</th>
                <th className="py-1 pr-4">Users</th>
                <th className="py-1 pr-4">D1</th>
                <th className="py-1 pr-4">D7</th>
                <th className="py-1 pr-4">Paid 30d</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.cohorts.map((cohort) => (
                <tr key={cohort.cohort_week_start}>
                  <td className="py-1 pr-4">{cohort.cohort_week_start}</td>
                  <td className="py-1 pr-4">{cohort.users}</td>
                  <td className="py-1 pr-4">{metric(cohort.d1_retention)}</td>
                  <td className="py-1 pr-4">
                    {cohort.d7_retention == null ? "n/a" : metric(cohort.d7_retention)}
                  </td>
                  <td className="py-1 pr-4">
                    {cohort.paid_30d_conversion == null ? "n/a" : metric(cohort.paid_30d_conversion)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}


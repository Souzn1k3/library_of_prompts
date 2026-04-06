import { ApiRequestError, fetchGtmDashboard } from "@/lib/api";
import { getServerAccessToken } from "@/lib/server-auth";

function pct(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "n/a";
  }
  return `${value.toFixed(2)}%`;
}

function usd(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "n/a";
  }
  return `$${value.toFixed(2)}`;
}

export default async function GtmPage() {
  const token = await getServerAccessToken();

  let dashboard = null;
  let error: string | null = null;
  try {
    dashboard = await fetchGtmDashboard(token, { windowDays: 30 });
  } catch (cause) {
    if (cause instanceof ApiRequestError) {
      error = `GTM dashboard unavailable (${cause.status})`;
    } else {
      error = "GTM dashboard unavailable";
    }
  }

  if (!dashboard) {
    return (
      <section className="space-y-3">
        <h1 className="text-2xl font-semibold tracking-tight">GTM Engine Dashboard</h1>
        <p className="text-sm text-[var(--muted-foreground)]">{error ?? "No GTM data available yet."}</p>
      </section>
    );
  }

  const h = dashboard.headline;
  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">GTM Engine Dashboard</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Window: {h.window_days}d · Updated: {new Date(h.computed_at).toLocaleString()}
        </p>
      </header>

      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <article className="rounded-xl border p-3"><div className="text-xs text-[var(--muted-foreground)]">Traffic</div><div className="text-xl font-semibold">{h.traffic_sessions}</div></article>
        <article className="rounded-xl border p-3"><div className="text-xs text-[var(--muted-foreground)]">Signups</div><div className="text-xl font-semibold">{h.signups}</div></article>
        <article className="rounded-xl border p-3"><div className="text-xs text-[var(--muted-foreground)]">Paid</div><div className="text-xl font-semibold">{h.paid_users}</div></article>
        <article className="rounded-xl border p-3"><div className="text-xs text-[var(--muted-foreground)]">Revenue</div><div className="text-xl font-semibold">{usd(h.revenue_usd)}</div></article>
        <article className="rounded-xl border p-3"><div className="text-xs text-[var(--muted-foreground)]">Spend</div><div className="text-xl font-semibold">{usd(h.spend_usd)}</div></article>
        <article className="rounded-xl border p-3"><div className="text-xs text-[var(--muted-foreground)]">Blended ROI</div><div className="text-xl font-semibold">{pct(h.blended_roi_percent)}</div></article>
      </div>

      <section className="rounded-xl border p-4 space-y-2">
        <h2 className="text-lg font-semibold">Channel Performance</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-[var(--muted-foreground)]">
                <th className="py-1 pr-4">Source</th>
                <th className="py-1 pr-4">Campaign</th>
                <th className="py-1 pr-4">Traffic</th>
                <th className="py-1 pr-4">Signups</th>
                <th className="py-1 pr-4">Paid</th>
                <th className="py-1 pr-4">Revenue</th>
                <th className="py-1 pr-4">CAC</th>
                <th className="py-1 pr-4">ROI</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.channels.map((row) => (
                <tr key={`${row.source}:${row.campaign ?? "none"}`}>
                  <td className="py-1 pr-4">{row.source}</td>
                  <td className="py-1 pr-4">{row.campaign ?? "—"}</td>
                  <td className="py-1 pr-4">{row.traffic_sessions}</td>
                  <td className="py-1 pr-4">{row.signups}</td>
                  <td className="py-1 pr-4">{row.paid_users}</td>
                  <td className="py-1 pr-4">{usd(row.revenue_usd)}</td>
                  <td className="py-1 pr-4">{usd(row.cac_usd)}</td>
                  <td className="py-1 pr-4">{pct(row.roi_percent)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border p-4 space-y-2">
        <h2 className="text-lg font-semibold">Top Campaigns</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-[var(--muted-foreground)]">
                <th className="py-1 pr-4">Source</th>
                <th className="py-1 pr-4">Campaign</th>
                <th className="py-1 pr-4">Revenue</th>
                <th className="py-1 pr-4">ROI</th>
                <th className="py-1 pr-4">Conversion</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.top_campaigns.map((row) => (
                <tr key={`top:${row.source}:${row.campaign ?? "none"}`}>
                  <td className="py-1 pr-4">{row.source}</td>
                  <td className="py-1 pr-4">{row.campaign ?? "—"}</td>
                  <td className="py-1 pr-4">{usd(row.revenue_usd)}</td>
                  <td className="py-1 pr-4">{pct(row.roi_percent)}</td>
                  <td className="py-1 pr-4">{pct(row.conversion_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border p-4 space-y-2">
        <h2 className="text-lg font-semibold">Top Creatives</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-[var(--muted-foreground)]">
                <th className="py-1 pr-4">Source</th>
                <th className="py-1 pr-4">Campaign</th>
                <th className="py-1 pr-4">Ad ID</th>
                <th className="py-1 pr-4">Creative ID</th>
                <th className="py-1 pr-4">Revenue</th>
                <th className="py-1 pr-4">Conversion</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.top_creatives.map((row) => (
                <tr key={`creative:${row.source}:${row.ad_id ?? "na"}:${row.creative_id ?? "na"}`}>
                  <td className="py-1 pr-4">{row.source}</td>
                  <td className="py-1 pr-4">{row.campaign ?? "—"}</td>
                  <td className="py-1 pr-4">{row.ad_id ?? "—"}</td>
                  <td className="py-1 pr-4">{row.creative_id ?? "—"}</td>
                  <td className="py-1 pr-4">{usd(row.revenue_usd)}</td>
                  <td className="py-1 pr-4">{pct(row.conversion_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border p-4 space-y-2">
        <h2 className="text-lg font-semibold">Scaling Signals</h2>
        <div className="grid gap-2 md:grid-cols-2">
          {dashboard.signals.length ? (
            dashboard.signals.map((signal, index) => (
              <article key={`${signal.signal}:${signal.source}:${signal.campaign ?? "none"}:${index}`} className="rounded-lg border p-3">
                <div className="text-xs text-[var(--muted-foreground)]">{signal.signal}</div>
                <div className="text-sm font-semibold">{signal.source} {signal.campaign ? `· ${signal.campaign}` : ""}</div>
                <div className="text-xs text-[var(--muted-foreground)]">
                  ROI {pct(signal.roi_percent)} · CAC {usd(signal.cac_usd)} · Conv {pct(signal.conversion_rate)}
                </div>
              </article>
            ))
          ) : (
            <p className="text-sm text-[var(--muted-foreground)]">No scale/kill signals in current window.</p>
          )}
        </div>
      </section>
    </section>
  );
}


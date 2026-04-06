import Link from "next/link";

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
      <div className="pv-page-sm">
        <section className="pv-hero px-6 py-7 sm:px-8 sm:py-8">
          <p className="pv-kicker">GTM Engine</p>
          <h1 className="pv-title max-w-4xl text-zinc-950">GTM Engine Dashboard</h1>
          <p className="mt-3 pv-lead max-w-3xl">{error ?? "No GTM data available yet."}</p>
        </section>
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-copy">
            <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Prepare GTM data feed</h2>
            <p className="mt-2 text-sm text-zinc-600">
              This dashboard needs campaign attribution and conversion events to compute ROI.
            </p>
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-3">
            <article className="pv-analytics-card">
              <p className="pv-analytics-label">Attribution</p>
              <p className="mt-2 text-sm text-zinc-700">Use tracked links and consistent campaign naming.</p>
            </article>
            <article className="pv-analytics-card">
              <p className="pv-analytics-label">Volume</p>
              <p className="mt-2 text-sm text-zinc-700">Generate enough traffic and signups to detect winners.</p>
            </article>
            <article className="pv-analytics-card">
              <p className="pv-analytics-label">Optimization</p>
              <p className="mt-2 text-sm text-zinc-700">Revisit this dashboard to scale high-ROI sources.</p>
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
        <p className="pv-kicker">GTM Engine</p>
        <h1 className="pv-title max-w-4xl text-zinc-950">GTM Engine Dashboard</h1>
        <p className="mt-3 pv-lead max-w-3xl">
          Channel-level acquisition performance, spend efficiency, and scaling signals.
        </p>
        <p className="mt-3 text-sm font-medium text-zinc-600">
          Window: {h.window_days}d · Updated: {new Date(h.computed_at).toLocaleString()}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href="/growth" className="pv-nav-pill !min-h-0 !px-3 !py-1.5 !text-xs">
            Growth
          </Link>
          <Link href="/revenue" className="pv-nav-pill !min-h-0 !px-3 !py-1.5 !text-xs">
            Revenue
          </Link>
          <Link href="/gtm" className="pv-nav-pill pv-nav-pill-active !min-h-0 !px-3 !py-1.5 !text-xs">
            GTM
          </Link>
        </div>
      </section>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        <article className="pv-analytics-card"><div className="pv-analytics-label">Traffic</div><div className="pv-analytics-value">{h.traffic_sessions}</div></article>
        <article className="pv-analytics-card"><div className="pv-analytics-label">Signups</div><div className="pv-analytics-value">{h.signups}</div></article>
        <article className="pv-analytics-card"><div className="pv-analytics-label">Paid</div><div className="pv-analytics-value">{h.paid_users}</div></article>
        <article className="pv-analytics-card"><div className="pv-analytics-label">Revenue</div><div className="pv-analytics-value">{usd(h.revenue_usd)}</div></article>
        <article className="pv-analytics-card"><div className="pv-analytics-label">Spend</div><div className="pv-analytics-value">{usd(h.spend_usd)}</div></article>
        <article className="pv-analytics-card"><div className="pv-analytics-label">Blended ROI</div><div className="pv-analytics-value">{pct(h.blended_roi_percent)}</div></article>
      </div>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Channel Performance</h2>
        </div>
        <div className="pv-analytics-table-wrap mt-5">
          <table className="pv-analytics-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Campaign</th>
                <th>Traffic</th>
                <th>Signups</th>
                <th>Paid</th>
                <th>Revenue</th>
                <th>CAC</th>
                <th>ROI</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.channels.map((row) => (
                <tr key={`${row.source}:${row.campaign ?? "none"}`}>
                  <td>{row.source}</td>
                  <td>{row.campaign ?? "—"}</td>
                  <td>{row.traffic_sessions}</td>
                  <td>{row.signups}</td>
                  <td>{row.paid_users}</td>
                  <td>{usd(row.revenue_usd)}</td>
                  <td>{usd(row.cac_usd)}</td>
                  <td>{pct(row.roi_percent)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Top Campaigns</h2>
        </div>
        <div className="pv-analytics-table-wrap mt-5">
          <table className="pv-analytics-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Campaign</th>
                <th>Revenue</th>
                <th>ROI</th>
                <th>Conversion</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.top_campaigns.map((row) => (
                <tr key={`top:${row.source}:${row.campaign ?? "none"}`}>
                  <td>{row.source}</td>
                  <td>{row.campaign ?? "—"}</td>
                  <td>{usd(row.revenue_usd)}</td>
                  <td>{pct(row.roi_percent)}</td>
                  <td>{pct(row.conversion_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Top Creatives</h2>
        </div>
        <div className="pv-analytics-table-wrap mt-5">
          <table className="pv-analytics-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Campaign</th>
                <th>Ad ID</th>
                <th>Creative ID</th>
                <th>Revenue</th>
                <th>Conversion</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.top_creatives.map((row) => (
                <tr key={`creative:${row.source}:${row.ad_id ?? "na"}:${row.creative_id ?? "na"}`}>
                  <td>{row.source}</td>
                  <td>{row.campaign ?? "—"}</td>
                  <td>{row.ad_id ?? "—"}</td>
                  <td>{row.creative_id ?? "—"}</td>
                  <td>{usd(row.revenue_usd)}</td>
                  <td>{pct(row.conversion_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Scaling Signals</h2>
        </div>
        <div className="mt-5 grid gap-2 md:grid-cols-2">
          {dashboard.signals.length ? (
            dashboard.signals.map((signal, index) => (
              <article key={`${signal.signal}:${signal.source}:${signal.campaign ?? "none"}:${index}`} className="pv-analytics-card">
                <div className="pv-analytics-label">{signal.signal}</div>
                <div className="mt-2 text-sm font-semibold text-zinc-900">{signal.source} {signal.campaign ? `· ${signal.campaign}` : ""}</div>
                <div className="pv-analytics-meta">
                  ROI {pct(signal.roi_percent)} · CAC {usd(signal.cac_usd)} · Conv {pct(signal.conversion_rate)}
                </div>
              </article>
            ))
          ) : (
            <p className="text-sm text-zinc-600">No scale/kill signals in current window.</p>
          )}
        </div>
      </section>
    </div>
  );
}

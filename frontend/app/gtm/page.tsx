import { ApiRequestError, fetchGtmDashboard } from "@/lib/api";
import { getServerAccessToken } from "@/lib/server-auth";
import { GtmSpendForm } from "@/components/analytics/GtmSpendForm";
import {
  OpsDashboardEmptyState,
  OpsDashboardHero,
  OpsTableEmptyRow,
  OpsTableSection,
} from "@/components/analytics/OpsDashboardShell";

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
      <OpsDashboardEmptyState
        kicker="GTM Engine"
        title="GTM Engine Dashboard"
        message={error ?? "No GTM data available yet."}
        steps={[
          { label: "1. Attribution", body: "Use tracked links and consistent campaign naming." },
          { label: "2. Volume", body: "Generate enough traffic and signups to detect winners." },
          { label: "3. Optimization", body: "Revisit this dashboard to scale high-ROI sources." },
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
        kicker="GTM Engine"
        title="GTM Engine Dashboard"
        subtitle="Channel-level acquisition performance, spend efficiency, and scaling signals."
        windowDays={h.window_days}
        updatedAt={h.computed_at}
        activeTab="gtm"
      />

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-7">
        <article className="pv-analytics-card"><div className="pv-analytics-label">Traffic</div><div className="pv-analytics-value">{h.traffic_sessions}</div></article>
        <article className="pv-analytics-card"><div className="pv-analytics-label">Signups</div><div className="pv-analytics-value">{h.signups}</div></article>
        <article className="pv-analytics-card"><div className="pv-analytics-label">Activated</div><div className="pv-analytics-value">{h.activated_users}</div></article>
        <article className="pv-analytics-card"><div className="pv-analytics-label">Paid</div><div className="pv-analytics-value">{h.paid_users}</div></article>
        <article className="pv-analytics-card"><div className="pv-analytics-label">Revenue</div><div className="pv-analytics-value">{usd(h.revenue_usd)}</div></article>
        <article className="pv-analytics-card"><div className="pv-analytics-label">Spend</div><div className="pv-analytics-value">{usd(h.spend_usd)}</div></article>
        <article className="pv-analytics-card"><div className="pv-analytics-label">Blended CAC</div><div className="pv-analytics-value">{usd(h.blended_cac_usd)}</div></article>
        <article className="pv-analytics-card"><div className="pv-analytics-label">Blended ROI</div><div className="pv-analytics-value">{pct(h.blended_roi_percent)}</div></article>
      </div>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Cost Ingestion</h2>
          <p className="mt-2 text-sm text-zinc-600">
            Add or update channel spend directly from this dashboard to keep CAC and ROI live.
          </p>
        </div>
        <div className="mt-5">
          <GtmSpendForm />
        </div>
      </section>

      <OpsTableSection title="Channel Performance" subtitle="Acquisition, activation, spend and monetization at source/campaign level.">
        <div className="pv-analytics-table-wrap">
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
              {dashboard.channels.length ? (
                dashboard.channels.map((row) => (
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
                ))
              ) : (
                <OpsTableEmptyRow colSpan={8} label="No channel performance rows in this window." />
              )}
            </tbody>
          </table>
        </div>
      </OpsTableSection>

      <OpsTableSection title="Funnel By Source" subtitle="How each source moves from acquisition to paid conversion.">
        <div className="pv-analytics-table-wrap">
          <table className="pv-analytics-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Acquired</th>
                <th>Signed up</th>
                <th>Activated</th>
                <th>Paid</th>
                <th>Acq→Signup</th>
                <th>Signup→Activated</th>
                <th>Activated→Paid</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.funnel_by_source.length ? (
                dashboard.funnel_by_source.map((row) => (
                  <tr key={`funnel:${row.source}`}>
                    <td>{row.source}</td>
                    <td>{row.acquired}</td>
                    <td>{row.signed_up}</td>
                    <td>{row.activated}</td>
                    <td>{row.paid}</td>
                    <td>{pct(row.acquired_to_signup)}</td>
                    <td>{pct(row.signup_to_activated)}</td>
                    <td>{pct(row.activated_to_paid)}</td>
                  </tr>
                ))
              ) : (
                <OpsTableEmptyRow colSpan={8} label="No source funnel rows available." />
              )}
            </tbody>
          </table>
        </div>
      </OpsTableSection>

      <OpsTableSection title="Top Campaigns" subtitle="Campaigns ranked by revenue and efficiency.">
        <div className="pv-analytics-table-wrap">
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
              {dashboard.top_campaigns.length ? (
                dashboard.top_campaigns.map((row) => (
                  <tr key={`top:${row.source}:${row.campaign ?? "none"}`}>
                    <td>{row.source}</td>
                    <td>{row.campaign ?? "—"}</td>
                    <td>{usd(row.revenue_usd)}</td>
                    <td>{pct(row.roi_percent)}</td>
                    <td>{pct(row.conversion_rate)}</td>
                  </tr>
                ))
              ) : (
                <OpsTableEmptyRow colSpan={5} label="No campaign-level rows captured." />
              )}
            </tbody>
          </table>
        </div>
      </OpsTableSection>

      <OpsTableSection title="Top Creatives" subtitle="Ad-level and creative-level monetization signals.">
        <div className="pv-analytics-table-wrap">
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
              {dashboard.top_creatives.length ? (
                dashboard.top_creatives.map((row) => (
                  <tr key={`creative:${row.source}:${row.ad_id ?? "na"}:${row.creative_id ?? "na"}`}>
                    <td>{row.source}</td>
                    <td>{row.campaign ?? "—"}</td>
                    <td>{row.ad_id ?? "—"}</td>
                    <td>{row.creative_id ?? "—"}</td>
                    <td>{usd(row.revenue_usd)}</td>
                    <td>{pct(row.conversion_rate)}</td>
                  </tr>
                ))
              ) : (
                <OpsTableEmptyRow colSpan={6} label="No creative-level rows available yet." />
              )}
            </tbody>
          </table>
        </div>
      </OpsTableSection>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Scaling Signals</h2>
          <p className="mt-2 text-sm text-zinc-600">
            Auto-generated scale/kill decisions from spend, ROI, and conversion quality.
          </p>
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

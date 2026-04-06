"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { ApiRequestError } from "@/lib/api";
import { upsertGtmChannelSpend } from "@/lib/client-api";

type SpendFormState = {
  spend_day: string;
  source: string;
  medium: string;
  campaign: string;
  ad_id: string;
  creative_id: string;
  cost_usd: string;
  clicks: string;
  impressions: string;
  dedupe_key: string;
};

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export function GtmSpendForm() {
  const router = useRouter();
  const [state, setState] = useState<SpendFormState>({
    spend_day: todayIsoDate(),
    source: "google",
    medium: "ads",
    campaign: "",
    ad_id: "",
    creative_id: "",
    cost_usd: "",
    clicks: "",
    impressions: "",
    dedupe_key: "",
  });
  const [submitPending, setSubmitPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = useMemo(() => {
    const cost = Number(state.cost_usd);
    return state.spend_day.trim().length > 0 && state.source.trim().length > 0 && Number.isFinite(cost) && cost >= 0;
  }, [state.cost_usd, state.source, state.spend_day]);

  function updateField<K extends keyof SpendFormState>(field: K, value: SpendFormState[K]) {
    setState((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }
    setSubmitPending(true);
    setMessage(null);
    setError(null);
    try {
      const payload = await upsertGtmChannelSpend({
        spend_day: state.spend_day,
        source: state.source.trim(),
        medium: state.medium.trim() || null,
        campaign: state.campaign.trim() || null,
        ad_id: state.ad_id.trim() || null,
        creative_id: state.creative_id.trim() || null,
        cost_usd: Number(state.cost_usd),
        clicks: Number(state.clicks || 0),
        impressions: Number(state.impressions || 0),
        dedupe_key: state.dedupe_key.trim() || null,
      });
      setMessage(
        `Spend saved: ${payload.source} ${payload.campaign ?? "—"} · $${payload.cost_usd.toFixed(2)} (${payload.spend_day})`,
      );
      router.refresh();
    } catch (cause) {
      if (cause instanceof ApiRequestError && cause.status === 403) {
        setError("Only admin users can submit GTM spend data.");
      } else if (cause instanceof Error) {
        setError(cause.message);
      } else {
        setError("Could not save spend data.");
      }
    } finally {
      setSubmitPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="pv-analytics-form-grid">
      <div className="pv-field">
        <label className="pv-label" htmlFor="gtm-spend-day">Spend day</label>
        <input
          id="gtm-spend-day"
          type="date"
          value={state.spend_day}
          onChange={(event) => updateField("spend_day", event.target.value)}
          className="pv-input"
          required
        />
      </div>
      <div className="pv-field">
        <label className="pv-label" htmlFor="gtm-source">Source</label>
        <input
          id="gtm-source"
          type="text"
          value={state.source}
          onChange={(event) => updateField("source", event.target.value)}
          className="pv-input"
          placeholder="google"
          required
        />
      </div>
      <div className="pv-field">
        <label className="pv-label" htmlFor="gtm-medium">Medium</label>
        <input
          id="gtm-medium"
          type="text"
          value={state.medium}
          onChange={(event) => updateField("medium", event.target.value)}
          className="pv-input"
          placeholder="ads"
        />
      </div>
      <div className="pv-field">
        <label className="pv-label" htmlFor="gtm-campaign">Campaign</label>
        <input
          id="gtm-campaign"
          type="text"
          value={state.campaign}
          onChange={(event) => updateField("campaign", event.target.value)}
          className="pv-input"
          placeholder="q2_launch"
        />
      </div>
      <div className="pv-field">
        <label className="pv-label" htmlFor="gtm-cost">Cost (USD)</label>
        <input
          id="gtm-cost"
          type="number"
          inputMode="decimal"
          step="0.01"
          min="0"
          value={state.cost_usd}
          onChange={(event) => updateField("cost_usd", event.target.value)}
          className="pv-input"
          placeholder="120.00"
          required
        />
      </div>
      <div className="pv-field">
        <label className="pv-label" htmlFor="gtm-clicks">Clicks</label>
        <input
          id="gtm-clicks"
          type="number"
          inputMode="numeric"
          min="0"
          step="1"
          value={state.clicks}
          onChange={(event) => updateField("clicks", event.target.value)}
          className="pv-input"
          placeholder="0"
        />
      </div>
      <div className="pv-field">
        <label className="pv-label" htmlFor="gtm-impressions">Impressions</label>
        <input
          id="gtm-impressions"
          type="number"
          inputMode="numeric"
          min="0"
          step="1"
          value={state.impressions}
          onChange={(event) => updateField("impressions", event.target.value)}
          className="pv-input"
          placeholder="0"
        />
      </div>
      <div className="pv-field">
        <label className="pv-label" htmlFor="gtm-ad-id">Ad ID</label>
        <input
          id="gtm-ad-id"
          type="text"
          value={state.ad_id}
          onChange={(event) => updateField("ad_id", event.target.value)}
          className="pv-input"
          placeholder="ad_44"
        />
      </div>
      <div className="pv-field">
        <label className="pv-label" htmlFor="gtm-creative-id">Creative ID</label>
        <input
          id="gtm-creative-id"
          type="text"
          value={state.creative_id}
          onChange={(event) => updateField("creative_id", event.target.value)}
          className="pv-input"
          placeholder="creative_2"
        />
      </div>
      <div className="pv-field sm:col-span-2 xl:col-span-3">
        <label className="pv-label" htmlFor="gtm-dedupe">Dedupe key (optional)</label>
        <input
          id="gtm-dedupe"
          type="text"
          value={state.dedupe_key}
          onChange={(event) => updateField("dedupe_key", event.target.value)}
          className="pv-input"
          placeholder="google-q2-launch-2026-04-06"
        />
      </div>
      <div className="sm:col-span-2 xl:col-span-3">
        <button
          type="submit"
          className="pv-button-primary !w-auto"
          disabled={!canSubmit || submitPending}
        >
          {submitPending ? "Saving spend..." : "Save spend entry"}
        </button>
      </div>
      {message ? <p className="sm:col-span-2 xl:col-span-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="sm:col-span-2 xl:col-span-3 text-sm text-rose-700">{error}</p> : null}
    </form>
  );
}

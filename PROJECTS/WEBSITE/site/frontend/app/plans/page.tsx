import type { Metadata } from "next";
import Link from "next/link";

import { ApiRequestError, fetchPlans } from "@/lib/api";

export const metadata: Metadata = {
  title: "Plans",
  description: "Subscription tiers for Prompts Vault (API-driven).",
};

export const revalidate = 300;

export default async function PlansPage() {
  let plans: Awaited<ReturnType<typeof fetchPlans>> = [];
  let error: string | null = null;
  try {
    plans = await fetchPlans();
  } catch (e) {
    error = e instanceof ApiRequestError ? e.message : "Could not load plans.";
  }

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Plans</h1>
        <p className="max-w-2xl text-sm text-zinc-600">
          Tiers are enforced by the API (<code className="font-mono text-xs">plan_tier</code> on the
          user). Checkout is a stub until Stripe is wired; admins can adjust tiers via{" "}
          <code className="font-mono text-xs">PATCH /api/v1/admin/users/&#123;id&#125;/tier</code>.
        </p>
      </header>

      {error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        {plans.map((p) => (
          <div
            key={p.tier}
            className="rounded-lg border border-zinc-200 bg-white p-5 shadow-card"
          >
            <div className="flex items-baseline justify-between gap-2">
              <h2 className="text-lg font-semibold text-zinc-900">{p.name}</h2>
              <p className="text-sm text-zinc-600">
                ${String(p.price_usd_month)}
                <span className="text-zinc-400">/mo</span>
              </p>
            </div>
            <p className="mt-1 text-xs uppercase tracking-wide text-zinc-500">{p.tier}</p>
            <ul className="mt-4 list-inside list-disc space-y-1 text-sm text-zinc-700">
              {p.features.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <p className="text-sm text-zinc-600">
        <Link href="/signup" className="font-medium text-zinc-900 underline">
          Create an account
        </Link>{" "}
        to start on Free, then upgrade when billing is connected.
      </p>
    </div>
  );
}

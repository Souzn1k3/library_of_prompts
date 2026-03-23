import type { Metadata } from "next";
import Link from "next/link";

import { T } from "@/components/i18n/T";
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
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          <T k="plans.title" />
        </h1>
        <p className="max-w-2xl text-sm text-zinc-600">
          <T k="plans.subtitle" />
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
                <span className="text-zinc-400">
                  <T k="plans.perMonth" />
                </span>
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
          <T k="plans.createAccount" />
        </Link>{" "}
        <T k="plans.createAccountSuffix" />
      </p>
    </div>
  );
}

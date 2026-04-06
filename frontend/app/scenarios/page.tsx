import Link from "next/link";

import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { RouteCard } from "@/components/navigation/RouteCard";
import { fetchScenarioHomeAggregate } from "@/lib/api";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";
import type { PromptListItem } from "@/lib/types";

import { ScenariosHubClient } from "./ScenariosHubClient";

export default async function ScenariosPage() {
  const [accessToken, language] = await Promise.all([
    getServerAccessToken(),
    getServerLanguage(),
  ]);

  const aggregate = await fetchScenarioHomeAggregate({
    accessToken,
    language,
    limit: 12,
  }).catch(() => null);

  const prompts = dedupePrompts([
    ...(aggregate?.featured ?? []),
    ...(aggregate?.recommended ?? []),
    ...(aggregate?.retention ?? []),
  ]).slice(0, 24);

  return (
    <div className="pv-page">
      <PageIntro
        breadcrumbs={[
          { label: <T k="brand.name" />, href: "/" },
          { label: <T k="home.scenarioTryTitle" /> },
        ]}
        eyebrow={<T k="home.scenarioTryKicker" />}
        title={<T k="home.scenarioTryTitle" />}
        description={<T k="home.scenarioTrySubtitle" />}
        actions={(
          <>
            <Link href="/#home-workbench" className="pv-button-primary">
              Run from Workbench
            </Link>
            <Link href="/catalog" className="pv-button-secondary">
              <T k="home.explorePrompts" />
            </Link>
            <Link href="/scenarios/marketplace" className="pv-button-secondary">
              Scenario Marketplace
            </Link>
          </>
        )}
      />

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Choose your next scenario flow</h2>
          <p className="mt-2 text-sm text-zinc-600">Start from curated prompts, creator blueprints, or your workspace experiments.</p>
        </div>

        <div className="mt-6 grid gap-3 lg:grid-cols-3">
          <RouteCard
            eyebrow="Catalog"
            title="Browse proven scenarios"
            description="Filter by use case, output type, and quality score to find the fastest path."
            href="/catalog"
            actionLabel="Open catalog"
          />
          <RouteCard
            eyebrow="Marketplace"
            title="Fork creator blueprints"
            description="Reuse top scenario templates and adapt them in your own environment."
            href="/scenarios/marketplace"
            actionLabel="Open marketplace"
          />
          <RouteCard
            eyebrow="Workspace"
            title="Track runs and results"
            description="Go to dashboard and continue unfinished tasks with clear next actions."
            href="/dashboard"
            actionLabel="Open dashboard"
          />
        </div>
      </section>

      <ScenariosHubClient
        prompts={prompts}
        nextSteps={aggregate?.next_steps ?? []}
        loopHints={aggregate?.loop_hints ?? null}
        isAuthenticated={Boolean(accessToken)}
      />
    </div>
  );
}

function dedupePrompts(prompts: PromptListItem[]) {
  const map = new Map<string, PromptListItem>();
  for (const prompt of prompts) {
    map.set(prompt.id, prompt);
  }
  return [...map.values()];
}

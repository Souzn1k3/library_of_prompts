import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ContributorBadge } from "@/components/ContributorBadge";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import { ApiRequestError, fetchContributorProfile, fetchPrompts } from "@/lib/api";
import { getTranslation } from "@/lib/i18n";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();
  try {
    const profile = await fetchContributorProfile(slug, accessToken, language);
    return buildPageMetadata({
      title: `${profile.display_name} (@${profile.slug})`,
      description: `Contributor profile, reputation score ${profile.reputation_score}, approved prompts ${profile.stats.approved_submissions}.`,
      path: `/contributors/${profile.slug}`,
    });
  } catch {
    return buildPageMetadata({
      title: getTranslation(language, "contributors.metadataFallbackTitle"),
      description: getTranslation(language, "contributors.metadataFallbackDescription"),
      path: `/contributors/${slug}`,
    });
  }
}

export default async function ContributorProfilePage(props: Props) {
  const { slug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  try {
    const [profile, prompts] = await Promise.all([
      fetchContributorProfile(slug, accessToken, language),
      fetchPrompts({
        contributor: slug,
        sort: "relevance",
        limit: 12,
        accessToken,
        language,
      }),
    ]);

    const approvalRate = profile.stats.approved_submissions + profile.stats.rejected_submissions > 0
      ? Math.round(
          (profile.stats.approved_submissions /
            (profile.stats.approved_submissions + profile.stats.rejected_submissions)) *
            100,
        )
      : 0;

    return (
      <div className="space-y-8">
        <JsonLd
          id={`ld-contributor-${profile.slug}`}
          data={{
            "@context": "https://schema.org",
            "@type": "Person",
            name: profile.display_name,
            url: absoluteUrl(`/contributors/${profile.slug}`),
            description: profile.bio ?? `${profile.display_name} contributor profile`,
          }}
        />

        <header className="space-y-3">
          <Link href="/catalog" className="text-xs font-medium text-zinc-500 transition hover:text-zinc-800">
            ← {getTranslation(language, "contributors.backToCatalog")}
          </Link>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">{profile.display_name}</h1>
              <p className="mt-1 text-sm text-zinc-600">@{profile.slug}</p>
            </div>
            <ContributorBadge tier={profile.reputation_tier} />
          </div>
          {profile.bio ? <p className="max-w-2xl text-sm text-zinc-700">{profile.bio}</p> : null}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label={getTranslation(language, "contributors.reputationScore")} value={profile.reputation_score} />
            <StatCard label={getTranslation(language, "contributors.approvalRate")} value={`${approvalRate}%`} />
            <StatCard
              label={getTranslation(language, "contributors.approvedPrompts")}
              value={profile.stats.approved_submissions}
            />
            <StatCard label={getTranslation(language, "contributors.rejectionRate")} value={`${profile.stats.rejection_rate}%`} />
            <StatCard label={getTranslation(language, "contributors.totalSaves")} value={profile.stats.total_saves} />
            <StatCard label={getTranslation(language, "contributors.totalCopies")} value={profile.stats.total_copies} />
            <StatCard
              label={getTranslation(language, "contributors.missionSuccesses")}
              value={profile.stats.mission_success_count}
            />
            <StatCard label={getTranslation(language, "contributors.avgQuality")} value={profile.stats.average_prompt_quality} />
          </div>
        </header>

        <section className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
          <h2 className="text-sm font-semibold text-zinc-900">
            {getTranslation(language, "contributors.howTiersEarned")}
          </h2>
          <p className="mt-2 text-xs text-zinc-600">
            {getTranslation(language, "contributors.howTiersBody")}
          </p>
          <ul className="mt-3 grid gap-2 text-xs text-zinc-700 sm:grid-cols-3">
            <li className="rounded border border-zinc-200 bg-white p-2">
              {getTranslation(language, "contributors.tierNew")}
            </li>
            <li className="rounded border border-zinc-200 bg-white p-2">
              {getTranslation(language, "contributors.tierVerified")}
            </li>
            <li className="rounded border border-zinc-200 bg-white p-2">
              {getTranslation(language, "contributors.tierTop")}
            </li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
            {getTranslation(language, "contributors.publishedPrompts")}
          </h2>
          {prompts.length === 0 ? (
            <p className="text-sm text-zinc-500">{getTranslation(language, "contributors.noPublished")}</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {prompts.map((prompt) => (
                <PromptCard key={prompt.id} prompt={prompt} />
              ))}
            </div>
          )}
        </section>
      </div>
    );
  } catch (e) {
    if (e instanceof ApiRequestError && e.status === 404) {
      notFound();
    }
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        {getTranslation(language, "contributors.loadFailed")}
      </div>
    );
  }
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-zinc-200 bg-white p-3">
      <p className="text-xs text-zinc-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-zinc-900">{value}</p>
    </div>
  );
}

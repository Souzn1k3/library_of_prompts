import Link from "next/link";

import { ContributorBadge } from "@/components/ContributorBadge";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import { formatTranslation, getTranslation, type Language } from "@/lib/i18n";
import { absoluteUrl } from "@/lib/seo";

import type { ContributorPageData } from "./contributor-page-data";

type ContributorProfileViewProps = {
  language: Language;
  data: ContributorPageData;
};

export function ContributorProfileView({ language, data }: ContributorProfileViewProps) {
  const { profile, prompts, reviewSort, approvalRate } = data;

  return (
    <div className="space-y-8">
      <JsonLd
        id={`ld-contributor-${profile.slug}`}
        data={{
          "@context": "https://schema.org",
          "@type": "Person",
          name: profile.display_name,
          url: absoluteUrl(`/contributors/${profile.slug}`),
          description:
            profile.bio ??
            formatTranslation(language, "contributors.profileDescriptionFallback", {
              name: profile.display_name,
            }),
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
            label={getTranslation(language, "contributors.rating")}
            value={profile.rating_display ? `${profile.rating_display}/5` : getTranslation(language, "contributors.ratingNew")}
          />
          <StatCard label={getTranslation(language, "contributors.reviews")} value={profile.review_count ?? 0} />
          <StatCard
            label={getTranslation(language, "contributors.approvedPrompts")}
            value={profile.stats.approved_submissions}
          />
          <StatCard label={getTranslation(language, "contributors.soldPaidPrompts")} value={profile.sold_prompts_count ?? 0} />
          <StatCard label={getTranslation(language, "contributors.purchasesServed")} value={profile.purchases_count ?? 0} />
          <StatCard label={getTranslation(language, "contributors.revenueRub")} value={profile.seller_revenue_rub ?? 0} />
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

      {profile.trust_indicators?.length ? (
        <section className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
          <h2 className="text-sm font-semibold text-zinc-900">
            {getTranslation(language, "contributors.trustSignals")}
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {profile.trust_indicators.map((indicator) => (
              <span key={indicator.key} className="pv-chip">
                {indicator.key.replaceAll("_", " ")}
              </span>
            ))}
          </div>
        </section>
      ) : null}

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

      <section className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-zinc-900">
              {getTranslation(language, "contributors.marketplaceReviews")}
            </h2>
            <p className="mt-1 text-xs text-zinc-600">
              {getTranslation(language, "contributors.marketplaceReviewsBody")}
            </p>
          </div>
          <div className="flex gap-2 text-sm">
            <Link
              href={`/contributors/${encodeURIComponent(profile.slug)}?review_sort=new`}
              className={reviewSort === "new" ? "pv-button-secondary" : "pv-chip"}
            >
              {getTranslation(language, "contributors.sortNew")}
            </Link>
            <Link
              href={`/contributors/${encodeURIComponent(profile.slug)}?review_sort=best`}
              className={reviewSort === "best" ? "pv-button-secondary" : "pv-chip"}
            >
              {getTranslation(language, "contributors.sortBest")}
            </Link>
          </div>
        </div>
        {profile.recent_reviews?.length ? (
          <div className="mt-4 space-y-3">
            {profile.recent_reviews.map((review) => (
              <div key={review.id} className="rounded-md border border-zinc-200 bg-white p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-zinc-900">{review.author_display_name}</p>
                  <p className="text-sm text-zinc-600">{review.rating}/5</p>
                </div>
                <p className="mt-1 text-xs text-zinc-500">{review.prompt_title}</p>
                {review.text ? <p className="mt-3 text-sm text-zinc-700">{review.text}</p> : null}
                <p className="mt-3 text-xs text-zinc-500">{new Date(review.created_at).toLocaleDateString()}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm text-zinc-500">{getTranslation(language, "contributors.noVerifiedReviews")}</p>
        )}
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
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-zinc-200 bg-white p-3">
      <p className="text-xs text-zinc-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-zinc-900">{value}</p>
    </div>
  );
}

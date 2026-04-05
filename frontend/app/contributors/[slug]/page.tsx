import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { ApiRequestError, fetchContributorProfile } from "@/lib/api";
import { isOfficialTeamContributor } from "@/lib/contributors";
import { formatTranslation, getTranslation, type Language } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

import { ContributorProfileView } from "./ContributorProfileView";
import { loadContributorPageData, parseContributorReviewSort } from "./contributor-page-data";

type Props = {
  params: Promise<{ slug: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function buildContributorFallbackMetadata(slug: string, language: Language): Metadata {
  return buildPageMetadata({
    title: getTranslation(language, "contributors.metadataFallbackTitle"),
    description: getTranslation(language, "contributors.metadataFallbackDescription"),
    path: `/contributors/${slug}`,
  });
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  const language = await getServerLanguage();
  if (isOfficialTeamContributor(slug)) {
    return buildContributorFallbackMetadata(slug, language);
  }
  const accessToken = await getServerAccessToken();
  try {
    const profile = await fetchContributorProfile(slug, { accessToken, language });
    return buildPageMetadata({
      title: `${profile.display_name} (@${profile.slug})`,
      description: formatTranslation(language, "contributors.metaDescription", {
        score: profile.reputation_score,
        approved: profile.stats.approved_submissions,
      }),
      path: `/contributors/${profile.slug}`,
    });
  } catch {
    return buildContributorFallbackMetadata(slug, language);
  }
}

export default async function ContributorProfilePage(props: Props) {
  const { slug } = await props.params;
  if (isOfficialTeamContributor(slug)) {
    notFound();
  }
  const searchParams = (await props.searchParams) ?? {};
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();
  const reviewSort = parseContributorReviewSort(searchParams);

  try {
    const data = await loadContributorPageData({
      slug,
      accessToken,
      language,
      reviewSort,
    });
    return <ContributorProfileView language={language} data={data} />;
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

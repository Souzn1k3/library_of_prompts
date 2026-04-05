import { fetchContributorProfile, fetchPrompts } from "@/lib/api";
import type { Language } from "@/lib/i18n";
import type { ContributorProfile, PromptListItem, ReviewSort } from "@/lib/types";

export type ContributorReviewSort = ReviewSort;

export type ContributorPageData = {
  profile: ContributorProfile;
  prompts: PromptListItem[];
  reviewSort: ContributorReviewSort;
  approvalRate: number;
};

export function parseContributorReviewSort(
  searchParams: Record<string, string | string[] | undefined>,
): ContributorReviewSort {
  return typeof searchParams.review_sort === "string" && searchParams.review_sort === "best" ? "best" : "new";
}

function calculateApprovalRate(profile: ContributorProfile): number {
  const approved = profile.stats.approved_submissions;
  const rejected = profile.stats.rejected_submissions;
  return approved + rejected > 0
    ? Math.round((approved / (approved + rejected)) * 100)
    : 0;
}

export async function loadContributorPageData({
  slug,
  accessToken,
  language,
  reviewSort,
}: {
  slug: string;
  accessToken: string | null | undefined;
  language: Language;
  reviewSort: ContributorReviewSort;
}): Promise<ContributorPageData> {
  const [profile, prompts] = await Promise.all([
    fetchContributorProfile(slug, {
      accessToken,
      language,
      review_sort: reviewSort,
      review_limit: 8,
    }),
    fetchPrompts({
      contributor: slug,
      sort: "relevance",
      limit: 12,
      accessToken,
      language,
    }),
  ]);

  return {
    profile,
    prompts,
    reviewSort,
    approvalRate: calculateApprovalRate(profile),
  };
}

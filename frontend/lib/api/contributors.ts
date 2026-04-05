import { API_ENDPOINTS, apiPath } from "../constants/api";
import { withQuery } from "../http";
import type { ContributorProfile, ContributorTopItem, ReviewSort } from "../types";
import type { Language } from "../i18n";
import { apiFetch } from "./transport";

export async function fetchTopContributors(
  params?: {
    limit?: number;
    accessToken?: string | null;
    language?: Language | string | null;
  },
): Promise<ContributorTopItem[]> {
  return apiFetch<ContributorTopItem[]>(withQuery(API_ENDPOINTS.contributorsTop, { limit: params?.limit }), {
    accessToken: params?.accessToken,
    language: params?.language,
  });
}

export async function fetchContributorProfile(
  slug: string,
  params?: {
    review_sort?: ReviewSort;
    review_limit?: number;
    accessToken?: string | null;
    language?: Language | string | null;
  },
): Promise<ContributorProfile> {
  return apiFetch<ContributorProfile>(withQuery(apiPath.contributorBySlug(slug), {
    review_sort: params?.review_sort,
    review_limit: params?.review_limit,
  }), {
    accessToken: params?.accessToken,
    language: params?.language,
  });
}

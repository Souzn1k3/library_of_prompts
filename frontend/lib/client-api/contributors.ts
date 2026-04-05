import { API_ENDPOINTS, apiPath } from "../constants/api";
import { withQuery } from "../http";
import type { ContributorProfile, ContributorTopItem } from "../types";
import { optionalAuthJsonFetch } from "./transport";

export async function fetchTopContributors(limit = 12): Promise<ContributorTopItem[]> {
  return optionalAuthJsonFetch<ContributorTopItem[]>(withQuery(API_ENDPOINTS.contributorsTop, { limit }));
}

export async function fetchContributorProfile(slug: string): Promise<ContributorProfile> {
  return optionalAuthJsonFetch<ContributorProfile>(
    apiPath.contributorBySlug(slug),
  );
}

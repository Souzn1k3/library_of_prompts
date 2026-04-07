import { API_ENDPOINTS, apiPath } from "../constants/api";
import type { Language } from "../i18n";
import type { MissionCurrentRead, MissionListRead, MissionRead } from "../types";
import { apiFetch } from "./transport";

export async function fetchMissions(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<MissionListRead> {
  return apiFetch<MissionListRead>(API_ENDPOINTS.missions, {
    accessToken,
    language,
    cache: "no-store",
  });
}

export async function fetchCurrentMission(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<MissionCurrentRead> {
  return apiFetch<MissionCurrentRead>(API_ENDPOINTS.missionsCurrent, {
    accessToken,
    language,
    cache: "no-store",
  });
}

export async function fetchMissionBySlug(
  slug: string,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<MissionRead> {
  return apiFetch<MissionRead>(apiPath.missionBySlug(slug), {
    accessToken,
    language,
    cache: "no-store",
  });
}

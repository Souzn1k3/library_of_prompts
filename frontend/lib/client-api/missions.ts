import { API_ENDPOINTS, apiPath } from "../constants/api";
import type { MissionCurrentRead, MissionListRead, MissionRead } from "../types";
import { authFetch } from "./transport";

export async function fetchCurrentMission(): Promise<MissionCurrentRead> {
  return authFetch<MissionCurrentRead>(API_ENDPOINTS.missionsCurrent);
}

export async function fetchMissions(): Promise<MissionListRead> {
  return authFetch<MissionListRead>(API_ENDPOINTS.missions);
}

export async function fetchMissionBySlug(slug: string): Promise<MissionRead> {
  return authFetch<MissionRead>(apiPath.missionBySlug(slug));
}

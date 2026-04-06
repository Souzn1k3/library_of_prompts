import { API_ENDPOINTS, apiPath } from "../constants/api";
import type {
  ScenarioBlueprintPatch,
  ScenarioBlueprintCommentRead,
  ScenarioBlueprintCommentWrite,
  ScenarioBlueprintLineageRead,
  ScenarioBlueprintPublishRead,
  ScenarioBlueprintRatingRead,
  ScenarioBlueprintRatingWrite,
  ScenarioBlueprintRead,
  ScenarioBlueprintSaveRead,
  ScenarioBlueprintShareRead,
  ScenarioBlueprintShareWrite,
  ScenarioBlueprintUsageTrackRead,
  ScenarioBlueprintUsageTrackWrite,
  ScenarioBlueprintVersionRead,
  ScenarioBlueprintWrite,
  ScenarioChainRead,
  ScenarioDemoRunStatusRead,
  ScenarioDemoRunTrackRead,
  ScenarioDemoRunTrackRequest,
  ScenarioGameClaimRead,
  ScenarioGameClaimRequest,
  ScenarioGameEarnRead,
  ScenarioGameEarnRequest,
  ScenarioGameStateRead,
  ScenarioHomeAggregateRead,
  ScenarioMarketplaceForkRead,
  ScenarioNextStepRead,
  ScenarioPackRead,
  ScenarioRunEventRead,
  ScenarioShowcaseCreateRequest,
  ScenarioShowcaseRead,
  ScenarioShowcaseUpvoteRequest,
  ScenarioTokenBoostPurchaseRead,
  ScenarioTokenBoostPurchaseRequest,
  ScenarioWorkflowRead,
  ScenarioWorkflowRunAdvanceRead,
  ScenarioWorkflowRunRead,
  ScenarioWorkflowRunStartWrite,
  ScenarioWorkflowWrite,
  ScenarioWorkspaceRead,
  ScenarioWorkspaceTrackRequest,
} from "../types";
import { authFetch, jsonInit } from "./transport";

export async function fetchScenarioWorkspace(params?: {
  recent_limit?: number;
  saved_limit?: number;
  unfinished_limit?: number;
}): Promise<ScenarioWorkspaceRead> {
  const query = new URLSearchParams();
  if (params?.recent_limit) {
    query.set("recent_limit", String(params.recent_limit));
  }
  if (params?.saved_limit) {
    query.set("saved_limit", String(params.saved_limit));
  }
  if (params?.unfinished_limit) {
    query.set("unfinished_limit", String(params.unfinished_limit));
  }
  const suffix = query.toString();
  const path = suffix ? `${API_ENDPOINTS.scenariosWorkspace}?${suffix}` : API_ENDPOINTS.scenariosWorkspace;
  return authFetch<ScenarioWorkspaceRead>(path);
}

export async function trackScenarioWorkspaceAction(body: ScenarioWorkspaceTrackRequest): Promise<ScenarioRunEventRead> {
  return authFetch<ScenarioRunEventRead>(
    API_ENDPOINTS.scenariosWorkspaceTrack,
    jsonInit("POST", body),
  );
}

export async function fetchScenarioHomeAggregateClient(limit = 8): Promise<ScenarioHomeAggregateRead> {
  const path = `${API_ENDPOINTS.scenariosAggregate}?limit=${encodeURIComponent(String(limit))}`;
  return authFetch<ScenarioHomeAggregateRead>(path);
}

export async function fetchScenarioDemoRunStatus(promptSlug: string): Promise<ScenarioDemoRunStatusRead> {
  const path = `${API_ENDPOINTS.scenariosDemoRunStatus}?prompt_slug=${encodeURIComponent(promptSlug)}`;
  return authFetch<ScenarioDemoRunStatusRead>(path);
}

export async function trackScenarioDemoRun(body: ScenarioDemoRunTrackRequest): Promise<ScenarioDemoRunTrackRead> {
  return authFetch<ScenarioDemoRunTrackRead>(API_ENDPOINTS.scenariosDemoRunTrack, jsonInit("POST", body));
}

export async function purchaseScenarioDemoRunBoost(
  body: ScenarioTokenBoostPurchaseRequest,
): Promise<ScenarioTokenBoostPurchaseRead> {
  return authFetch<ScenarioTokenBoostPurchaseRead>(
    API_ENDPOINTS.scenariosDemoRunBoostPurchase,
    jsonInit("POST", body),
  );
}

export async function fetchScenarioGameState(): Promise<ScenarioGameStateRead> {
  return authFetch<ScenarioGameStateRead>(API_ENDPOINTS.scenariosGameState);
}

export async function earnScenarioGameTokens(body: ScenarioGameEarnRequest): Promise<ScenarioGameEarnRead> {
  return authFetch<ScenarioGameEarnRead>(API_ENDPOINTS.scenariosGameEarn, jsonInit("POST", body));
}

export async function claimScenarioGameTokens(body?: ScenarioGameClaimRequest): Promise<ScenarioGameClaimRead> {
  return authFetch<ScenarioGameClaimRead>(API_ENDPOINTS.scenariosGameClaim, jsonInit("POST", body ?? {}));
}

export async function fetchScenarioPacks(): Promise<ScenarioPackRead[]> {
  return authFetch<ScenarioPackRead[]>(API_ENDPOINTS.scenariosPacks);
}

export async function fetchScenarioChains(): Promise<ScenarioChainRead[]> {
  return authFetch<ScenarioChainRead[]>(API_ENDPOINTS.scenariosChains);
}

export async function fetchScenarioNextStep(promptSlug?: string | null): Promise<ScenarioNextStepRead | null> {
  const path = promptSlug
    ? `${API_ENDPOINTS.scenariosNextStep}?prompt_slug=${encodeURIComponent(promptSlug)}`
    : API_ENDPOINTS.scenariosNextStep;
  return authFetch<ScenarioNextStepRead | null>(path);
}

export async function fetchScenarioShowcase(limit = 24): Promise<ScenarioShowcaseRead[]> {
  return authFetch<ScenarioShowcaseRead[]>(
    `${API_ENDPOINTS.scenariosShowcase}?limit=${encodeURIComponent(String(limit))}`,
  );
}

export async function createScenarioShowcase(body: ScenarioShowcaseCreateRequest): Promise<ScenarioShowcaseRead> {
  return authFetch<ScenarioShowcaseRead>(API_ENDPOINTS.scenariosShowcaseShare, jsonInit("POST", body));
}

export async function upvoteScenarioShowcase(body: ScenarioShowcaseUpvoteRequest): Promise<ScenarioShowcaseRead> {
  return authFetch<ScenarioShowcaseRead>(API_ENDPOINTS.scenariosShowcaseUpvote, jsonInit("POST", body));
}

export async function fetchMyScenarioBlueprints(): Promise<ScenarioBlueprintRead[]> {
  return authFetch<ScenarioBlueprintRead[]>(API_ENDPOINTS.scenariosStudioMine);
}

export async function createScenarioBlueprint(body: ScenarioBlueprintWrite): Promise<ScenarioBlueprintRead> {
  return authFetch<ScenarioBlueprintRead>(API_ENDPOINTS.scenariosStudio, jsonInit("POST", body));
}

export async function patchScenarioBlueprint(
  blueprintId: string,
  body: ScenarioBlueprintPatch,
): Promise<ScenarioBlueprintRead> {
  return authFetch<ScenarioBlueprintRead>(apiPath.scenarioStudioById(blueprintId), jsonInit("PATCH", body));
}

export async function publishScenarioBlueprint(blueprintId: string): Promise<ScenarioBlueprintPublishRead> {
  return authFetch<ScenarioBlueprintPublishRead>(apiPath.scenarioStudioPublish(blueprintId), jsonInit("POST", {}));
}

export async function fetchScenarioBlueprintVersions(
  blueprintId: string,
  limit = 40,
): Promise<ScenarioBlueprintVersionRead[]> {
  return authFetch<ScenarioBlueprintVersionRead[]>(
    `${apiPath.scenarioStudioVersions(blueprintId)}?limit=${encodeURIComponent(String(limit))}`,
  );
}

export async function fetchScenarioBlueprintLineage(
  blueprintId: string,
): Promise<ScenarioBlueprintLineageRead> {
  return authFetch<ScenarioBlueprintLineageRead>(apiPath.scenarioStudioLineage(blueprintId));
}

export async function shareScenarioBlueprint(
  blueprintId: string,
  body: ScenarioBlueprintShareWrite,
): Promise<ScenarioBlueprintShareRead> {
  return authFetch<ScenarioBlueprintShareRead>(apiPath.scenarioStudioShare(blueprintId), jsonInit("POST", body));
}

export async function fetchScenarioMarketplace(
  params:
    | number
    | {
        limit?: number;
        section?: "trending" | "new" | "top" | "best" | "personalized";
        search?: string | null;
        category?: string | null;
        tags?: string[] | null;
      } = 24,
): Promise<ScenarioBlueprintRead[]> {
  const normalized = typeof params === "number" ? { limit: params } : params;
  const query = new URLSearchParams();
  query.set("limit", String(normalized.limit ?? 24));
  if (normalized.section) {
    query.set("section", normalized.section);
  }
  if (normalized.search) {
    query.set("search", normalized.search);
  }
  if (normalized.category) {
    query.set("category", normalized.category);
  }
  if (normalized.tags && normalized.tags.length) {
    query.set("tags", normalized.tags.join(","));
  }
  return authFetch<ScenarioBlueprintRead[]>(
    `${API_ENDPOINTS.scenariosMarketplace}?${query.toString()}`,
  );
}

export async function forkScenarioMarketplaceBlueprint(
  blueprintId: string,
): Promise<ScenarioMarketplaceForkRead> {
  return authFetch<ScenarioMarketplaceForkRead>(apiPath.scenarioMarketplaceFork(blueprintId), jsonInit("POST", {}));
}

export async function remixScenarioMarketplaceBlueprint(
  blueprintId: string,
): Promise<ScenarioMarketplaceForkRead> {
  return authFetch<ScenarioMarketplaceForkRead>(apiPath.scenarioMarketplaceRemix(blueprintId), jsonInit("POST", {}));
}

export async function likeScenarioMarketplaceBlueprint(
  blueprintId: string,
): Promise<ScenarioBlueprintRead> {
  return authFetch<ScenarioBlueprintRead>(apiPath.scenarioMarketplaceLike(blueprintId), jsonInit("POST", {}));
}

export async function saveScenarioMarketplaceBlueprint(
  blueprintId: string,
): Promise<ScenarioBlueprintSaveRead> {
  return authFetch<ScenarioBlueprintSaveRead>(apiPath.scenarioMarketplaceSave(blueprintId), jsonInit("POST", {}));
}

export async function rateScenarioMarketplaceBlueprint(
  blueprintId: string,
  body: ScenarioBlueprintRatingWrite,
): Promise<ScenarioBlueprintRatingRead> {
  return authFetch<ScenarioBlueprintRatingRead>(apiPath.scenarioMarketplaceRating(blueprintId), jsonInit("POST", body));
}

export async function fetchScenarioMarketplaceComments(
  blueprintId: string,
  limit = 30,
): Promise<ScenarioBlueprintCommentRead[]> {
  return authFetch<ScenarioBlueprintCommentRead[]>(
    `${apiPath.scenarioMarketplaceComments(blueprintId)}?limit=${encodeURIComponent(String(limit))}`,
  );
}

export async function createScenarioMarketplaceComment(
  blueprintId: string,
  body: ScenarioBlueprintCommentWrite,
): Promise<ScenarioBlueprintCommentRead> {
  return authFetch<ScenarioBlueprintCommentRead>(apiPath.scenarioMarketplaceComments(blueprintId), jsonInit("POST", body));
}

export async function trackScenarioMarketplaceUsage(
  blueprintId: string,
  body: ScenarioBlueprintUsageTrackWrite,
): Promise<ScenarioBlueprintUsageTrackRead> {
  return authFetch<ScenarioBlueprintUsageTrackRead>(apiPath.scenarioMarketplaceUsage(blueprintId), jsonInit("POST", body));
}

export async function fetchMyScenarioWorkflows(): Promise<ScenarioWorkflowRead[]> {
  return authFetch<ScenarioWorkflowRead[]>(API_ENDPOINTS.scenariosWorkflowsMine);
}

export async function createScenarioWorkflow(body: ScenarioWorkflowWrite): Promise<ScenarioWorkflowRead> {
  return authFetch<ScenarioWorkflowRead>(API_ENDPOINTS.scenariosWorkflows, jsonInit("POST", body));
}

export async function runScenarioWorkflow(
  workflowId: string,
  body?: ScenarioWorkflowRunStartWrite,
): Promise<ScenarioWorkflowRunRead> {
  return authFetch<ScenarioWorkflowRunRead>(apiPath.scenarioWorkflowRun(workflowId), jsonInit("POST", body ?? {}));
}

export async function advanceScenarioWorkflowRun(runId: string): Promise<ScenarioWorkflowRunAdvanceRead> {
  return authFetch<ScenarioWorkflowRunAdvanceRead>(apiPath.scenarioWorkflowAdvanceRun(runId), jsonInit("POST", {}));
}

export async function fetchTeamSharedScenarioBlueprints(): Promise<ScenarioBlueprintRead[]> {
  return authFetch<ScenarioBlueprintRead[]>(API_ENDPOINTS.scenariosTeamShared);
}

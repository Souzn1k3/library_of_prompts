export const API_V1_PREFIX = "/api/v1";

export const API_ENDPOINTS = {
  analyticsEvents: `${API_V1_PREFIX}/analytics/events`,
  auth: {
    refresh: `${API_V1_PREFIX}/auth/refresh`,
    login: `${API_V1_PREFIX}/auth/login`,
    register: `${API_V1_PREFIX}/auth/register`,
    logout: `${API_V1_PREFIX}/auth/logout`,
  },
  categories: `${API_V1_PREFIX}/categories`,
  prompts: `${API_V1_PREFIX}/prompts`,
  promptDiscoveryFilters: `${API_V1_PREFIX}/prompts/discovery-filters`,
  promptDiscoverySections: `${API_V1_PREFIX}/prompts/discovery-sections`,
  promptRecommendations: `${API_V1_PREFIX}/prompts/recommendations`,
  contributorsTop: `${API_V1_PREFIX}/contributors/top`,
  billingPlans: `${API_V1_PREFIX}/billing/plans`,
  billingSubscription: `${API_V1_PREFIX}/billing/subscription`,
  billingCheckoutSession: `${API_V1_PREFIX}/billing/checkout/session`,
  billingPortal: `${API_V1_PREFIX}/billing/portal`,
  marketplaceMe: `${API_V1_PREFIX}/marketplace/me`,
  marketplacePromptCheckoutSession: `${API_V1_PREFIX}/marketplace/prompts/checkout-session`,
  onboardingProfile: `${API_V1_PREFIX}/onboarding/profile`,
  onboardingSkip: `${API_V1_PREFIX}/onboarding/skip`,
  onboardingStarterPack: `${API_V1_PREFIX}/onboarding/starter-pack`,
  onboardingFirstWin: `${API_V1_PREFIX}/onboarding/first-win`,
  missions: `${API_V1_PREFIX}/missions`,
  missionsCurrent: `${API_V1_PREFIX}/missions/current`,
  wallet: `${API_V1_PREFIX}/wallet`,
  walletCheckIn: `${API_V1_PREFIX}/wallet/check-in`,
  scenariosAggregate: `${API_V1_PREFIX}/scenarios/aggregate`,
  scenariosWorkspace: `${API_V1_PREFIX}/scenarios/workspace`,
  scenariosWorkspaceTrack: `${API_V1_PREFIX}/scenarios/workspace/track`,
  scenariosDemoRunStatus: `${API_V1_PREFIX}/scenarios/demo-run/status`,
  scenariosDemoRunTrack: `${API_V1_PREFIX}/scenarios/demo-run/track`,
  scenariosDemoRunBoostPurchase: `${API_V1_PREFIX}/scenarios/demo-run/boost-purchase`,
  scenariosGameState: `${API_V1_PREFIX}/scenarios/game/state`,
  scenariosGameEarn: `${API_V1_PREFIX}/scenarios/game/earn`,
  scenariosGameClaim: `${API_V1_PREFIX}/scenarios/game/claim`,
  scenariosPacks: `${API_V1_PREFIX}/scenarios/packs`,
  scenariosChains: `${API_V1_PREFIX}/scenarios/chains`,
  scenariosNextStep: `${API_V1_PREFIX}/scenarios/next-step`,
  scenariosShowcase: `${API_V1_PREFIX}/scenarios/showcase`,
  scenariosShowcaseShare: `${API_V1_PREFIX}/scenarios/showcase/share`,
  scenariosShowcaseUpvote: `${API_V1_PREFIX}/scenarios/showcase/upvote`,
  scenariosStudio: `${API_V1_PREFIX}/scenarios/studio`,
  scenariosStudioMine: `${API_V1_PREFIX}/scenarios/studio/mine`,
  scenariosMarketplace: `${API_V1_PREFIX}/scenarios/marketplace`,
  scenariosWorkflows: `${API_V1_PREFIX}/scenarios/workflows`,
  scenariosWorkflowsMine: `${API_V1_PREFIX}/scenarios/workflows/mine`,
  scenariosTeamShared: `${API_V1_PREFIX}/scenarios/team/shared`,
  store: `${API_V1_PREFIX}/store`,
  lessons: `${API_V1_PREFIX}/lessons`,
  lessonsPopular: `${API_V1_PREFIX}/lessons/popular`,
  learningStartTarget: `${API_V1_PREFIX}/learning/start-target`,
  learningCourses: `${API_V1_PREFIX}/learning/courses`,
  learningMy: `${API_V1_PREFIX}/learning/my`,
  usersMe: `${API_V1_PREFIX}/users/me`,
  usersSavedPrompts: `${API_V1_PREFIX}/users/me/saved-prompts`,
  usersSubmissions: `${API_V1_PREFIX}/users/me/submissions`,
  contributionsSubmit: `${API_V1_PREFIX}/contributions/submit`,
} as const;

export const apiPath = {
  missionBySlug: (slug: string) => `${API_ENDPOINTS.missions}/${encodeURIComponent(slug)}`,
  storePurchaseBySlug: (slug: string) => `${API_ENDPOINTS.store}/${encodeURIComponent(slug)}/purchase`,
  lessonBySlug: (slug: string) => `${API_ENDPOINTS.lessons}/by-slug/${encodeURIComponent(slug)}`,
  lessonCompleteBySlug: (slug: string) =>
    `${API_ENDPOINTS.lessons}/by-slug/${encodeURIComponent(slug)}/complete`,
  learningCourse: (courseSlug: string) => `${API_ENDPOINTS.learningCourses}/${encodeURIComponent(courseSlug)}`,
  learningLesson: (courseSlug: string, lessonSlug: string) =>
    `${API_ENDPOINTS.learningCourses}/${encodeURIComponent(courseSlug)}/lessons/${encodeURIComponent(lessonSlug)}`,
  learningStepSubmit: (courseSlug: string, lessonSlug: string, stepSlug: string) =>
    `${API_ENDPOINTS.learningCourses}/${encodeURIComponent(courseSlug)}/lessons/${encodeURIComponent(lessonSlug)}/steps/${encodeURIComponent(stepSlug)}/submit`,
  learningLocateLessonBySlug: (lessonSlug: string) =>
    `${API_V1_PREFIX}/learning/lessons/by-slug/${encodeURIComponent(lessonSlug)}/locate`,
  promptBySlug: (slug: string) => `${API_ENDPOINTS.prompts}/by-slug/${encodeURIComponent(slug)}`,
  promptRelatedBySlug: (slug: string) =>
    `${API_ENDPOINTS.prompts}/by-slug/${encodeURIComponent(slug)}/related`,
  contributorBySlug: (slug: string) => `${API_V1_PREFIX}/contributors/${encodeURIComponent(slug)}`,
  marketplacePromptBuyWithLumens: (promptId: string) =>
    `${API_V1_PREFIX}/marketplace/prompts/${promptId}/buy-with-lumens`,
  marketplacePromptReview: (promptId: string) =>
    `${API_V1_PREFIX}/marketplace/prompts/${promptId}/review`,
  userSavedPromptById: (promptId: string) => `${API_ENDPOINTS.usersSavedPrompts}/${promptId}`,
  promptEventCopy: (promptId: string) => `${API_ENDPOINTS.prompts}/${promptId}/events/copy`,
  promptEventApply: (promptId: string) => `${API_ENDPOINTS.prompts}/${promptId}/events/apply`,
  scenarioStudioById: (blueprintId: string) => `${API_ENDPOINTS.scenariosStudio}/${encodeURIComponent(blueprintId)}`,
  scenarioStudioPublish: (blueprintId: string) =>
    `${API_ENDPOINTS.scenariosStudio}/${encodeURIComponent(blueprintId)}/publish`,
  scenarioStudioShare: (blueprintId: string) =>
    `${API_ENDPOINTS.scenariosStudio}/${encodeURIComponent(blueprintId)}/share`,
  scenarioMarketplaceFork: (blueprintId: string) =>
    `${API_ENDPOINTS.scenariosMarketplace}/${encodeURIComponent(blueprintId)}/fork`,
  scenarioMarketplaceLike: (blueprintId: string) =>
    `${API_ENDPOINTS.scenariosMarketplace}/${encodeURIComponent(blueprintId)}/like`,
  scenarioWorkflowRun: (workflowId: string) =>
    `${API_ENDPOINTS.scenariosWorkflows}/${encodeURIComponent(workflowId)}/run`,
  scenarioWorkflowAdvanceRun: (runId: string) =>
    `${API_ENDPOINTS.scenariosWorkflows}/runs/${encodeURIComponent(runId)}/advance`,
  telegramRewardClaim: `${API_V1_PREFIX}/telegram/rewards/claim`,
} as const;

export const APP_ROUTES = {
  home: "/",
  catalog: "/catalog",
  learn: "/learn",
  plans: "/plans",
  pricing: "/pricing",
  missions: "/missions",
  store: "/store",
  wallet: "/wallet",
  dashboard: "/dashboard",
  profile: "/profile",
  login: "/login",
  signup: "/signup",
  onboarding: "/onboarding",
  submit: "/submit",
  prompt: "/prompt",
  contributors: "/contributors",
} as const;

export const appRoute = {
  promptBySlug: (slug: string) => `${APP_ROUTES.prompt}/${encodeURIComponent(slug)}`,
  missionBySlug: (slug: string) => `${APP_ROUTES.missions}/${encodeURIComponent(slug)}`,
  learnBySlug: (slug: string) => `${APP_ROUTES.learn}/${encodeURIComponent(slug)}`,
  plansWithTier: (tier: string) => `${APP_ROUTES.plans}?tier=${encodeURIComponent(tier)}`,
  contributorBySlug: (slug: string) => `${APP_ROUTES.contributors}/${encodeURIComponent(slug)}`,
  contributorBySlugReviewSort: (slug: string, reviewSort: string) =>
    `${APP_ROUTES.contributors}/${encodeURIComponent(slug)}?review_sort=${encodeURIComponent(reviewSort)}`,
} as const;

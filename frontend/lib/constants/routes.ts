export const APP_ROUTES = {
  home: "/",
  catalog: "/catalog",
  scenarios: "/scenarios",
  scenariosMarketplace: "/scenarios/marketplace",
  learn: "/learn",
  learnStart: "/learn/start",
  learnMy: "/learn/my",
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

export const LEARNING_FOUNDATIONS_COURSE_SLUG = "prompt-engineering-foundations";

export const appRoute = {
  promptBySlug: (slug: string) => `${APP_ROUTES.prompt}/${encodeURIComponent(slug)}`,
  missionBySlug: (slug: string) => `${APP_ROUTES.missions}/${encodeURIComponent(slug)}`,
  learnBySlug: (slug: string) => `${APP_ROUTES.learn}/${encodeURIComponent(slug)}`,
  learnCourse: (courseSlug: string) => `${APP_ROUTES.learn}/course/${encodeURIComponent(courseSlug)}`,
  learnCourseLesson: (courseSlug: string, lessonSlug: string) =>
    `${APP_ROUTES.learn}/course/${encodeURIComponent(courseSlug)}/lesson/${encodeURIComponent(lessonSlug)}`,
  learnCourseLessonStep: (courseSlug: string, lessonSlug: string, stepSlug: string) =>
    `${APP_ROUTES.learn}/course/${encodeURIComponent(courseSlug)}/lesson/${encodeURIComponent(lessonSlug)}/step/${encodeURIComponent(stepSlug)}`,
  plansWithTier: (tier: string) => `${APP_ROUTES.pricing}?tier=${encodeURIComponent(tier)}`,
  contributorBySlug: (slug: string) => `${APP_ROUTES.contributors}/${encodeURIComponent(slug)}`,
  contributorBySlugReviewSort: (slug: string, reviewSort: string) =>
    `${APP_ROUTES.contributors}/${encodeURIComponent(slug)}?review_sort=${encodeURIComponent(reviewSort)}`,
} as const;

import { expect, test, type APIRequestContext } from "@playwright/test";

const API_BASE = process.env.PLAYWRIGHT_API_BASE_URL ?? "http://127.0.0.1:8000";
const COURSE_FOUNDATIONS = "prompt-engineering-foundations";
const SMOKE_EMAIL = process.env.PLAYWRIGHT_SMOKE_EMAIL;
const SMOKE_PASSWORD = process.env.PLAYWRIGHT_SMOKE_PASSWORD ?? "password123";
const SMOKE_ACCESS_TOKEN = process.env.PLAYWRIGHT_SMOKE_ACCESS_TOKEN;
const BASE_TEXT = `
[ROLE] Senior AI coach
[CONTEXT] This workflow supports study and work execution in a real project context.
[TASK] Build a clear brief, compare options, debug weak output, and refine results.
[CONSTRAINTS] Keep facts explicit, avoid vague wording, include risks and fallback.
[OUTPUT] Stage 1 brief, Stage 2 analysis table, Stage 3 action checklist.
[CHECK] score criterion metric 1-5 with threshold and confidence.
[EXAMPLE] changed because evidence improved; workflow success owner cadence metric risk fallback.
workflow success risk owner cadence metric threshold changed because Stage 1 Stage 2 Stage 3.
`.trim();

type LearningStep = {
  slug: string;
  submission_type: "none" | "text" | "choice";
  choices: Array<{ id: string }>;
  task?: string | null;
  title: string;
};

type LearningLesson = {
  lesson_slug: string;
  steps: LearningStep[];
};

type LearningCourse = {
  slug: string;
  modules: Array<{ lessons: Array<{ slug: string }> }>;
};

type LearningMyModules = {
  active_courses: Array<{ slug: string }>;
  completed_courses: Array<{
    slug: string;
    badge_code: string | null;
    certificate_ready: boolean;
  }>;
};

async function authByLogin(
  request: APIRequestContext,
  email: string,
  password: string,
): Promise<string> {
  const response = await request.post(`${API_BASE}/api/v1/auth/login`, {
    headers: { "Accept-Language": "en" },
    data: { email, password },
  });
  expect(response.ok()).toBeTruthy();
  const payload = (await response.json()) as { access_token: string };
  return payload.access_token;
}

async function registerWithRetry(
  request: APIRequestContext,
  email: string,
  password: string,
): Promise<string> {
  const maxAttempts = 8;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const registerResponse = await request.post(`${API_BASE}/api/v1/auth/register`, {
      headers: { "Accept-Language": "en" },
      data: {
        email,
        password,
        display_name: `Learning Smoke ${Date.now()}-${attempt}`,
      },
    });
    if (registerResponse.ok()) {
      const registerBody = (await registerResponse.json()) as { access_token: string };
      return registerBody.access_token;
    }

    if (registerResponse.status() === 429 && attempt < maxAttempts) {
      const retryAfterHeader = registerResponse.headers()["retry-after"];
      const retryAfterSeconds = Number.parseInt(retryAfterHeader ?? "", 10);
      const retryAfterMs = Number.isFinite(retryAfterSeconds) ? retryAfterSeconds * 1000 : 0;
      const backoffMs = Math.min(12000, 1500 * attempt);
      await new Promise((resolve) => setTimeout(resolve, Math.max(retryAfterMs, backoffMs)));
      continue;
    }

    throw new Error(`register failed: ${registerResponse.status()} ${await registerResponse.text()}`);
  }

  throw new Error("register retries exhausted");
}

function answerForStep(step: LearningStep): Record<string, unknown> | null {
  if (step.submission_type === "none") {
    return null;
  }
  if (step.submission_type === "choice") {
    const preferred = step.choices.find((item) => item.id === "b");
    return { choice_id: preferred?.id ?? step.choices[0]?.id ?? "" };
  }
  return { text: BASE_TEXT };
}

async function apiGet<T>(request: APIRequestContext, token: string, path: string): Promise<T> {
  const response = await request.get(`${API_BASE}${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Accept-Language": "en",
    },
  });
  if (!response.ok()) {
    throw new Error(`GET ${path} failed: ${response.status()} ${await response.text()}`);
  }
  return (await response.json()) as T;
}

async function submitStep(
  request: APIRequestContext,
  token: string,
  courseSlug: string,
  lessonSlug: string,
  step: LearningStep,
): Promise<void> {
  const response = await request.post(
    `${API_BASE}/api/v1/learning/courses/${courseSlug}/lessons/${lessonSlug}/steps/${step.slug}/submit`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        "Accept-Language": "en",
      },
      data: { answer: answerForStep(step) },
    },
  );
  if (!response.ok()) {
    throw new Error(
      `submit ${courseSlug}/${lessonSlug}/${step.slug} failed: ${response.status()} ${await response.text()}`,
    );
  }
  const payload = (await response.json()) as { passed: boolean };
  if (!payload.passed && step.submission_type === "text") {
    const retry = await request.post(
      `${API_BASE}/api/v1/learning/courses/${courseSlug}/lessons/${lessonSlug}/steps/${step.slug}/submit`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Accept-Language": "en",
        },
        data: { answer: { text: `${BASE_TEXT}\n${step.task ?? ""}\n${step.title}` } },
      },
    );
    expect(retry.ok()).toBeTruthy();
    const retryPayload = (await retry.json()) as { passed: boolean };
    expect(retryPayload.passed).toBeTruthy();
  }
}

async function completeCourse(
  request: APIRequestContext,
  token: string,
  courseSlug: string,
): Promise<void> {
  const course = await apiGet<LearningCourse>(request, token, `/api/v1/learning/courses/${courseSlug}`);
  for (const module of course.modules) {
    for (const lessonRef of module.lessons) {
      const lesson = await apiGet<LearningLesson>(
        request,
        token,
        `/api/v1/learning/courses/${courseSlug}/lessons/${lessonRef.slug}`,
      );
      for (const step of lesson.steps) {
        await submitStep(request, token, courseSlug, lessonRef.slug, step);
      }
    }
  }
}

test("learning browser smoke", async ({ page, request }) => {
  const email = SMOKE_EMAIL ?? `learning_smoke_${Date.now()}@example.com`;
  const password = SMOKE_PASSWORD;
  let token: string;

  if (SMOKE_ACCESS_TOKEN) {
    token = SMOKE_ACCESS_TOKEN;
  } else if (SMOKE_EMAIL) {
    token = await authByLogin(request, email, password);
  } else {
    token = await registerWithRetry(request, email, password);
  }

  await page.context().clearCookies();
  if (SMOKE_ACCESS_TOKEN) {
    await page.context().addCookies([{
      name: "pv_access_token",
      value: SMOKE_ACCESS_TOKEN,
      domain: "localhost",
      path: "/",
      httpOnly: true,
      secure: false,
      sameSite: "Lax",
    }]);
  } else {
    await page.goto("/login");
    await expect(page).toHaveURL(/\/login$/);
    const loginForm = page.locator("form").filter({ has: page.locator("input[name='email']") }).first();
    await loginForm.locator("input[name='email']").fill(email);
    await loginForm.locator("input[name='password']").fill(password);
    await loginForm.locator("button[type='submit']").click();
    await page.waitForURL(/\/(dashboard|onboarding)(\/.*)?$/);
  }

  await page.goto("/learn/start");
  await page.waitForURL(/\/learn(\/course\/[^/]+\/lesson\/[^/?#]+)?$/);

  await page.goto(`/learn/course/${COURSE_FOUNDATIONS}`);
  await expect(page.locator("a[href*='/learn/course/prompt-engineering-foundations/lesson/']").first()).toBeVisible();
  await page.locator("a[href*='/learn/course/prompt-engineering-foundations/lesson/']").first().click();
  await expect(page).toHaveURL(/\/learn\/course\/prompt-engineering-foundations\/lesson\//);

  const lessonUrl = page.url();

  const lessonSlugMatch = lessonUrl.match(/\/lesson\/([^/?#]+)/);
  expect(lessonSlugMatch).not.toBeNull();
  const lessonSlug = lessonSlugMatch![1];

  const lesson = await apiGet<LearningLesson>(
    request,
    token,
    `/api/v1/learning/courses/${COURSE_FOUNDATIONS}/lessons/${lessonSlug}`,
  );
  const finalStep = lesson.steps[lesson.steps.length - 1];
  expect(finalStep).toBeTruthy();

  if (lesson.steps.length > 1) {
    for (const step of lesson.steps.slice(0, lesson.steps.length - 1)) {
      await submitStep(request, token, COURSE_FOUNDATIONS, lessonSlug, step);
    }
  }

  await page.reload();

  const finalStepHeading = page.getByRole("heading", { name: finalStep.title });
  await expect(finalStepHeading.first()).toBeVisible();
  const finalStepCard = finalStepHeading.first().locator("xpath=ancestor::article[1]");
  if (finalStep.submission_type === "text") {
    await finalStepCard.locator("textarea").fill(BASE_TEXT);
  } else if (finalStep.submission_type === "choice") {
    await finalStepCard.locator("input[type='radio']").first().check();
  }
  await finalStepCard.getByRole("button").first().click();

  await expect(page.locator(".pv-alert-success").first()).toBeVisible();
  await expect(page.locator("[role='progressbar'][aria-valuenow='100']").first()).toBeVisible();

  await page.goto("/learn/start");
  await page.waitForURL(/\/learn\/course\/[^/]+\/lesson\//);
  const continueHref = page.url();
  expect(continueHref).toMatch(/\/learn\/course\/[^/]+\/lesson\//);
  await page.goto(continueHref);
  await expect(page).toHaveURL(/\/learn\/course\/[^/]+\/lesson\//);

  await completeCourse(request, token, COURSE_FOUNDATIONS);
  const myModules = await apiGet<LearningMyModules>(
    request,
    token,
    "/api/v1/learning/my",
  );
  const completedFoundations = myModules.completed_courses.find((course) => course.slug === COURSE_FOUNDATIONS);
  expect(completedFoundations).toBeTruthy();

  await page.goto("/learn/my");
  await expect(page.locator("text=100%").first()).toBeVisible();
  await expect(page.locator(".pv-chip").first()).toBeVisible();
  if (completedFoundations?.certificate_ready) {
    await expect(page.getByText(/Certificate[- ]ready/i).first()).toBeVisible();
  }

  await page.goto("/learn");
  await page.evaluate(() => {
    localStorage.setItem("pv_language", "en");
    document.cookie = "pv_language=en; path=/";
  });
  await page.reload();
  await expect(page.getByRole("heading", { name: "Learn" }).first()).toBeVisible();

  await page.evaluate(() => {
    localStorage.setItem("pv_language", "ru");
    document.cookie = "pv_language=ru; path=/";
  });
  await page.reload();
  await expect(page.getByRole("heading", { name: "Обучение" }).first()).toBeVisible();

  await page.evaluate(() => {
    localStorage.setItem("pv_language", "tt");
    document.cookie = "pv_language=tt; path=/";
  });
  await page.reload();
  await expect(page.getByRole("heading", { name: "Өйрәнү" }).first()).toBeVisible();
});

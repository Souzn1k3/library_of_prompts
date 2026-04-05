import fs from "node:fs/promises";
import path from "node:path";

import { chromium } from "playwright";

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";
const API_BASE = process.env.PLAYWRIGHT_API_BASE_URL ?? "http://127.0.0.1:8000";
const OUTPUT_DIR = path.resolve("artifacts", "screenshots", "learning-deep-debug");

const COURSE_SLUG = "prompt-engineering-foundations";
const FIRST_LESSON_SLUG = "pe-foundations";
const FINAL_LESSON_SLUG = "pe-final-studio";

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

function candidateOrigins(base, api) {
  const baseUrl = new URL(base);
  const apiUrl = new URL(api);
  const protocol = baseUrl.protocol;
  const preferredPort = baseUrl.port || "3000";
  const origins = new Set([
    base,
    api,
    `${protocol}//localhost:${preferredPort}`,
    `${protocol}//127.0.0.1:${preferredPort}`,
    `${protocol}//localhost:8000`,
    `${protocol}//127.0.0.1:8000`,
    `${apiUrl.protocol}//localhost:${apiUrl.port || "8000"}`,
    `${apiUrl.protocol}//127.0.0.1:${apiUrl.port || "8000"}`,
  ]);
  return [...origins];
}

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function registerUser() {
  const loginEmail = process.env.LEARNING_DEBUG_EMAIL;
  const loginPassword = process.env.LEARNING_DEBUG_PASSWORD;
  if (loginEmail && loginPassword) {
    return loginUser(loginEmail, loginPassword);
  }

  const nonce = Date.now();
  const email = `learning.deep.debug.${nonce}@example.com`;
  const password = "password123";
  const displayName = `Learning Deep Debug ${nonce}`;

  let response = null;
  for (let attempt = 1; attempt <= 4; attempt += 1) {
    response = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "Accept-Language": "en",
      },
      body: JSON.stringify({
        email,
        password,
        display_name: displayName,
      }),
    });
    if (response.ok) {
      break;
    }
    if (response.status !== 429 || attempt === 4) {
      throw new Error(`Register failed: ${response.status} ${await response.text()}`);
    }
    await new Promise((resolve) => setTimeout(resolve, 1200 * attempt));
  }

  if (!response || !response.ok) {
    throw new Error("Register failed without response");
  }

  const payload = await response.json();
  const accessToken = payload?.access_token;
  if (!accessToken) {
    throw new Error("register response missing access_token");
  }

  let refreshToken = null;
  const setCookie = response.headers.get("set-cookie");
  if (setCookie) {
    const match = setCookie.match(/pv_refresh_token=([^;]+)/);
    refreshToken = match?.[1] ?? null;
  }

  return { email, password, accessToken, refreshToken };
}

async function loginUser(email, password) {
  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "Accept-Language": "en",
    },
    body: JSON.stringify({
      email,
      password,
    }),
  });
  if (!response.ok) {
    throw new Error(`Login failed: ${response.status} ${await response.text()}`);
  }
  const payload = await response.json();
  const accessToken = payload?.access_token;
  if (!accessToken) {
    throw new Error("login response missing access_token");
  }

  let refreshToken = null;
  const setCookie = response.headers.get("set-cookie");
  if (setCookie) {
    const match = setCookie.match(/pv_refresh_token=([^;]+)/);
    refreshToken = match?.[1] ?? null;
  }

  return { email, password, accessToken, refreshToken };
}

async function apiGet(pathname, accessToken) {
  const response = await fetch(`${API_BASE}${pathname}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      Accept: "application/json",
      "Accept-Language": "en",
    },
  });
  if (!response.ok) {
    throw new Error(`GET ${pathname} failed: ${response.status} ${await response.text()}`);
  }
  return response.json();
}

async function apiSubmitStep(accessToken, lessonSlug, step, answerOverride = undefined) {
  const answer = answerOverride ?? answerForStep(step);
  const response = await fetch(
    `${API_BASE}/api/v1/learning/courses/${COURSE_SLUG}/lessons/${lessonSlug}/steps/${step.slug}/submit`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: "application/json",
        "Accept-Language": "en",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ answer }),
    },
  );
  if (!response.ok) {
    throw new Error(
      `submit ${lessonSlug}/${step.slug} failed: ${response.status} ${await response.text()}`,
    );
  }
  return response.json();
}

function answerForStep(step) {
  if (step.submission_type === "none") {
    return null;
  }
  if (step.submission_type === "choice") {
    const preferred = step.choices.find((item) => item.id === "b");
    return { choice_id: preferred?.id ?? step.choices[0]?.id ?? "" };
  }
  return { text: BASE_TEXT };
}

async function completeCourse(accessToken) {
  const completedLessonSlugs = new Set();

  for (let pass = 0; pass < 8; pass += 1) {
    let progressed = false;
    const course = await apiGet(`/api/v1/learning/courses/${COURSE_SLUG}`, accessToken);
    for (const module of course.modules) {
      for (const lessonRef of module.lessons) {
        if (completedLessonSlugs.has(lessonRef.slug)) {
          continue;
        }

        const lessonResponse = await fetch(
          `${API_BASE}/api/v1/learning/courses/${COURSE_SLUG}/lessons/${lessonRef.slug}`,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
              Accept: "application/json",
              "Accept-Language": "en",
            },
          },
        );
        if (lessonResponse.status === 409) {
          continue;
        }
        if (!lessonResponse.ok) {
          throw new Error(
            `GET lesson ${lessonRef.slug} failed: ${lessonResponse.status} ${await lessonResponse.text()}`,
          );
        }

        const lesson = await lessonResponse.json();
        for (const step of lesson.steps) {
          await apiSubmitStep(accessToken, lessonRef.slug, step);
        }
        completedLessonSlugs.add(lessonRef.slug);
        progressed = true;
      }
    }
    if (!progressed) {
      break;
    }
  }
}

async function shot(page, id) {
  const file = path.join(OUTPUT_DIR, `${id}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

async function waitAfterNavigation(page) {
  await page.waitForLoadState("domcontentloaded");
  await page.waitForLoadState("networkidle").catch(() => null);
}

async function gotoAndShot(page, route, id, report) {
  await page.goto(route, { waitUntil: "domcontentloaded" });
  await waitAfterNavigation(page);
  const file = await shot(page, id);
  report.push({ id, route: page.url(), file });
}

async function clickSubmit(page) {
  const labels = [/Mark as learned/i, /Check step/i, /Retry step/i];
  for (const label of labels) {
    const button = page.getByRole("button", { name: label }).first();
    if (await button.count()) {
      await button.click();
      return;
    }
  }
  throw new Error("submit button not found");
}

async function main() {
  await ensureDir(OUTPUT_DIR);
  const account = await registerUser();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    baseURL: BASE_URL,
    viewport: { width: 1440, height: 1024 },
  });

  const cookies = [];
  for (const origin of candidateOrigins(BASE_URL, API_BASE)) {
    cookies.push({
      name: "pv_access_token",
      value: account.accessToken,
      url: origin,
      httpOnly: false,
      secure: false,
      sameSite: "Lax",
    });
    if (account.refreshToken) {
      cookies.push({
        name: "pv_refresh_token",
        value: account.refreshToken,
        url: origin,
        httpOnly: false,
        secure: false,
        sameSite: "Lax",
      });
    }
  }
  cookies.push({
    name: "pv_language",
    value: "en",
    url: BASE_URL,
    httpOnly: false,
    secure: false,
    sameSite: "Lax",
  });
  await context.addCookies(cookies);

  await context.addInitScript(() => {
    localStorage.setItem("pv_language", "en");
    document.cookie = "pv_language=en; path=/";
  });

  const page = await context.newPage();
  const report = [];

  await gotoAndShot(page, "/learn/start", "01-entry-start-target", report);
  await page.waitForURL(/\/learn\/course\/[^/]+\/lesson\/[^/?#]+/);
  await shot(page, "02-entry-resolved-lesson");

  await gotoAndShot(page, "/learn", "03-learning-catalog", report);
  await gotoAndShot(page, "/learn/my", "04-my-learning", report);
  await gotoAndShot(page, `/learn/course/${COURSE_SLUG}`, "05-course-overview", report);
  await gotoAndShot(
    page,
    `/learn/course/${COURSE_SLUG}/lesson/${FIRST_LESSON_SLUG}`,
    "06-lesson-initial",
    report,
  );

  const lesson = await apiGet(
    `/api/v1/learning/courses/${COURSE_SLUG}/lessons/${FIRST_LESSON_SLUG}`,
    account.accessToken,
  );
  const theory = lesson.steps.find((step) => step.kind === "theory");
  const guided = lesson.steps.find((step) => step.kind === "guided_practice");
  const quiz = lesson.steps.find((step) => step.kind === "quiz");
  const applied = lesson.steps.find((step) => step.kind === "applied_exercise");
  const reflection = lesson.steps.find((step) => step.kind === "reflection");

  if (!theory || !guided || !quiz || !applied || !reflection) {
    throw new Error("first lesson does not include required step kinds");
  }

  await gotoAndShot(
    page,
    `/learn/course/${COURSE_SLUG}/lesson/${FIRST_LESSON_SLUG}/step/${theory.slug}`,
    "07-step-theory",
    report,
  );
  await clickSubmit(page);
  await page.locator(".pv-alert-success").first().waitFor({ timeout: 10000 });
  await shot(page, "08-step-theory-submitted");

  await gotoAndShot(
    page,
    `/learn/course/${COURSE_SLUG}/lesson/${FIRST_LESSON_SLUG}/step/${guided.slug}`,
    "09-step-guided",
    report,
  );
  await page.locator("textarea").first().fill("short");
  await clickSubmit(page);
  await page.locator(".pv-alert-warning").first().waitFor({ timeout: 10000 });
  await shot(page, "10-step-guided-fail-feedback");
  await page.locator("textarea").first().fill(BASE_TEXT);
  await clickSubmit(page);
  await page.locator(".pv-alert-success").first().waitFor({ timeout: 10000 });
  await shot(page, "11-step-guided-pass-feedback");

  await gotoAndShot(
    page,
    `/learn/course/${COURSE_SLUG}/lesson/${FIRST_LESSON_SLUG}/step/${quiz.slug}`,
    "12-step-quiz",
    report,
  );
  await page.locator("input[type='radio']").first().check();
  await clickSubmit(page);
  await page.locator(".pv-alert-warning").first().waitFor({ timeout: 10000 });
  await shot(page, "13-step-quiz-fail-feedback");
  await page.locator("input[type='radio']").nth(1).check();
  await clickSubmit(page);
  await page.locator(".pv-alert-success").first().waitFor({ timeout: 10000 });
  await shot(page, "14-step-quiz-pass-feedback");

  await gotoAndShot(
    page,
    `/learn/course/${COURSE_SLUG}/lesson/${FIRST_LESSON_SLUG}/step/${applied.slug}`,
    "15-step-applied",
    report,
  );
  await page.locator("textarea").first().fill(BASE_TEXT);
  await clickSubmit(page);
  await page.locator(".pv-alert-success").first().waitFor({ timeout: 10000 });
  await shot(page, "16-step-applied-pass-feedback");

  await gotoAndShot(
    page,
    `/learn/course/${COURSE_SLUG}/lesson/${FIRST_LESSON_SLUG}/step/${reflection.slug}`,
    "17-step-reflection",
    report,
  );
  await page
    .locator("textarea")
    .first()
    .fill(
      "I often skip output format. Next prompt I will lock format and add one quality check.",
    );
  await clickSubmit(page);
  await page.locator(".pv-alert-success").first().waitFor({ timeout: 10000 });
  await shot(page, "18-step-reflection-lesson-complete");

  await gotoAndShot(page, `/learn/course/${COURSE_SLUG}`, "19-course-progress-after-lesson", report);

  await completeCourse(account.accessToken);
  await gotoAndShot(page, "/learn/my", "20-my-learning-course-complete", report);

  await gotoAndShot(
    page,
    `/learn/course/${COURSE_SLUG}/lesson/${FINAL_LESSON_SLUG}/step/pe-final-checkpoint`,
    "21-step-final-checkpoint",
    report,
  );
  await gotoAndShot(page, "/learn/start", "22-start-after-course-complete", report);

  const reportPath = path.join(OUTPUT_DIR, "report.json");
  await fs.writeFile(
    reportPath,
    JSON.stringify(
      {
        generatedAt: new Date().toISOString(),
        baseUrl: BASE_URL,
        apiBase: API_BASE,
        screenshots: report,
      },
      null,
      2,
    ),
    "utf8",
  );

  await context.close();
  await browser.close();

  console.log(`Saved screenshots to ${OUTPUT_DIR}`);
  console.log(`Report: ${reportPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

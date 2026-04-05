import fs from "node:fs/promises";
import path from "node:path";

import { chromium } from "playwright";

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";
const API_BASE = process.env.PLAYWRIGHT_API_BASE_URL ?? "http://127.0.0.1:8000";
const OUTPUT_DIR = path.resolve("artifacts", "screenshots", "learning-deep-debug-mobile");

const COURSE_SLUG = "prompt-engineering-foundations";
const FIRST_LESSON_SLUG = "pe-foundations";

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

async function loginUser(email, password) {
  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "Accept-Language": "en",
    },
    body: JSON.stringify({ email, password }),
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

  return { accessToken, refreshToken };
}

async function registerUser() {
  const loginEmail = process.env.LEARNING_DEBUG_EMAIL;
  const loginPassword = process.env.LEARNING_DEBUG_PASSWORD;
  if (loginEmail && loginPassword) {
    return loginUser(loginEmail, loginPassword);
  }

  const nonce = Date.now();
  const email = `learning.mobile.audit.${nonce}@example.com`;
  const password = "password123";
  const displayName = `Learning Mobile Audit ${nonce}`;

  let response = null;
  const maxAttempts = 8;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
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
    if (response.status !== 429 || attempt === maxAttempts) {
      throw new Error(`Register failed: ${response.status} ${await response.text()}`);
    }
    const retryAfterHeader = response.headers.get("retry-after");
    const retryAfterSeconds = Number.parseInt(retryAfterHeader ?? "", 10);
    const retryAfterMs = Number.isFinite(retryAfterSeconds) ? retryAfterSeconds * 1000 : 0;
    const backoffMs = Math.min(12000, 1500 * attempt);
    await new Promise((resolve) => setTimeout(resolve, Math.max(retryAfterMs, backoffMs)));
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

  return { accessToken, refreshToken };
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

async function waitAfterNavigation(page) {
  await page.waitForLoadState("domcontentloaded");
  await page.waitForLoadState("networkidle").catch(() => null);
}

async function gotoAndShot(page, route, id, report) {
  await page.goto(route, { waitUntil: "domcontentloaded" });
  await waitAfterNavigation(page);
  const file = path.join(OUTPUT_DIR, `${id}.png`);
  await page.screenshot({ path: file, fullPage: true });
  report.push({ id, route: page.url(), file });
}

async function main() {
  await ensureDir(OUTPUT_DIR);
  const account = await registerUser();

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    baseURL: BASE_URL,
    viewport: { width: 390, height: 844 },
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

  const lesson = await apiGet(
    `/api/v1/learning/courses/${COURSE_SLUG}/lessons/${FIRST_LESSON_SLUG}`,
    account.accessToken,
  );
  const firstStepSlug = lesson.steps[0]?.slug;
  if (!firstStepSlug) {
    throw new Error("lesson has no steps");
  }

  const page = await context.newPage();
  const report = [];

  await gotoAndShot(page, "/learn", "01-learn", report);
  await gotoAndShot(page, `/learn/course/${COURSE_SLUG}`, "02-course", report);
  await gotoAndShot(
    page,
    `/learn/course/${COURSE_SLUG}/lesson/${FIRST_LESSON_SLUG}/step/${firstStepSlug}`,
    "03-step",
    report,
  );

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

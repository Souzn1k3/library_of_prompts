import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";

const baseUrl = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";
const baseUrlObject = new URL(baseUrl);
const inferredApiBase = `${baseUrlObject.protocol}//${baseUrlObject.hostname}:8000`;
const apiBase = process.env.API_BASE_URL ?? inferredApiBase;

const outputRoot = path.resolve("codex-visual-audit", "before");
const reportPath = path.resolve("codex-visual-audit", "before-audit-report.json");
const authStatePath = path.resolve("codex-visual-audit", "auth-state.json");

const locales = ["en", "ru", "tt"];
const viewports = [
  { id: "desktop", width: 1440, height: 1024 },
  { id: "mobile", width: 390, height: 844 },
];

function candidateOrigins(base, api) {
  const baseUrlObject = new URL(base);
  const apiUrlObject = new URL(api);
  const protocol = baseUrlObject.protocol;
  const preferredPort = baseUrlObject.port || "3000";
  const origins = new Set([
    base,
    api,
    `${protocol}//localhost:${preferredPort}`,
    `${protocol}//127.0.0.1:${preferredPort}`,
    `${protocol}//localhost:8000`,
    `${protocol}//127.0.0.1:8000`,
  ]);
  origins.add(`${apiUrlObject.protocol}//localhost:${apiUrlObject.port || "8000"}`);
  origins.add(`${apiUrlObject.protocol}//127.0.0.1:${apiUrlObject.port || "8000"}`);
  return [...origins];
}

function slugify(input) {
  return String(input)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function getJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Accept": "application/json",
      "Accept-Language": "en",
      ...(options.headers ?? {}),
    },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed ${response.status} for ${url}`);
  }
  return response.json();
}

function extractText(node) {
  return (node?.textContent ?? "").replace(/\s+/g, " ").trim();
}

async function collectDomAudit(page) {
  return page.evaluate(() => {
    const clientWidth = document.documentElement.clientWidth;
    const scrollWidth = document.documentElement.scrollWidth;
    const horizontalOverflow = scrollWidth > clientWidth + 1;

    const clippedText = [];
    const tinyInteractive = [];
    const longWords = [];

    const all = Array.from(document.querySelectorAll("body *"));

    for (const el of all) {
      const style = window.getComputedStyle(el);
      if (style.display === "none" || style.visibility === "hidden") continue;

      const rect = el.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) continue;

      const text = (el.textContent || "").trim();
      const hasText = text.length >= 12;
      const canClip =
        style.overflowX !== "visible" ||
        style.overflowY !== "visible" ||
        style.textOverflow === "ellipsis" ||
        style.webkitLineClamp !== "none";

      const clipsHoriz = el.scrollWidth > el.clientWidth + 2;
      const clipsVert = el.scrollHeight > el.clientHeight + 2;

      if (hasText && canClip && (clipsHoriz || clipsVert)) {
        clippedText.push({
          tag: el.tagName.toLowerCase(),
          className: (el.className || "").toString().slice(0, 160),
          text: text.slice(0, 120),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          scrollWidth: el.scrollWidth,
          clientWidth: el.clientWidth,
          scrollHeight: el.scrollHeight,
          clientHeight: el.clientHeight,
        });
      }

      if (el.matches("a, button, input, select, textarea, [role='button']")) {
        if (rect.width < 34 || rect.height < 34) {
          tinyInteractive.push({
            tag: el.tagName.toLowerCase(),
            className: (el.className || "").toString().slice(0, 160),
            text: text.slice(0, 80),
            width: Math.round(rect.width),
            height: Math.round(rect.height),
          });
        }
      }

      if (hasText) {
        const words = text.split(/\s+/);
        const longest = words.reduce((m, w) => Math.max(m, w.length), 0);
        if (longest >= 28 && rect.width < 420) {
          longWords.push({
            tag: el.tagName.toLowerCase(),
            className: (el.className || "").toString().slice(0, 160),
            longestWordLength: longest,
            text: text.slice(0, 120),
            width: Math.round(rect.width),
          });
        }
      }
    }

    return {
      url: location.href,
      title: document.title,
      horizontalOverflow,
      clientWidth,
      scrollWidth,
      clippedText: clippedText.slice(0, 25),
      tinyInteractive: tinyInteractive.slice(0, 25),
      longWords: longWords.slice(0, 25),
    };
  });
}

async function safeGoto(page, url) {
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForLoadState("networkidle", { timeout: 5000 }).catch(() => null);
    return null;
  } catch (error) {
    return error instanceof Error ? error.message : String(error);
  }
}

async function safeScreenshot(page, filePath) {
  try {
    await page.screenshot({ path: filePath, fullPage: true, timeout: 90000 });
    return null;
  } catch (error) {
    return error instanceof Error ? error.message : String(error);
  }
}

async function setLanguageSignals(context, locale) {
  await context.addCookies([
    {
      name: "pv_language",
      value: locale,
      url: baseUrl,
    },
  ]);

  await context.addInitScript((lang) => {
    try {
      localStorage.setItem("pv_language", lang);
    } catch {
      // ignore
    }
    document.cookie = `pv_language=${encodeURIComponent(lang)}; path=/`;
  }, locale);
}

async function createAuthState(browser) {
  const nonce = Date.now();
  const email = `visual.qa.${nonce}@example.com`;
  const password = "Password123!";

  const registerResponse = await fetch(`${apiBase}/api/v1/auth/register`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "Accept-Language": "en",
    },
    body: JSON.stringify({
      email,
      password,
      display_name: "Visual QA Bot",
    }),
  });

  if (!registerResponse.ok) {
    const body = await registerResponse.text().catch(() => "");
    throw new Error(`Failed to register visual audit user (${registerResponse.status}): ${body}`);
  }

  const registerPayload = await registerResponse.json();
  const accessToken = registerPayload?.access_token;
  if (!accessToken) {
    throw new Error("Register response did not include access_token");
  }

  let refreshToken = null;
  const setCookie = registerResponse.headers.get("set-cookie");
  if (setCookie) {
    const refreshMatch = setCookie.match(/pv_refresh_token=([^;]+)/);
    refreshToken = refreshMatch?.[1] ?? null;
  }

  const context = await browser.newContext({ baseURL: baseUrl, viewport: { width: 1280, height: 900 } });
  await setLanguageSignals(context, "en");
  const origins = candidateOrigins(baseUrl, apiBase);
  const cookies = [];
  for (const origin of origins) {
    cookies.push({
      name: "pv_access_token",
      value: accessToken,
      url: origin,
      httpOnly: false,
      secure: false,
      sameSite: "Lax",
    });
    if (refreshToken) {
      cookies.push({
        name: "pv_refresh_token",
        value: refreshToken,
        url: origin,
        httpOnly: false,
        secure: false,
        sameSite: "Lax",
      });
    }
  }
  await context.addCookies(cookies);

  const me = await context.request.get(`${apiBase}/api/v1/users/me`, {
    headers: {
      Accept: "application/json",
      "Accept-Language": "en",
    },
    timeout: 30000,
  });

  if (!me.ok()) {
    const body = await me.text().catch(() => "");
    throw new Error(`Failed to validate auth cookies (${me.status()}): ${body}`);
  }

  await context.storageState({ path: authStatePath });
  await context.close();
}

async function missionSlugForContext(context) {
  try {
    const response = await context.request.get(`${apiBase}/api/v1/missions`, {
      headers: { "Accept-Language": "en" },
      timeout: 30000,
    });
    if (!response.ok()) return null;
    const payload = await response.json();
    return payload?.missions?.[0]?.slug ?? null;
  } catch {
    return null;
  }
}

async function captureState({ page, locale, viewportId, routeId, pathUrl, report }) {
  const gotoError = await safeGoto(page, pathUrl);
  await page.waitForTimeout(350);

  const fileName = `${locale}_${viewportId}_${routeId}.png`;
  const filePath = path.join(outputRoot, fileName);
  const screenshotError = await safeScreenshot(page, filePath);

  const domAudit = await collectDomAudit(page);

  report.push({
    locale,
    viewport: viewportId,
    routeId,
    path: pathUrl,
    file: filePath,
    gotoError: gotoError ?? screenshotError,
    domAudit,
  });
}

async function captureInteractiveStates({ page, locale, viewportId, report }) {
  // Language dropdown
  await safeGoto(page, "/");
  const switcher = page.locator('button[aria-haspopup="menu"]').first();
  if (await switcher.count()) {
    await switcher.click().catch(() => null);
    await page.waitForTimeout(180);
    const file = path.join(outputRoot, `${locale}_${viewportId}_header-language-menu.png`);
    const screenshotError = await safeScreenshot(page, file);
    report.push({
      locale,
      viewport: viewportId,
      routeId: "header-language-menu",
      path: page.url(),
      file,
      gotoError: screenshotError,
      domAudit: await collectDomAudit(page),
    });
  }

  // Catalog advanced filters
  await safeGoto(page, "/catalog");
  const details = page.locator("details.pv-details").first();
  if (await details.count()) {
    await details.evaluate((el) => {
      el.open = true;
    }).catch(() => null);
    await page.waitForTimeout(180);
    const file = path.join(outputRoot, `${locale}_${viewportId}_catalog-advanced-filters.png`);
    const screenshotError = await safeScreenshot(page, file);
    report.push({
      locale,
      viewport: viewportId,
      routeId: "catalog-advanced-filters",
      path: page.url(),
      file,
      gotoError: screenshotError,
      domAudit: await collectDomAudit(page),
    });
  }
}

async function captureAuthInteractiveStates({ page, locale, viewportId, report }) {
  await safeGoto(page, "/dashboard");
  const accountTrigger = page.locator(".pv-header-user-trigger").first();
  if (await accountTrigger.count()) {
    await accountTrigger.click().catch(() => null);
    await page.waitForTimeout(200);
    const file = path.join(outputRoot, `${locale}_${viewportId}_header-account-menu.png`);
    const screenshotError = await safeScreenshot(page, file);
    report.push({
      locale,
      viewport: viewportId,
      routeId: "header-account-menu",
      path: page.url(),
      file,
      gotoError: screenshotError,
      domAudit: await collectDomAudit(page),
    });
  }
}

async function captureLoadingStateAttempt({ context, page, locale, viewportId, report }) {
  const cdp = await context.newCDPSession(page);
  await cdp.send("Network.enable");
  await cdp.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 450,
    downloadThroughput: 45 * 1024,
    uploadThroughput: 45 * 1024,
    connectionType: "cellular3g",
  });

  await safeGoto(page, "/");
  await page.click('a[href="/catalog"]').catch(() => null);
  await page.waitForTimeout(260);

  const file = path.join(outputRoot, `${locale}_${viewportId}_loading-transition-catalog.png`);
  const screenshotError = await safeScreenshot(page, file);
  report.push({
    locale,
    viewport: viewportId,
    routeId: "loading-transition-catalog",
    path: page.url(),
    file,
    gotoError: screenshotError,
    domAudit: await collectDomAudit(page),
  });

  await cdp.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 0,
    downloadThroughput: -1,
    uploadThroughput: -1,
    connectionType: "none",
  });
}

async function main() {
  await ensureDir(outputRoot);

  const [prompts, lessons, categories, contributors] = await Promise.all([
    getJson(`${apiBase}/api/v1/prompts?limit=12`).catch(() => []),
    getJson(`${apiBase}/api/v1/lessons`).catch(() => []),
    getJson(`${apiBase}/api/v1/categories`).catch(() => []),
    getJson(`${apiBase}/api/v1/contributors/top?limit=8`).catch(() => []),
  ]);

  const promptSlug = prompts[0]?.slug ?? "react-debug-checklist";
  const premiumPromptSlug = prompts.find((p) => p?.is_paid || p?.is_premium)?.slug ?? promptSlug;
  const lessonSlug = lessons[0]?.slug ?? "prompt-basics";
  const categorySlug = categories[0]?.slug ?? "development";
  const categoryId = categories[0]?.id ?? "";
  const contributorSlug = contributors[0]?.slug ?? "prompts-vault-curated";

  const publicRoutes = [
    { id: "home", path: "/" },
    { id: "catalog", path: "/catalog" },
    { id: "catalog-empty", path: "/catalog?q=zzzzzzzzzzzzzzzzzzzz" },
    {
      id: "catalog-filtered",
      path: categoryId
        ? `/catalog?category_id=${encodeURIComponent(categoryId)}&technique=chain_of_thought&sort=most_saved`
        : "/catalog?technique=chain_of_thought&sort=most_saved",
    },
    { id: "category", path: `/category/${encodeURIComponent(categorySlug)}` },
    { id: "prompt", path: `/prompt/${encodeURIComponent(promptSlug)}` },
    { id: "prompt-premium", path: `/prompt/${encodeURIComponent(premiumPromptSlug)}` },
    { id: "learn", path: "/learn" },
    { id: "lesson", path: `/learn/${encodeURIComponent(lessonSlug)}` },
    { id: "contributor", path: `/contributors/${encodeURIComponent(contributorSlug)}` },
    { id: "pricing", path: "/pricing" },
    { id: "login", path: "/login" },
    { id: "signup", path: "/signup" },
    { id: "not-found", path: "/__missing_visual_audit__" },
  ];

  const browser = await chromium.launch({ headless: true });

  await createAuthState(browser);

  const report = {
    generatedAt: new Date().toISOString(),
    baseUrl,
    apiBase,
    routes: {
      public: publicRoutes,
      auth: [],
    },
    captures: [],
  };

  for (const locale of locales) {
    for (const viewport of viewports) {
      // Public context
      const publicContext = await browser.newContext({
        baseURL: baseUrl,
        viewport: { width: viewport.width, height: viewport.height },
      });
      await setLanguageSignals(publicContext, locale);
      const publicPage = await publicContext.newPage();

      for (const route of publicRoutes) {
        await captureState({
          page: publicPage,
          locale,
          viewportId: viewport.id,
          routeId: route.id,
          pathUrl: route.path,
          report: report.captures,
        });
      }

      await captureInteractiveStates({
        page: publicPage,
        locale,
        viewportId: viewport.id,
        report: report.captures,
      });

      await captureLoadingStateAttempt({
        context: publicContext,
        page: publicPage,
        locale,
        viewportId: viewport.id,
        report: report.captures,
      });

      await publicContext.close();

      // Auth context
      const authContext = await browser.newContext({
        baseURL: baseUrl,
        viewport: { width: viewport.width, height: viewport.height },
        storageState: authStatePath,
      });
      await setLanguageSignals(authContext, locale);
      const authPage = await authContext.newPage();

      const missionSlug = await missionSlugForContext(authContext);
      const authRoutes = [
        { id: "dashboard", path: "/dashboard" },
        { id: "profile", path: "/profile" },
        { id: "wallet", path: "/wallet" },
        { id: "store", path: "/store" },
        { id: "missions", path: "/missions" },
        { id: "mission-detail", path: missionSlug ? `/missions/${encodeURIComponent(missionSlug)}` : "/missions" },
        { id: "onboarding", path: "/onboarding" },
        { id: "submit", path: "/submit" },
      ];

      report.routes.auth = authRoutes;

      for (const route of authRoutes) {
        await captureState({
          page: authPage,
          locale,
          viewportId: viewport.id,
          routeId: route.id,
          pathUrl: route.path,
          report: report.captures,
        });
      }

      await captureAuthInteractiveStates({
        page: authPage,
        locale,
        viewportId: viewport.id,
        report: report.captures,
      });

      await authContext.close();
    }
  }

  await browser.close();

  await ensureDir(path.dirname(reportPath));
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2), "utf8");

  console.log(`Saved ${report.captures.length} screenshots to ${outputRoot}`);
  console.log(`Report: ${reportPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});


import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";

const baseUrl = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";
const apiBase = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

const locales = ["en", "ru", "tt"];
const desktop = { width: 1440, height: 1024 };
const mobile = { width: 390, height: 844 };

const outputRoot = path.resolve("codex-visual-audit", "after-targeted");
const reportPath = path.resolve("codex-visual-audit", "after-targeted-report.json");
const authStatePath = path.resolve("codex-visual-audit", "auth-state.json");

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function getJson(url) {
  const response = await fetch(url, {
    headers: {
      Accept: "application/json",
      "Accept-Language": "en",
    },
  });
  if (!response.ok) {
    throw new Error(`Request failed ${response.status} for ${url}`);
  }
  return response.json();
}

async function safeGoto(page, pathUrl) {
  try {
    await page.goto(pathUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForLoadState("networkidle", { timeout: 6000 }).catch(() => null);
    return null;
  } catch (error) {
    return error instanceof Error ? error.message : String(error);
  }
}

async function safeShot(page, filePath) {
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

async function captureRoute({ page, locale, viewportId, routeId, pathUrl, report }) {
  const gotoError = await safeGoto(page, pathUrl);
  const file = path.join(outputRoot, `${locale}_${viewportId}_${routeId}.png`);
  const shotError = await safeShot(page, file);
  report.push({
    locale,
    viewport: viewportId,
    routeId,
    path: pathUrl,
    file,
    error: gotoError ?? shotError,
  });
}

async function captureMobileHeader({ page, locale, report }) {
  await captureRoute({
    page,
    locale,
    viewportId: "mobile",
    routeId: "home-header-language",
    pathUrl: "/",
    report,
  });
}

async function main() {
  await ensureDir(outputRoot);
  const hasAuthState = await fs
    .access(authStatePath)
    .then(() => true)
    .catch(() => false);
  if (!hasAuthState) {
    throw new Error(`Auth storage state not found at ${authStatePath}`);
  }

  const [prompts, lessons] = await Promise.all([
    getJson(`${apiBase}/api/v1/prompts?limit=16`).catch(() => []),
    getJson(`${apiBase}/api/v1/lessons`).catch(() => []),
  ]);

  const promptSlug = prompts[0]?.slug ?? "react-debug-checklist";
  const premiumPromptSlug = prompts.find((item) => item?.is_paid || item?.is_premium)?.slug ?? promptSlug;
  const lessonSlug = lessons[0]?.slug ?? "prompt-basics";

  const browser = await chromium.launch({ headless: true });
  const captures = [];

  for (const locale of locales) {
    const publicDesktop = await browser.newContext({
      baseURL: baseUrl,
      viewport: desktop,
    });
    await setLanguageSignals(publicDesktop, locale);
    const publicDesktopPage = await publicDesktop.newPage();

    const publicRoutes = [
      { id: "prompt", path: `/prompt/${encodeURIComponent(promptSlug)}` },
      { id: "prompt-premium", path: `/prompt/${encodeURIComponent(premiumPromptSlug)}` },
      { id: "lesson", path: `/learn/${encodeURIComponent(lessonSlug)}` },
      { id: "pricing", path: "/pricing" },
    ];

    for (const route of publicRoutes) {
      await captureRoute({
        page: publicDesktopPage,
        locale,
        viewportId: "desktop",
        routeId: route.id,
        pathUrl: route.path,
        report: captures,
      });
    }

    await publicDesktop.close();

    const authDesktop = await browser.newContext({
      baseURL: baseUrl,
      viewport: desktop,
      storageState: authStatePath,
    });
    await setLanguageSignals(authDesktop, locale);
    const authDesktopPage = await authDesktop.newPage();

    const authRoutes = [
      { id: "wallet", path: "/wallet" },
      { id: "missions", path: "/missions" },
    ];

    for (const route of authRoutes) {
      await captureRoute({
        page: authDesktopPage,
        locale,
        viewportId: "desktop",
        routeId: route.id,
        pathUrl: route.path,
        report: captures,
      });
    }

    await authDesktop.close();

    const mobileContext = await browser.newContext({
      baseURL: baseUrl,
      viewport: mobile,
    });
    await setLanguageSignals(mobileContext, locale);
    const mobilePage = await mobileContext.newPage();
    await captureMobileHeader({ page: mobilePage, locale, report: captures });
    await mobileContext.close();
  }

  await browser.close();

  const report = {
    generatedAt: new Date().toISOString(),
    baseUrl,
    apiBase,
    captures,
  };

  await fs.writeFile(reportPath, JSON.stringify(report, null, 2), "utf8");

  console.log(`Saved ${captures.length} screenshots to ${outputRoot}`);
  console.log(`Report: ${reportPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

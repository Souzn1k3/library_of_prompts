import { chromium } from "@playwright/test";

function parseArg(name, fallback) {
  const prefix = `--${name}=`;
  const raw = process.argv.find((arg) => arg.startsWith(prefix));
  if (!raw) return fallback;
  return raw.slice(prefix.length);
}

function toNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function average(values) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function percentile(values, p) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.min(sorted.length - 1, Math.max(0, Math.floor((sorted.length - 1) * p)));
  return sorted[index];
}

async function clickAndMeasure(page, href) {
  const link = page.locator(`a[href="${href}"]`).first();
  await link.waitFor({ state: "visible", timeout: 20000 });

  const start = performance.now();
  await Promise.all([
    page.waitForURL(
      (url) => {
        return url.pathname === href;
      },
      { timeout: 30000 },
    ),
    link.click(),
  ]);
  await page.waitForLoadState("networkidle");
  return performance.now() - start;
}

async function runRound(browser, baseUrl) {
  const context = await browser.newContext();
  const page = await context.newPage();
  const origin = new URL(baseUrl).origin;
  const requests = [];

  page.on("request", (request) => {
    const url = request.url();
    if (!url.startsWith(origin)) {
      return;
    }

    requests.push({
      url,
      type: request.resourceType(),
      ts: Date.now(),
    });
  });

  await page.goto(baseUrl, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForTimeout(1200);

  const homeToCatalogMs = await clickAndMeasure(page, "/catalog");
  const beforeCatalogIdle = requests.length;
  await page.waitForTimeout(2000);
  const catalogIdleRequests = requests.slice(beforeCatalogIdle);
  const catalogPromptRequests = catalogIdleRequests.filter((entry) => {
    const url = new URL(entry.url);
    return url.pathname.startsWith("/prompt/");
  }).length;

  const catalogToMissionsMs = await clickAndMeasure(page, "/missions");
  const missionsToPricingMs = await clickAndMeasure(page, "/pricing");
  const pricingToHomeMs = await clickAndMeasure(page, "/");

  const allPromptRequests = requests.filter((entry) => {
    const url = new URL(entry.url);
    return url.pathname.startsWith("/prompt/");
  }).length;

  await context.close();

  return {
    homeToCatalogMs,
    catalogToMissionsMs,
    missionsToPricingMs,
    pricingToHomeMs,
    catalogIdleRequestCount: catalogIdleRequests.length,
    catalogIdlePromptRequests: catalogPromptRequests,
    totalPromptRequests: allPromptRequests,
    totalRequests: requests.length,
  };
}

async function main() {
  const baseUrl = parseArg("baseUrl", process.env.BASE_URL || "http://localhost:3000");
  const label = parseArg("label", "run");
  const rounds = toNumber(parseArg("rounds", "6"), 6);
  const warmups = toNumber(parseArg("warmups", "1"), 1);

  const browser = await chromium.launch({ headless: true });
  const allRounds = [];
  try {
    for (let i = 0; i < warmups; i += 1) {
      await runRound(browser, baseUrl);
    }

    for (let i = 0; i < rounds; i += 1) {
      const result = await runRound(browser, baseUrl);
      allRounds.push(result);
    }
  } finally {
    await browser.close();
  }

  const navHomeToCatalog = allRounds.map((item) => item.homeToCatalogMs);
  const navCatalogToMissions = allRounds.map((item) => item.catalogToMissionsMs);
  const navMissionsToPricing = allRounds.map((item) => item.missionsToPricingMs);
  const navPricingToHome = allRounds.map((item) => item.pricingToHomeMs);
  const idlePromptRequests = allRounds.map((item) => item.catalogIdlePromptRequests);
  const idleTotalRequests = allRounds.map((item) => item.catalogIdleRequestCount);
  const totalRequests = allRounds.map((item) => item.totalRequests);

  const summary = {
    label,
    rounds,
    warmups,
    baseUrl,
    navigationMs: {
      homeToCatalog: {
        avg: average(navHomeToCatalog),
        p50: percentile(navHomeToCatalog, 0.5),
      },
      catalogToMissions: {
        avg: average(navCatalogToMissions),
        p50: percentile(navCatalogToMissions, 0.5),
      },
      missionsToPricing: {
        avg: average(navMissionsToPricing),
        p50: percentile(navMissionsToPricing, 0.5),
      },
      pricingToHome: {
        avg: average(navPricingToHome),
        p50: percentile(navPricingToHome, 0.5),
      },
    },
    catalogIdleRequests: {
      avg: average(idleTotalRequests),
      p50: percentile(idleTotalRequests, 0.5),
    },
    catalogIdlePromptRequests: {
      avg: average(idlePromptRequests),
      p50: percentile(idlePromptRequests, 0.5),
    },
    totalRequests: {
      avg: average(totalRequests),
      p50: percentile(totalRequests, 0.5),
    },
    raw: allRounds,
  };

  console.log(JSON.stringify(summary, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

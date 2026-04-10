import { expect, test, type Page } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";

async function preparePage(page: Page) {
  await page.context().addCookies([
    {
      name: "pv_language",
      value: "en",
      url: baseURL,
    },
  ]);

  await page.addInitScript(() => {
    window.localStorage.setItem("pv_language", "en");
    window.localStorage.setItem("pv-theme", "light");
  });
}

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));

  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.clientWidth + 1);
}

test("home renders the new product hero", async ({ page }, testInfo) => {
  await preparePage(page);
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toContainText(/proven ai prompt/i);
  await expect(page.getByRole("link", { name: /get starter pack/i })).toBeVisible();
  await expect(page.getByText(/personalized prompts/i).first()).toBeVisible();
  await expect(page.getByText(/curated for fast execution/i).first()).toBeVisible();
  await expect(page.getByRole("link", { name: /^see all$/i }).first()).toBeVisible();
  await expectNoHorizontalOverflow(page);

  await page.screenshot({ path: testInfo.outputPath("home-desktop.png"), fullPage: true });
});

test("dashboard guest state keeps a clear next action", async ({ page }, testInfo) => {
  await preparePage(page);
  await page.goto("/dashboard");

  await expect(page.getByRole("heading", { level: 1 })).toContainText(/dashboard/i);
  await expect(page.locator("#main-content").getByRole("link", { name: /^log in$/i }).first()).toBeVisible();
  await expect(page.locator("#main-content").getByRole("link", { name: /^sign up$/i }).first()).toBeVisible();
  await expectNoHorizontalOverflow(page);

  await page.screenshot({ path: testInfo.outputPath("dashboard-guest.png"), fullPage: true });
});

test("login and signup keep the primary auth fields visible", async ({ page }, testInfo) => {
  await preparePage(page);

  await page.goto("/login");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(/log in/i);
  await expect(page.getByLabel(/email/i)).toBeVisible();
  await expect(page.getByLabel(/password/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /continue/i })).toBeVisible();
  await expectNoHorizontalOverflow(page);

  await page.goto("/signup");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(/create account/i);
  await expect(page.getByLabel(/display name/i)).toBeVisible();
  await expect(page.getByLabel(/email/i)).toBeVisible();
  await expect(page.getByLabel(/password/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /create account/i })).toBeVisible();
  await expectNoHorizontalOverflow(page);

  await page.screenshot({ path: testInfo.outputPath("signup-desktop.png"), fullPage: true });
});

test("learning page surfaces tracks without layout breaks", async ({ page }, testInfo) => {
  await preparePage(page);
  await page.goto("/learn");

  await expect(page.getByRole("heading", { level: 1 })).toContainText(/learn/i);
  await expect(page.getByText(/recommended/i).first()).toBeVisible();
  await expect(page.getByText(/learning system/i).first()).toBeVisible();
  await expectNoHorizontalOverflow(page);

  await page.screenshot({ path: testInfo.outputPath("learn-desktop.png"), fullPage: true });
});

test("mobile home stays readable", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await preparePage(page);
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByRole("link", { name: /get starter pack/i })).toBeVisible();
  await expectNoHorizontalOverflow(page);

  await page.screenshot({ path: testInfo.outputPath("home-mobile.png"), fullPage: true });
});

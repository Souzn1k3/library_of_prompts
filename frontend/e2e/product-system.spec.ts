import { expect, test } from "@playwright/test";

const ROUTES = [
  "/",
  "/scenarios",
  "/growth",
  "/revenue",
  "/gtm",
  "/pricing",
  "/onboarding",
  "/login",
  "/signup",
];

for (const route of ROUTES) {
  test(`route shell is stable: ${route}`, async ({ page }) => {
    await page.goto(route, { waitUntil: "domcontentloaded" });

    await expect(page.locator("main")).toBeVisible();
    await expect(page.locator("h1, h2").first()).toBeVisible();

    const horizontalOverflow = await page.evaluate(() => {
      const root = document.documentElement;
      return root.scrollWidth - root.clientWidth;
    });
    expect(horizontalOverflow).toBeLessThanOrEqual(2);
  });
}

test("home and scenarios expose primary actions", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.locator(".pv-button-primary").first()).toBeVisible();

  await page.goto("/scenarios", { waitUntil: "domcontentloaded" });
  await expect(page.locator(".pv-button-primary").first()).toBeVisible();
});

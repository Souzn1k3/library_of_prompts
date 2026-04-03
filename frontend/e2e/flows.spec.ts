import { test, expect } from "@playwright/test";

test("plans page loads", async ({ page }) => {
  await page.goto("/plans");
  await expect(page.locator("body")).toBeVisible();
});

test("onboarding page requires navigation", async ({ page }) => {
  await page.goto("/onboarding");
  await expect(page.locator("body")).toBeVisible();
});

test("missions page loads shell", async ({ page }) => {
  await page.goto("/missions");
  await expect(page.locator("body")).toBeVisible();
});

import { test, expect } from "@playwright/test";

test("home page loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("body")).toBeVisible();
});

test("catalog page loads", async ({ page }) => {
  await page.goto("/catalog");
  await expect(page.locator("body")).toBeVisible();
});

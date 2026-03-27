import { test, expect } from "@playwright/test";

test("submit prompt page loads", async ({ page }) => {
  await page.goto("/submit");
  await expect(page.locator("body")).toBeVisible();
});

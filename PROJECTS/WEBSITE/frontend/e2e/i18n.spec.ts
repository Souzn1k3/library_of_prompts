import { test, expect } from "@playwright/test";

test("language switcher changes selection", async ({ page }) => {
  await page.goto("/");
  const switcher = page.locator('button[aria-haspopup="menu"]').first();
  await switcher.click();
  const ru = page.locator('[data-testid="lang-switch-ru"]:visible');
  await expect(ru).toBeVisible();
  await ru.click();
  await expect(switcher).toContainText("RU");
});

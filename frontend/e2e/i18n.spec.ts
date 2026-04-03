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

test("pricing heading updates after locale change", async ({ page }) => {
  await page.goto("/pricing");
  const switcher = page.locator('button[aria-haspopup="menu"]').first();

  await switcher.click();
  const en = page.locator('[data-testid="lang-switch-en"]:visible');
  await expect(en).toBeVisible();
  await en.click();
  await expect(page.locator("h1").first()).toContainText("Plans");

  await switcher.click();
  const ru = page.locator('[data-testid="lang-switch-ru"]:visible');
  await expect(ru).toBeVisible();
  await ru.click();
  await expect(page.locator("h1").first()).toContainText("Тарифы");
});

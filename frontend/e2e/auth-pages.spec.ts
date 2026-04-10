import { test, expect } from "@playwright/test";

test("login page renders", async ({ page }) => {
  await page.goto("/login");
  await expect(page.locator("body")).toBeVisible();
});

test("signup page renders", async ({ page }) => {
  await page.goto("/signup");
  await expect(page.locator("body")).toBeVisible();
});

test("login persists after page reload", async ({ page }) => {
  const unique = Date.now();
  const email = `refresh-auth-${unique}@example.com`;
  const password = "password123";
  const displayName = `Refresh Auth ${unique}`;

  await page.context().addCookies([
    {
      name: "pv_language",
      value: "en",
      url: "http://127.0.0.1:3000",
    },
  ]);

  await page.addInitScript(() => {
    window.localStorage.setItem("pv_language", "en");
  });

  await page.goto("/signup");
  await page.getByLabel(/display name/i).fill(displayName);
  await page.getByLabel(/^email$/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole("button", { name: /create account/i }).click();

  await page.waitForURL(/\/(dashboard|onboarding)/i);
  await expect(page.getByRole("link", { name: /^log in$/i })).toHaveCount(0);

  await page.reload();
  await page.waitForLoadState("networkidle");
  await expect(page.getByRole("link", { name: /^log in$/i })).toHaveCount(0);
});

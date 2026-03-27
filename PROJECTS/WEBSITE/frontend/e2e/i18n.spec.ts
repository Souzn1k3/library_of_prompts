import { test, expect } from "@playwright/test";

test("language switcher changes selection", async ({ page }) => {
  await page.goto("/");
  const ru = page.getByTestId("lang-switch-ru");
  await expect(ru).toBeVisible();
  await ru.click();
  await expect(ru).toHaveAttribute("aria-pressed", "true");
});

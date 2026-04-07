import { expect, test, type Page } from "@playwright/test";

type LanguageCase = {
  code: "en" | "ru" | "tt";
  heading: string;
  shouldRejectPatterns: RegExp[];
};

const languageCases: LanguageCase[] = [
  {
    code: "en",
    heading: "Learn",
    shouldRejectPatterns: [/[А-Яа-яЁёӘәӨөҮүҖҗҢңҺһ]/],
  },
  {
    code: "ru",
    heading: "Обучение",
    shouldRejectPatterns: [
      /\bworkflow\b/i,
      /\bprompt v[12]\b/i,
      /\bversion\b/i,
      /\bdeployment note\b/i,
      /\bcapstone\b/i,
      /\bfallback\b/i,
      /\broadmap\b/i,
      /\bdebug\b/i,
      /\bmini\b/i,
    ],
  },
  {
    code: "tt",
    heading: "Өйрәнү",
    shouldRejectPatterns: [
      /\bworkflow\b/i,
      /\bprompt v[12]\b/i,
      /\bversion\b/i,
      /\bdeployment note\b/i,
      /\bcapstone\b/i,
      /\bfallback\b/i,
      /\broadmap\b/i,
      /\bdebug\b/i,
      /\bmini\b/i,
    ],
  },
];

async function setLanguage(page: Page, language: "en" | "ru" | "tt") {
  await page.evaluate((lang) => {
    localStorage.setItem("pv_language", lang);
    document.cookie = `pv_language=${lang}; path=/`;
  }, language);
}

async function assertNoLeaks(text: string, patterns: RegExp[]) {
  const normalized = text.toLowerCase();
  for (const pattern of patterns) {
    expect(normalized).not.toMatch(pattern);
  }
}

test("learning copy stays localized across 3 languages", async ({ page }) => {
  for (const languageCase of languageCases) {
    await page.goto("/learn");
    await setLanguage(page, languageCase.code);
    await page.reload();
    await expect(page.getByRole("heading", { name: languageCase.heading }).first()).toBeVisible();

    const learnPageText = await page.locator("main").innerText();
    await assertNoLeaks(learnPageText, languageCase.shouldRejectPatterns);

    const firstCourseLink = page.locator("a[href^='/learn/course/']").first();
    await expect(firstCourseLink).toBeVisible();
    await firstCourseLink.click();
    await expect(page).toHaveURL(/\/learn\/course\/[^/?#]+$/);

    const coursePageText = await page.locator("main").innerText();
    await assertNoLeaks(coursePageText, languageCase.shouldRejectPatterns);

    const firstLessonLink = page.locator("a[href*='/learn/course/'][href*='/lesson/']").first();
    await expect(firstLessonLink).toBeVisible();
    await firstLessonLink.click();
    await expect(page).toHaveURL(/\/learn\/course\/[^/]+\/lesson\/[^/?#]+/);

    const lessonPageText = await page.locator("main").innerText();
    await assertNoLeaks(lessonPageText, languageCase.shouldRejectPatterns);
  }
});

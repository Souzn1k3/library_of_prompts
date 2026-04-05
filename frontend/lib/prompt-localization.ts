import { normalizeLanguage, type Language } from "@/lib/i18n";

type PromptTranslationEntry = {
  title: Partial<Record<Language, string>>;
  summary?: Partial<Record<Language, string>>;
};

const PROMPT_TRANSLATIONS_BY_SLUG: Record<string, PromptTranslationEntry> = {
  "react-debug-checklist": {
    title: {
      ru: "Чеклист отладки React",
      tt: "React хаталарын төзәтү чеклисты",
    },
    summary: {
      ru: "Помогает быстро находить ошибки React через структурированный процесс диагностики.",
      tt: "Структуралы диагностика адымнары ярдәмендә React хаталарын тиз табарга ярдәм итә.",
    },
  },
  "study-topic-explainer": {
    title: {
      ru: "Объяснение учебной темы",
      tt: "Уку темасын аңлатучы",
    },
    summary: {
      ru: "Преобразует сложные темы в понятные для студентов объяснения.",
      tt: "Катлаулы темаларны студентка аңлаешлы дәрес аңлатмаларына әйләндерә.",
    },
  },
  "enterprise-code-reviewer": {
    title: {
      ru: "Ревьюер кода для enterprise-проектов",
      tt: "Enterprise проектлары өчен код ревьюеры",
    },
    summary: {
      ru: "Шаблон глубокого ревью для критически важных изменений в коде.",
      tt: "Критик әһәмиятле код үзгәрешләре өчен тирән код-ревью шаблоны.",
    },
  },
};

function pickLocalizedText(
  values: Partial<Record<Language, string>> | undefined,
  language: Language,
): string | null {
  if (!values) {
    return null;
  }
  return values[language] ?? values.en ?? null;
}

export function localizePromptTitle(
  slug: string,
  title: string,
  language: Language | string | null | undefined,
): string {
  const normalizedLanguage = normalizeLanguage(language);
  const localized = pickLocalizedText(PROMPT_TRANSLATIONS_BY_SLUG[slug]?.title, normalizedLanguage);
  return localized ?? title;
}

export function localizePromptSummary(
  slug: string,
  summary: string | null,
  language: Language | string | null | undefined,
): string | null {
  const normalizedLanguage = normalizeLanguage(language);
  const localized = pickLocalizedText(PROMPT_TRANSLATIONS_BY_SLUG[slug]?.summary, normalizedLanguage);
  return localized ?? summary;
}

type PromptLike = {
  slug: string;
  title: string;
  summary: string | null;
};

export function localizePromptText<T extends PromptLike>(
  prompt: T,
  language: Language | string | null | undefined,
): T {
  return {
    ...prompt,
    title: localizePromptTitle(prompt.slug, prompt.title, language),
    summary: localizePromptSummary(prompt.slug, prompt.summary, language),
  };
}

export function localizePromptTextList<T extends PromptLike>(
  prompts: T[],
  language: Language | string | null | undefined,
): T[] {
  if (!prompts.length) {
    return prompts;
  }
  return prompts.map((prompt) => localizePromptText(prompt, language));
}

import type {
  ContributorTier,
  MissionProgressStatus,
  PromptDifficulty,
  PromptOutputType,
  PromptTechnique,
} from "@/lib/types";

import { translations as translationMap } from "./i18n/translations/index";

export const LANGUAGES = ["en", "ru", "tt"] as const;

export type Language = (typeof LANGUAGES)[number];

export const DEFAULT_LANGUAGE: Language = "ru";
export const LANGUAGE_STORAGE_KEY = "pv_language";
export const LANGUAGE_COOKIE_KEY = "pv_language";
export const LANGUAGE_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365;

export type TranslationKey = string;
type TranslationDictionary = Record<TranslationKey, string>;

export const translations: Record<Language, TranslationDictionary> = translationMap;

const techniqueKeyMap: Record<PromptTechnique, TranslationKey> = {
  zero_shot: "catalogFilters.zeroShot",
  few_shot: "catalogFilters.fewShot",
  chain_of_thought: "catalogFilters.chainOfThought",
  other: "catalogFilters.other",
};

const tierKeyMap: Record<string, TranslationKey> = {
  free: "tier.free",
  starter: "tier.starter",
  pro: "tier.pro",
  enterprise: "tier.enterprise",
};

const difficultyKeyMap: Record<PromptDifficulty, TranslationKey> = {
  beginner: "catalogFilters.difficultyBeginner",
  intermediate: "catalogFilters.difficultyIntermediate",
  advanced: "catalogFilters.difficultyAdvanced",
};

const outputTypeKeyMap: Record<PromptOutputType, TranslationKey> = {
  text: "catalogFilters.outputText",
  code: "catalogFilters.outputCode",
  structured: "catalogFilters.outputStructured",
};

const sortKeyMap: Record<string, TranslationKey> = {
  relevance: "catalogFilters.sortRelevance",
  trending: "catalogFilters.sortTrending",
  most_used: "catalogFilters.sortMostUsed",
  most_saved: "catalogFilters.sortMostSaved",
  newest: "catalogFilters.sortNewest",
};

const missionStatusKeyMap: Record<MissionProgressStatus, TranslationKey> = {
  not_started: "missions.status.not_started",
  in_progress: "missions.status.in_progress",
  completed: "missions.status.completed",
};

const contributorTierKeyMap: Record<ContributorTier, TranslationKey> = {
  new: "contributorTier.new",
  verified: "contributorTier.verified",
  top: "contributorTier.top",
};

export function normalizeLanguage(value: string | null | undefined): Language {
  const matched = detectLanguage(value);
  return matched ?? DEFAULT_LANGUAGE;
}

function detectLanguage(value: string | null | undefined): Language | null {
  if (!value) return null;
  const normalized = value.trim().toLowerCase().replace("_", "-");
  if (normalized === "ru" || normalized.startsWith("ru-")) return "ru";
  if (normalized === "tt" || normalized.startsWith("tt-")) return "tt";
  if (normalized === "en" || normalized.startsWith("en-")) return "en";
  return null;
}

export function getTranslation(lang: Language, key: TranslationKey): string {
  const localized = translations[lang][key];
  const fallback = translations[DEFAULT_LANGUAGE][key];

  if (localized && localized !== key) {
    return localized;
  }
  if (fallback) {
    return fallback;
  }
  return localized ?? key;
}

export function formatTranslation(
  lang: Language,
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
): string {
  const template = getTranslation(lang, key);
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (_match, token: string) => {
    const value = params[token];
    if (value === null || value === undefined) return "";
    return String(value);
  });
}

export function resolveLanguageFromAcceptLanguage(headerValue: string | null | undefined): Language {
  if (!headerValue) return DEFAULT_LANGUAGE;
  const candidates = headerValue.split(",");
  for (const candidate of candidates) {
    const token = candidate.trim();
    if (!token) continue;
    const tag = token.split(";")[0]?.trim();
    const matched = detectLanguage(tag);
    if (matched) {
      return matched;
    }
  }
  return DEFAULT_LANGUAGE;
}

export function extractLanguageFromCookie(cookieValue: string | null | undefined): Language | null {
  if (!cookieValue) return null;
  const chunks = cookieValue.split(";").map((chunk) => chunk.trim());
  const row = chunks.find((chunk) => chunk.startsWith(`${LANGUAGE_COOKIE_KEY}=`));
  if (!row) return null;
  return normalizeLanguage(decodeURIComponent(row.slice(LANGUAGE_COOKIE_KEY.length + 1)));
}

export function getClientLanguage(): Language {
  if (typeof window === "undefined") {
    return DEFAULT_LANGUAGE;
  }
  try {
    const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (stored) {
      return normalizeLanguage(stored);
    }
  } catch {
    /* ignore */
  }
  const fromCookie = extractLanguageFromCookie(document.cookie);
  if (fromCookie) {
    return fromCookie;
  }
  return normalizeLanguage(window.navigator.language);
}

export function getTechniqueTranslationKey(technique: PromptTechnique): TranslationKey {
  return techniqueKeyMap[technique] ?? "catalogFilters.other";
}

export function getTierTranslationKey(tier: string): TranslationKey {
  return tierKeyMap[tier] ?? "tier.free";
}

export function getDifficultyTranslationKey(difficulty: PromptDifficulty | string): TranslationKey {
  return difficultyKeyMap[difficulty as PromptDifficulty] ?? "catalogFilters.difficultyBeginner";
}

export function getOutputTypeTranslationKey(outputType: PromptOutputType | string): TranslationKey {
  return outputTypeKeyMap[outputType as PromptOutputType] ?? "catalogFilters.outputText";
}

export function getSortTranslationKey(sort: string): TranslationKey {
  return sortKeyMap[sort] ?? "catalogFilters.sortRelevance";
}

export function getMissionStatusTranslationKey(status: MissionProgressStatus): TranslationKey {
  return missionStatusKeyMap[status] ?? "missions.status.not_started";
}

export function getContributorTierTranslationKey(tier: ContributorTier): TranslationKey {
  return contributorTierKeyMap[tier] ?? "contributorTier.new";
}

export function languageToLocale(language: Language): string {
  switch (language) {
    case "ru":
      return "ru_RU";
    case "tt":
      return "tt_RU";
    default:
      return "en_US";
  }
}

export function languageToIntlLocale(language: Language): string {
  return languageToLocale(language).replace("_", "-");
}

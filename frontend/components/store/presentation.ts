import type { TranslationKey } from "@/lib/i18n";
import type { StoreItem } from "@/lib/types";

export type TranslateFn = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type TranslationParams = Record<string, string | number | null | undefined>;

export function kindLabel(kind: StoreItem["kind"], t: TranslateFn): string {
  const key = `store.kind.${kind}` as TranslationKey;
  const translated = t(key);
  return translated === key ? kind : translated;
}

export function sectionLabel(kind: StoreItem["kind"], t: TranslateFn): string {
  const key = `store.section.${kind}` as TranslationKey;
  const translated = t(key);
  return translated === key ? kindLabel(kind, t) : translated;
}

export function translationOrNull(
  t: TranslateFn,
  key: TranslationKey,
  params?: TranslationParams,
): string | null {
  const translated = t(key, params);
  return translated === key ? null : translated;
}

export function textOrNull(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

export function extractPromptTitle(item: StoreItem): string {
  const fromMeta = textOrNull(item.metadata?.prompt_title);
  if (fromMeta) return fromMeta;

  const normalized = item.title.trim();
  if (normalized.toLowerCase().startsWith("unlock:")) {
    return normalized.slice("unlock:".length).trim();
  }
  return normalized;
}

export function localizedStoreItemTitle(item: StoreItem, t: TranslateFn): string {
  const key = `store.item.${item.slug}.title` as TranslationKey;
  const directTranslation = translationOrNull(t, key);
  if (directTranslation) return directTranslation;

  if (item.kind === "premium_prompt_unlock" || item.slug.startsWith("unlock-")) {
    const dynamicTranslation = translationOrNull(t, "store.item.dynamicUnlock.title", {
      title: extractPromptTitle(item),
    });
    if (dynamicTranslation) return dynamicTranslation;
  }
  return item.title;
}

export function localizedStoreItemDescription(item: StoreItem, t: TranslateFn): string | null {
  const key = `store.item.${item.slug}.description` as TranslationKey;
  const directTranslation = translationOrNull(t, key);
  if (directTranslation) return directTranslation;

  if (item.kind === "premium_prompt_unlock" || item.slug.startsWith("unlock-")) {
    const dynamicTranslation = translationOrNull(t, "store.item.dynamicUnlock.description");
    if (dynamicTranslation) return dynamicTranslation;
  }
  return textOrNull(item.description);
}

export function localizedStarterReward(args: {
  slug: string;
  t: TranslateFn;
  fallbackTitle: string | null;
  fallbackBody: string | null;
}) {
  const title =
    translationOrNull(args.t, `store.item.${args.slug}.rewardTitle` as TranslationKey) ?? args.fallbackTitle;
  const body =
    translationOrNull(args.t, `store.item.${args.slug}.rewardBody` as TranslationKey) ?? args.fallbackBody;
  return { title, body };
}

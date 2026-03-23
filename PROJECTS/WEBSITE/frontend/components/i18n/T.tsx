"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { TranslationKey } from "@/lib/i18n";

export function T({ k }: { k: TranslationKey }) {
  const { t } = useI18n();
  return <>{t(k)}</>;
}

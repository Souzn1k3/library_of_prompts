import type { TranslationKey } from "@/lib/i18n";

export type WalletTranslate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

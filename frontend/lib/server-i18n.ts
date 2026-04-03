import { cookies, headers } from "next/headers";

import {
  DEFAULT_LANGUAGE,
  LANGUAGE_COOKIE_KEY,
  type Language,
  normalizeLanguage,
  resolveLanguageFromAcceptLanguage,
} from "@/lib/i18n";

export async function getServerLanguage(): Promise<Language> {
  const cookieStore = await cookies();
  const fromCookie = cookieStore.get(LANGUAGE_COOKIE_KEY)?.value;
  if (fromCookie) {
    return normalizeLanguage(fromCookie);
  }

  const headerStore = await headers();
  const acceptLanguage = headerStore.get("accept-language");
  return resolveLanguageFromAcceptLanguage(acceptLanguage) ?? DEFAULT_LANGUAGE;
}

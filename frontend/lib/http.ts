import { getTranslation, normalizeLanguage, type Language } from "./i18n";

export async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!text) {
    return undefined as T;
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    return undefined as T;
  }
}

type QueryPrimitive = string | number | boolean | null | undefined;
type QueryValue = QueryPrimitive | QueryPrimitive[];

function appendQueryParam(params: URLSearchParams, key: string, value: QueryValue): void {
  if (value == null) {
    return;
  }
  if (Array.isArray(value)) {
    for (const entry of value) {
      appendQueryParam(params, key, entry);
    }
    return;
  }
  const normalized = String(value);
  if (!normalized) {
    return;
  }
  params.append(key, normalized);
}

export function withQuery(path: string, query?: Record<string, QueryValue>): string {
  if (!query) {
    return path;
  }
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    appendQueryParam(params, key, value);
  }
  const suffix = params.toString();
  return suffix ? `${path}?${suffix}` : path;
}

function fallbackMessageForStatus(
  status: number,
  fallbackMessage?: string,
  language?: Language | string | null,
): string {
  const lang = normalizeLanguage(language);
  if (status === 401) {
    return getTranslation(lang, "api.http401");
  }
  if (status === 403) {
    return getTranslation(lang, "api.http403");
  }
  if (status === 404) {
    return getTranslation(lang, "api.http404");
  }
  if (status === 409) {
    return getTranslation(lang, "api.http409");
  }
  if (status === 422) {
    return getTranslation(lang, "api.http422");
  }
  if (status === 429) {
    return getTranslation(lang, "api.http429");
  }
  if (status >= 500) {
    return getTranslation(lang, "api.http500");
  }
  if (status === 0) {
    return getTranslation(lang, "api.httpNetwork");
  }
  return fallbackMessage ?? getTranslation(lang, "api.requestFailed");
}

function looksTechnicalError(message: string): boolean {
  const technicalPatterns = [
    /traceback/i,
    /exception/i,
    /stack trace/i,
    /sql/i,
    /token [a-z]+error/i,
    /undefined is not/i,
    /cannot read/i,
  ];
  return technicalPatterns.some((pattern) => pattern.test(message));
}

export function extractApiErrorMessage(
  data: unknown,
  status: number,
  fallbackMessage?: string,
  language?: Language | string | null,
): string {
  const fallback = fallbackMessageForStatus(status, fallbackMessage, language);
  if (typeof data === "object" && data) {
    if ("message" in data && typeof (data as { message: unknown }).message === "string") {
      const message = (data as { message: string }).message.trim();
      if (message && !looksTechnicalError(message)) {
        return message;
      }
    }
    if ("detail" in data) {
      const detail = (data as { detail: unknown }).detail;
      if (typeof detail === "string" && detail.trim() && !looksTechnicalError(detail)) {
        return detail;
      }
    }
  }
  return fallback;
}

import { getClientLanguage, getTranslation, normalizeLanguage, type Language } from "../i18n";
import { extractApiErrorMessage, parseJson } from "../http";

type NextFetchInit = RequestInit & {
  next?: { revalidate?: number; tags?: string[] };
};

export type ApiFetchInit = NextFetchInit & {
  accessToken?: string | null;
  language?: Language | string | null;
};

/**
 * Browser uses NEXT_PUBLIC_API_URL. Server components in Docker should set API_URL
 * to the internal service URL (e.g. http://api:8000) while keeping NEXT_PUBLIC_API_URL
 * for the public origin the browser calls.
 */
export function getApiBaseUrl(): string {
  const fallbackLocalApiUrl = "http://localhost:8000";

  if (typeof window === "undefined") {
    return (
      process.env.API_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      fallbackLocalApiUrl
    );
  }

  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // Keep frontend/backend on the same host in local dev so SameSite=Lax auth cookies work.
  const hostname = window.location.hostname || "localhost";
  const host = hostname.includes(":") ? `[${hostname}]` : hostname;
  return `http://${host}:8000`;
}

export class ApiRequestError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.body = body;
  }
}

export async function apiFetch<T>(path: string, init?: ApiFetchInit): Promise<T> {
  const url = `${getApiBaseUrl()}${path}`;
  const { accessToken, language, ...fetchInit } = init ?? {};
  const isAuthedRequest = Boolean(accessToken);
  const activeLanguage = normalizeLanguage(
    language ?? (typeof window !== "undefined" ? getClientLanguage() : undefined),
  );
  const includeCredentials = typeof window !== "undefined";
  let res: Response;
  try {
    res = await fetch(url, {
      ...fetchInit,
      cache: fetchInit.cache ?? (isAuthedRequest ? "no-store" : undefined),
      credentials: includeCredentials ? "include" : fetchInit.credentials,
      headers: {
        Accept: "application/json",
        "Accept-Language": activeLanguage,
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...(fetchInit.headers ?? {}),
      },
      next: isAuthedRequest ? undefined : fetchInit.next ?? { revalidate: 30 },
    });
  } catch {
    const message = extractApiErrorMessage(
      undefined,
      0,
      getTranslation(activeLanguage, "api.requestFailed"),
      activeLanguage,
    );
    throw new ApiRequestError(message, 0, null);
  }

  const data = await parseJson<unknown>(res);

  if (!res.ok) {
    const message = extractApiErrorMessage(
      data,
      res.status,
      getTranslation(activeLanguage, "api.requestFailed"),
      activeLanguage,
    );
    throw new ApiRequestError(message, res.status, data);
  }

  return data as T;
}

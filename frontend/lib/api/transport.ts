import { getClientLanguage, getTranslation, normalizeLanguage, type Language } from "../i18n";
import { extractApiErrorMessage, parseJson } from "../http";

type NextFetchInit = RequestInit & {
  next?: { revalidate?: number; tags?: string[] };
};

export type ApiFetchInit = NextFetchInit & {
  accessToken?: string | null;
  language?: Language | string | null;
  timeoutMs?: number | null;
};

const SERVER_FETCH_TIMEOUT_MS = 8000;

function resolveTimeoutMs(timeoutMs: number | null | undefined): number | undefined {
  if (typeof timeoutMs === "number" && Number.isFinite(timeoutMs) && timeoutMs > 0) {
    return timeoutMs;
  }
  if (typeof window === "undefined") {
    return SERVER_FETCH_TIMEOUT_MS;
  }
  return undefined;
}

function createTimedSignal(
  existingSignal: AbortSignal | null | undefined,
  timeoutMs: number | undefined,
): { signal?: AbortSignal; cleanup: () => void } {
  if (!existingSignal && !timeoutMs) {
    return { cleanup: () => undefined };
  }

  const controller = new AbortController();
  let timeoutId: ReturnType<typeof setTimeout> | undefined;

  const abortFromExistingSignal = () => {
    controller.abort();
  };

  if (existingSignal) {
    if (existingSignal.aborted) {
      controller.abort();
    } else {
      existingSignal.addEventListener("abort", abortFromExistingSignal, { once: true });
    }
  }

  if (timeoutMs) {
    timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  }

  return {
    signal: controller.signal,
    cleanup: () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      if (existingSignal) {
        existingSignal.removeEventListener("abort", abortFromExistingSignal);
      }
    },
  };
}

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
  const { accessToken, language, timeoutMs, ...fetchInit } = init ?? {};
  const isAuthedRequest = Boolean(accessToken);
  const activeLanguage = normalizeLanguage(
    language ?? (typeof window !== "undefined" ? getClientLanguage() : undefined),
  );
  const includeCredentials = typeof window !== "undefined";
  const { signal, cleanup } = createTimedSignal(fetchInit.signal, resolveTimeoutMs(timeoutMs));
  let res: Response;
  try {
    res = await fetch(url, {
      ...fetchInit,
      ...(signal ? { signal } : {}),
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
    cleanup();
    const message = extractApiErrorMessage(
      undefined,
      0,
      getTranslation(activeLanguage, "api.requestFailed"),
      activeLanguage,
    );
    throw new ApiRequestError(message, 0, null);
  }
  cleanup();

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

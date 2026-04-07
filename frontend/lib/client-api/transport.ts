import { ApiRequestError, getApiBaseUrl } from "../api";
import { emitAuthStateChange } from "../auth";
import { API_ENDPOINTS } from "../constants/api";
import { getClientLanguage, getTranslation, type Language } from "../i18n";
import { extractApiErrorMessage, parseJson } from "../http";

let refreshInFlight: Promise<boolean> | null = null;

function networkError(language: Language): ApiRequestError {
  return new ApiRequestError(
    extractApiErrorMessage(undefined, 0, getTranslation(language, "api.requestFailed"), language),
    0,
    null,
  );
}

function apiRequestError(
  {
    language,
    status,
    data,
  }: {
    language: Language;
    status: number;
    data: unknown;
  },
): ApiRequestError {
  const message = extractApiErrorMessage(
    data,
    status,
    getTranslation(language, "api.requestFailed"),
    language,
  );
  return new ApiRequestError(message, status, data);
}

function requestHeaders(language: string, initHeaders?: HeadersInit): HeadersInit {
  return {
    Accept: "application/json",
    "Accept-Language": language,
    ...(initHeaders ?? {}),
  };
}

export function jsonInit(method: "POST" | "PUT" | "DELETE", body?: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  };
}

async function refreshSession(language: string): Promise<boolean> {
  if (refreshInFlight) {
    return refreshInFlight;
  }
  refreshInFlight = (async () => {
    try {
      const res = await fetch(`${getApiBaseUrl()}${API_ENDPOINTS.auth.refresh}`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Accept-Language": language,
        },
        credentials: "include",
        cache: "no-store",
      });
      if (!res.ok) {
        emitAuthStateChange({ reason: "refresh" });
        return false;
      }
      await parseJson<unknown>(res);
      return true;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

async function authFetchRaw(path: string, init?: RequestInit, canRetry = true): Promise<Response> {
  const language = getClientLanguage();
  const url = `${getApiBaseUrl()}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: requestHeaders(language, init?.headers),
      credentials: "include",
      cache: "no-store",
    });
  } catch {
    throw networkError(language);
  }

  if (response.status === 401 && canRetry) {
    const refreshed = await refreshSession(language);
    if (refreshed) {
      return authFetchRaw(path, init, false);
    }
  }

  if (response.status === 401) {
    emitAuthStateChange({ reason: "expired" });
  }

  return response;
}

export async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const language = getClientLanguage();
  const res = await authFetchRaw(path, init);
  const data = await parseJson<unknown>(res);
  if (!res.ok) {
    throw apiRequestError({ language, status: res.status, data });
  }
  return data as T;
}

export async function authFetchNoContent(path: string, init?: RequestInit): Promise<void> {
  const language = getClientLanguage();
  const res = await authFetchRaw(path, init);
  if (!res.ok) {
    const data = await parseJson<unknown>(res);
    throw apiRequestError({ language, status: res.status, data });
  }
}

export async function optionalAuthJsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const language = getClientLanguage();
  let res: Response;
  try {
    res = await fetch(`${getApiBaseUrl()}${path}`, {
      ...init,
      headers: requestHeaders(language, init?.headers),
      credentials: "include",
      cache: "no-store",
    });
  } catch {
    throw networkError(language);
  }
  const data = await parseJson<unknown>(res);
  if (!res.ok) {
    throw apiRequestError({ language, status: res.status, data });
  }
  return data as T;
}

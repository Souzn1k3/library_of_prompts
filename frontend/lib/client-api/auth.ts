import { API_ENDPOINTS } from "../constants/api";
import { clearAuthSessionHint, emitAuthStateChange, markAuthSessionHint } from "../auth";
import type { UserProfile } from "../types";
import { authFetch, authFetchNoContent, jsonInit, optionalAuthJsonFetch } from "./transport";

export async function loginRequest(email: string, password: string): Promise<void> {
  await optionalAuthJsonFetch<unknown>(API_ENDPOINTS.auth.login, jsonInit("POST", { email, password }));
  markAuthSessionHint();
}

export async function registerRequest(
  email: string,
  password: string,
  displayName: string,
): Promise<void> {
  await optionalAuthJsonFetch<unknown>(
    API_ENDPOINTS.auth.register,
    jsonInit("POST", { email, password, display_name: displayName }),
  );
  markAuthSessionHint();
}

export async function logoutRequest(): Promise<void> {
  try {
    await authFetchNoContent(API_ENDPOINTS.auth.logout, jsonInit("POST", {}));
  } finally {
    clearAuthSessionHint();
    emitAuthStateChange({ reason: "logout" });
  }
}

export async function fetchMe(): Promise<UserProfile> {
  return authFetch<UserProfile>(API_ENDPOINTS.usersMe);
}

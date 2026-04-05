import { API_ENDPOINTS } from "../constants/api";
import { emitAuthStateChange } from "../auth";
import type { UserProfile } from "../types";
import { authFetch, authFetchNoContent, jsonInit, optionalAuthJsonFetch } from "./transport";

export async function loginRequest(email: string, password: string): Promise<void> {
  await optionalAuthJsonFetch<unknown>(API_ENDPOINTS.auth.login, jsonInit("POST", { email, password }));
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
}

export async function logoutRequest(): Promise<void> {
  try {
    await authFetchNoContent(API_ENDPOINTS.auth.logout, jsonInit("POST", {}));
  } finally {
    emitAuthStateChange({ reason: "logout" });
  }
}

export async function fetchMe(): Promise<UserProfile> {
  return authFetch<UserProfile>(API_ENDPOINTS.usersMe);
}

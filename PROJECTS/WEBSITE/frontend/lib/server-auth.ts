import { cookies } from "next/headers";

const ACCESS_TOKEN_COOKIE =
  process.env.NEXT_PUBLIC_ACCESS_TOKEN_COOKIE_NAME ??
  process.env.ACCESS_TOKEN_COOKIE_NAME ??
  "pv_access_token";
const REFRESH_TOKEN_COOKIE =
  process.env.NEXT_PUBLIC_REFRESH_TOKEN_COOKIE_NAME ??
  process.env.REFRESH_TOKEN_COOKIE_NAME ??
  "pv_refresh_token";

export async function getServerAccessToken(): Promise<string | undefined> {
  const jar = await cookies();
  return jar.get(ACCESS_TOKEN_COOKIE)?.value;
}

export async function getServerAuthCookieState(): Promise<{
  hasAccessToken: boolean;
  hasRefreshToken: boolean;
  hasAnyAuthCookie: boolean;
}> {
  const jar = await cookies();
  const hasAccessToken = Boolean(jar.get(ACCESS_TOKEN_COOKIE)?.value);
  const hasRefreshToken = Boolean(jar.get(REFRESH_TOKEN_COOKIE)?.value);

  return {
    hasAccessToken,
    hasRefreshToken,
    hasAnyAuthCookie: hasAccessToken || hasRefreshToken,
  };
}

import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";

const baseUrl = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";
const baseUrlObject = new URL(baseUrl);
const inferredApiBase = `${baseUrlObject.protocol}//${baseUrlObject.hostname}:8000`;
const apiBase = process.env.API_BASE_URL ?? inferredApiBase;
const authStatePath = path.resolve("codex-visual-audit", "auth-state.json");

function candidateOrigins(base, api) {
  const baseUrlObject = new URL(base);
  const apiUrlObject = new URL(api);
  const protocol = baseUrlObject.protocol;
  const preferredPort = baseUrlObject.port || "3000";
  const origins = new Set([
    base,
    api,
    `${protocol}//localhost:${preferredPort}`,
    `${protocol}//127.0.0.1:${preferredPort}`,
    `${protocol}//localhost:8000`,
    `${protocol}//127.0.0.1:8000`,
  ]);
  origins.add(`${apiUrlObject.protocol}//localhost:${apiUrlObject.port || "8000"}`);
  origins.add(`${apiUrlObject.protocol}//127.0.0.1:${apiUrlObject.port || "8000"}`);
  return [...origins];
}

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function main() {
  const nonce = Date.now();
  const email = `visual.qa.${nonce}@example.com`;
  const password = "Password123!";

  const registerResponse = await fetch(`${apiBase}/api/v1/auth/register`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "Accept-Language": "en",
    },
    body: JSON.stringify({
      email,
      password,
      display_name: "Visual QA Bot",
    }),
  });

  if (!registerResponse.ok) {
    const body = await registerResponse.text().catch(() => "");
    throw new Error(`Failed to register visual audit user (${registerResponse.status}): ${body}`);
  }

  const registerPayload = await registerResponse.json();
  const accessToken = registerPayload?.access_token;
  if (!accessToken) {
    throw new Error("Register response did not include access_token");
  }

  let refreshToken = null;
  const setCookie = registerResponse.headers.get("set-cookie");
  if (setCookie) {
    const refreshMatch = setCookie.match(/pv_refresh_token=([^;]+)/);
    refreshToken = refreshMatch?.[1] ?? null;
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    baseURL: baseUrl,
    viewport: { width: 1280, height: 900 },
  });

  const origins = candidateOrigins(baseUrl, apiBase);
  const cookies = [];
  for (const origin of origins) {
    cookies.push({
      name: "pv_access_token",
      value: accessToken,
      url: origin,
      httpOnly: false,
      secure: false,
      sameSite: "Lax",
    });
    if (refreshToken) {
      cookies.push({
        name: "pv_refresh_token",
        value: refreshToken,
        url: origin,
        httpOnly: false,
        secure: false,
        sameSite: "Lax",
      });
    }
  }
  cookies.push({
    name: "pv_language",
    value: "en",
    url: baseUrl,
  });
  await context.addCookies(cookies);

  const me = await context.request.get(`${apiBase}/api/v1/users/me`, {
    headers: {
      Accept: "application/json",
      "Accept-Language": "en",
    },
    timeout: 30000,
  });

  if (!me.ok()) {
    const body = await me.text().catch(() => "");
    throw new Error(`Failed to validate auth cookies (${me.status()}): ${body}`);
  }

  await ensureDir(path.dirname(authStatePath));
  await context.storageState({ path: authStatePath });
  await context.close();
  await browser.close();

  console.log(`Saved auth state to ${authStatePath}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

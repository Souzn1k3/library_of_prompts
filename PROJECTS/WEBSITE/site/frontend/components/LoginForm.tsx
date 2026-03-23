"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { ApiRequestError } from "@/lib/api";
import { setToken } from "@/lib/auth";
import { loginRequest } from "@/lib/client-api";

export function LoginForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setPending(true);
    const fd = new FormData(e.currentTarget);
    const email = String(fd.get("email") ?? "");
    const password = String(fd.get("password") ?? "");
    try {
      const token = await loginRequest(email, password);
      setToken(token.access_token);
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Failed to log in");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </div>
      ) : null}
      <div className="space-y-1">
        <label htmlFor="email" className="text-xs font-medium text-zinc-700">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
          placeholder="you@example.com"
        />
      </div>
      <div className="space-y-1">
        <label htmlFor="password" className="text-xs font-medium text-zinc-700">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          autoComplete="current-password"
          minLength={8}
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
          placeholder="••••••••"
        />
      </div>
      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-60"
      >
        {pending ? "Signing in…" : "Continue"}
      </button>
      <p className="text-center text-sm text-zinc-600">
        No account?{" "}
        <Link href="/signup" className="font-medium text-zinc-900 underline">
          Sign up
        </Link>
      </p>
    </form>
  );
}

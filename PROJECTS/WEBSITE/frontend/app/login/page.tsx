import { redirect } from "next/navigation";

import { LoginForm } from "@/components/LoginForm";
import { T } from "@/components/i18n/T";
import { getServerAuthCookieState } from "@/lib/server-auth";

export default async function LoginPage() {
  const authState = await getServerAuthCookieState();
  if (authState.hasAnyAuthCookie) {
    redirect("/dashboard");
  }

  return (
    <div className="mx-auto max-w-md space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          <T k="login.pageTitle" />
        </h1>
        <p className="text-sm text-zinc-600">
          <T k="login.pageSubtitle" />
        </p>
      </div>
      <LoginForm />
    </div>
  );
}

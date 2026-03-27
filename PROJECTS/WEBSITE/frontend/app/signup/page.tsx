import { redirect } from "next/navigation";

import { SignupForm } from "@/components/SignupForm";
import { T } from "@/components/i18n/T";
import { getServerAuthCookieState } from "@/lib/server-auth";

export default async function SignupPage() {
  const authState = await getServerAuthCookieState();
  if (authState.hasAnyAuthCookie) {
    redirect("/dashboard");
  }

  return (
    <div className="mx-auto max-w-md space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          <T k="signup.pageTitle" />
        </h1>
        <p className="text-sm text-zinc-600">
          <T k="signup.pageSubtitle" />
        </p>
      </div>
      <SignupForm />
    </div>
  );
}

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
    <div className="mx-auto max-w-xl space-y-6">
      <div className="space-y-2">
        <p className="pv-kicker">
          <T k="signup.pageTitle" />
        </p>
        <h1 className="pv-title text-zinc-900">
          <T k="signup.pageTitle" />
        </h1>
        <p className="text-sm text-zinc-600">
          <T k="signup.pageSubtitle" />
        </p>
      </div>
      <div className="pv-panel px-5 py-5 sm:px-6">
        <SignupForm />
      </div>
    </div>
  );
}

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
    <div className="mx-auto max-w-5xl">
      <div className="grid gap-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,0.85fr)] lg:items-start">
        <section className="pv-hero px-6 py-7 sm:px-8 sm:py-8">
          <h1 className="pv-title whitespace-nowrap text-zinc-900">
            <T k="signup.pageTitle" />
          </h1>
          <p className="mt-3 pv-lead max-w-xl">
            <T k="signup.pageSubtitle" />
          </p>
        </section>
        <div className="pv-panel px-5 py-5 sm:px-6">
          <SignupForm />
        </div>
      </div>
    </div>
  );
}

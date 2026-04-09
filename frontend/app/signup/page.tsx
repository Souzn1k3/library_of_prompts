import Link from "next/link";

import { AuthScreen } from "@/components/auth/AuthScreen";
import { SignupForm } from "@/components/SignupForm";
import { T } from "@/components/i18n/T";

export default function SignupPage() {
  return (
    <AuthScreen
      eyebrow={<T k="brand.name" />}
      title={<T k="signup.pageTitle" />}
      subtitle={<T k="signup.pageSubtitle" />}
      items={[
        {
          title: <T k="onboarding.pageTitle" />,
          body: <T k="onboarding.pageSubtitle" />,
        },
        {
          title: <T k="home.startLearning" />,
          body: <T k="learn.learningSystemBody" />,
        },
        {
          title: <T k="nav.dashboard" />,
          body: <T k="dashboard.subtitle" />,
        },
      ]}
      actions={
        <>
          <Link href="/learn" className="pv-button-secondary !w-auto">
            <T k="learn.title" />
          </Link>
          <Link href="/catalog" className="pv-button-secondary !w-auto">
            <T k="home.explorePrompts" />
          </Link>
        </>
      }
      form={
        <div className="space-y-5">
          <div className="space-y-2">
            <p className="pv-kicker">
              <T k="nav.signup" />
            </p>
            <h2 className="text-2xl font-semibold tracking-[-0.05em] text-zinc-950">
              <T k="signup.pageTitle" />
            </h2>
            <p className="text-sm leading-relaxed text-zinc-600">
              <T k="signup.pageSubtitle" />
            </p>
          </div>
          <div className="pv-form-card">
            <SignupForm />
          </div>
        </div>
      }
    />
  );
}

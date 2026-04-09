import Link from "next/link";

import { AuthScreen } from "@/components/auth/AuthScreen";
import { LoginForm } from "@/components/LoginForm";
import { T } from "@/components/i18n/T";

export default function LoginPage() {
  return (
    <AuthScreen
      eyebrow={<T k="home.kicker" />}
      title={<T k="login.pageTitle" />}
      subtitle={<T k="login.pageSubtitle" />}
      items={[
        {
          title: <T k="home.explorePrompts" />,
          body: <T k="home.subtitle" />,
        },
        {
          title: <T k="learn.title" />,
          body: <T k="learn.releaseSubtitle" />,
        },
        {
          title: <T k="dashboard.title" />,
          body: <T k="dashboard.finishOnboardingTitle" />,
        },
      ]}
      actions={
        <>
          <Link href="/catalog" className="pv-button-secondary !w-auto">
            <T k="home.explorePrompts" />
          </Link>
          <Link href="/plans" className="pv-button-secondary !w-auto">
            <T k="nav.plans" />
          </Link>
        </>
      }
      form={
        <div className="space-y-5">
          <div className="space-y-2">
            <p className="pv-kicker">
              <T k="nav.login" />
            </p>
            <h2 className="text-2xl font-semibold tracking-[-0.05em] text-zinc-950">
              <T k="login.pageTitle" />
            </h2>
            <p className="text-sm leading-relaxed text-zinc-600">
              <T k="login.pageSubtitle" />
            </p>
          </div>
          <div className="pv-form-card">
            <LoginForm />
          </div>
        </div>
      }
    />
  );
}

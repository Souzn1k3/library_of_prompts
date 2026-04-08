import Link from "next/link";

import { LoginForm } from "@/components/LoginForm";
import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";

export default function LoginPage() {
  return (
    <div className="pv-page mx-auto max-w-5xl">
      <PageIntro
        breadcrumbs={[
          { label: <T k="brand.name" />, href: "/" },
          { label: <T k="nav.login" /> },
        ]}
        eyebrow={<T k="nav.login" />}
        title={<T k="login.pageTitle" />}
        description={<T k="login.pageSubtitle" />}
        actions={(
          <Link href="/signup" className="pv-button-secondary">
            <T k="signup.pageTitle" />
          </Link>
        )}
      />

      <section className="pv-panel px-5 py-5 sm:px-6">
        <LoginForm />
      </section>
    </div>
  );
}

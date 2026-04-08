import Link from "next/link";

import { SignupForm } from "@/components/SignupForm";
import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";

export default function SignupPage() {
  return (
    <div className="pv-page mx-auto max-w-5xl">
      <PageIntro
        breadcrumbs={[
          { label: <T k="brand.name" />, href: "/" },
          { label: <T k="nav.signup" /> },
        ]}
        eyebrow={<T k="nav.signup" />}
        title={<T k="signup.pageTitle" />}
        description={<T k="signup.pageSubtitle" />}
        actions={(
          <Link href="/login" className="pv-button-secondary">
            <T k="login.pageTitle" />
          </Link>
        )}
      />

      <section className="pv-panel px-5 py-5 sm:px-6">
        <SignupForm />
      </section>
    </div>
  );
}

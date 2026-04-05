import Link from "next/link";

import { SubmitPromptForm } from "@/components/SubmitPromptForm";
import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { getServerAuthCookieState } from "@/lib/server-auth";

export default async function SubmitPage() {
  const authState = await getServerAuthCookieState();
  const isAuthenticated = authState.hasAnyAuthCookie;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageIntro
        breadcrumbs={
          isAuthenticated
            ? [
                { label: <T k="nav.dashboard" />, href: "/dashboard" },
                { label: <T k="submit.pageTitle" /> },
              ]
            : [
                { label: <T k="brand.name" />, href: "/" },
                { label: <T k="submit.pageTitle" /> },
              ]
        }
        eyebrow={<T k="submit.pageTitle" />}
        title={<T k="submit.pageTitle" />}
        description={<T k="submit.pageSubtitle" />}
        hint={isAuthenticated ? <T k="dashboard.submitAnother" /> : <T k="submit.authRequired" />}
        actions={
          isAuthenticated ? (
            <>
              <Link href="/dashboard" className="pv-button-secondary">
                <T k="nav.dashboard" />
              </Link>
              <Link href="/catalog" className="pv-inline-link">
                <T k="nav.catalog" />
                <span aria-hidden="true">↗</span>
              </Link>
            </>
          ) : (
            <>
              <Link href="/login" className="pv-button-secondary">
                <T k="nav.login" />
              </Link>
              <Link href="/signup" className="pv-button-primary">
                <T k="nav.signup" />
              </Link>
            </>
          )
        }
      >
        <div className="flex flex-wrap gap-2">
          <span className="pv-chip-brand">
            <T k="catalogFilters.technique" />
          </span>
          <span className="pv-chip">
            <T k="submit.advancedOptions" />
          </span>
        </div>
      </PageIntro>
      <SubmitPromptForm />
    </div>
  );
}

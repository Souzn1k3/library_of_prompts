import Link from "next/link";
import { redirect } from "next/navigation";

import { SubmitPromptForm } from "@/components/SubmitPromptForm";
import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { getServerAuthCookieState } from "@/lib/server-auth";

export default async function SubmitPage() {
  const authState = await getServerAuthCookieState();
  if (!authState.hasAnyAuthCookie) {
    redirect("/login");
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageIntro
        breadcrumbs={[
          { label: <T k="nav.dashboard" />, href: "/dashboard" },
          { label: <T k="submit.pageTitle" /> },
        ]}
        eyebrow={<T k="submit.pageTitle" />}
        title={<T k="submit.pageTitle" />}
        description={<T k="submit.pageSubtitle" />}
        hint={<T k="dashboard.submitAnother" />}
        actions={
          <>
            <Link href="/dashboard" className="pv-button-secondary">
              <T k="nav.dashboard" />
            </Link>
            <Link href="/catalog" className="pv-inline-link">
              <T k="nav.catalog" />
              <span aria-hidden="true">↗</span>
            </Link>
          </>
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

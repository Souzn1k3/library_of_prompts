import type { ReactNode } from "react";

import { T } from "@/components/i18n/T";

type AuthShellProps = {
  titleKey: "login.pageTitle" | "signup.pageTitle";
  subtitleKey: "login.pageSubtitle" | "signup.pageSubtitle";
  formTitleKey: "login.pageTitle" | "signup.pageTitle";
  formSubtitleKey: "login.pageSubtitle" | "signup.pageSubtitle";
  children: ReactNode;
};

export function AuthShell({
  titleKey,
  subtitleKey,
  formTitleKey,
  formSubtitleKey,
  children,
}: AuthShellProps) {
  return (
    <div className="mx-auto max-w-6xl">
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(360px,420px)]">
        <section className="pv-hero px-6 py-7 sm:px-8 sm:py-9">
          <div className="flex h-full flex-col gap-8">
            <div className="space-y-4">
              <span className="pv-chip-brand w-fit">
                <T k="brand.name" />
              </span>
              <div className="space-y-3">
                <h1 className="pv-display max-w-[10ch] text-zinc-950">
                  <T k={titleKey} />
                </h1>
                <p className="pv-lead max-w-2xl">
                  <T k={subtitleKey} />
                </p>
              </div>
            </div>

            <div className="pv-auth-card-grid">
              <article className="pv-auth-card">
                <p className="pv-auth-card-title">
                  <T k="nav.catalog" />
                </p>
                <p className="pv-auth-card-body">
                  <T k="home.structuredLibraryBody" />
                </p>
              </article>
              <article className="pv-auth-card">
                <p className="pv-auth-card-title">
                  <T k="learn.title" />
                </p>
                <p className="pv-auth-card-body">
                  <T k="home.builtToLearnBody" />
                </p>
              </article>
              <article className="pv-auth-card">
                <p className="pv-auth-card-title">
                  <T k="dashboard.title" />
                </p>
                <p className="pv-auth-card-body">
                  <T k="home.seriousToolBody" />
                </p>
              </article>
            </div>

            <div className="rounded-[1.35rem] border border-[var(--pv-border)] bg-white px-5 py-4">
              <p className="pv-kicker">
                <T k="home.smartPicks" />
              </p>
              <p className="mt-3 text-sm leading-relaxed text-zinc-600">
                <T k="dashboard.subtitle" />
              </p>
            </div>
          </div>
        </section>

        <section className="pv-panel px-5 py-5 sm:px-6 sm:py-6">
          <div className="space-y-5">
            <div className="space-y-2">
              <p className="pv-kicker">
                <T k="brand.name" />
              </p>
              <h2 className="text-[1.55rem] font-semibold tracking-[-0.05em] text-zinc-950">
                <T k={formTitleKey} />
              </h2>
              <p className="text-sm leading-relaxed text-zinc-600">
                <T k={formSubtitleKey} />
              </p>
            </div>

            {children}
          </div>
        </section>
      </div>
    </div>
  );
}

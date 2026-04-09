import type { ReactNode } from "react";

import { T } from "@/components/i18n/T";

type AuthShellProps = {
  titleKey: "login.pageTitle" | "signup.pageTitle";
  children: ReactNode;
};

export function AuthShell({ titleKey, children }: AuthShellProps) {
  return (
    <div className="mx-auto max-w-[560px]">
      <section className="pv-panel px-5 py-5 sm:px-6 sm:py-6">
        <div className="space-y-4">
          <div className="space-y-2">
            <p className="pv-kicker">
              <T k="brand.name" />
            </p>
            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-zinc-950 sm:text-4xl">
              <T k={titleKey} />
            </h1>
          </div>

          {children}
        </div>
      </section>
    </div>
  );
}

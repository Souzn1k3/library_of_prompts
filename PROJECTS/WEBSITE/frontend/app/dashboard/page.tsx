import Link from "next/link";

import { DashboardClient } from "@/components/DashboardClient";
import { T } from "@/components/i18n/T";

export default function DashboardPage() {
  return (
    <div className="pv-page">
      <section className="pv-panel px-6 py-7 sm:px-8 sm:py-8">
        <p className="pv-kicker">
          <T k="dashboard.title" />
        </p>
        <h1 className="mt-3 pv-title text-zinc-950">
          <T k="dashboard.title" />
        </h1>
        <p className="mt-3 max-w-3xl text-base leading-relaxed text-[var(--pv-muted)]">
          <T k="dashboard.subtitle" />
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link href="/catalog" className="pv-button-primary">
            <T k="home.explorePrompts" />
          </Link>
          <Link href="/missions" className="pv-button-secondary">
            <T k="nav.missions" />
          </Link>
        </div>
      </section>
      <DashboardClient />
    </div>
  );
}

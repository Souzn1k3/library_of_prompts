import Link from "next/link";

import { MissionsClient } from "@/components/MissionsClient";
import { T } from "@/components/i18n/T";

export default function MissionsPage() {
  return (
    <div className="pv-page">
      <section className="pv-panel px-6 py-7 sm:px-8 sm:py-8">
        <p className="pv-kicker">
          <T k="missions.title" />
        </p>
        <h1 className="mt-3 pv-title text-zinc-950">
          <T k="missions.title" />
        </h1>
        <p className="mt-3 max-w-3xl text-base leading-relaxed text-[var(--pv-muted)]">
          <T k="missions.subtitle" />
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link href="/wallet" className="pv-button-primary">
            <T k="nav.wallet" />
          </Link>
          <Link href="/store" className="pv-button-secondary">
            <T k="nav.store" />
          </Link>
        </div>
      </section>
      <MissionsClient />
    </div>
  );
}

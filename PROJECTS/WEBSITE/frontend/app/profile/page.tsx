import Link from "next/link";

import { ProfileClient } from "@/components/ProfileClient";
import { T } from "@/components/i18n/T";

export default function ProfilePage() {
  return (
    <div className="pv-page">
      <section className="pv-panel px-6 py-7 sm:px-8 sm:py-8">
        <p className="pv-kicker">
          <T k="profile.title" />
        </p>
        <h1 className="mt-3 pv-title text-zinc-950">
          <T k="profile.title" />
        </h1>
        <p className="mt-3 max-w-3xl text-base leading-relaxed text-[var(--pv-muted)]">
          <T k="profile.subtitle" />
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link href="/dashboard" className="pv-button-primary">
            <T k="nav.dashboard" />
          </Link>
          <Link href="/pricing" className="pv-button-secondary">
            <T k="nav.plans" />
          </Link>
        </div>
      </section>
      <ProfileClient />
    </div>
  );
}

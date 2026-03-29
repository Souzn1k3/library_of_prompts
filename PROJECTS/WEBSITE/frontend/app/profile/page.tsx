import Link from "next/link";

import { ProfileClient } from "@/components/ProfileClient";
import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";

export default function ProfilePage() {
  return (
    <div className="pv-page">
      <PageIntro
        breadcrumbs={[
          { label: <T k="nav.dashboard" />, href: "/dashboard" },
          { label: <T k="footer.account" /> },
          { label: <T k="profile.title" /> },
        ]}
        eyebrow={<T k="profile.title" />}
        title={<T k="profile.title" />}
        description={<T k="profile.subtitle" />}
        hint={<T k="dashboard.manageBilling" />}
        actions={
          <>
            <Link href="/dashboard" className="pv-button-primary">
              <T k="nav.dashboard" />
            </Link>
            <Link href="/pricing" className="pv-button-secondary">
              <T k="nav.billing" />
            </Link>
            <Link href="/wallet" className="pv-inline-link">
              <T k="nav.wallet" />
              <span aria-hidden="true">↗</span>
            </Link>
          </>
        }
      />
      <ProfileClient />
    </div>
  );
}

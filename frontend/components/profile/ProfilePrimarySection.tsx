"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { ProfileAccountOverview } from "@/components/profile/ProfileAccountOverview";
import { ProfileActionsPanel } from "@/components/profile/ProfileActionsPanel";
import { ProfileMembershipPanel } from "@/components/profile/ProfileMembershipPanel";
import { ProfileTelegramCard } from "@/components/profile/ProfileTelegramCard";
import type {
  BillingStatus,
  OnboardingProfile,
  SellerMarketplaceSummary,
  UserProfile,
  WalletRead,
} from "@/lib/types";

type ProfilePrimarySectionProps = {
  user: UserProfile;
  summary: SellerMarketplaceSummary;
  billing: BillingStatus | null;
  onboardingProfile: OnboardingProfile | null;
  wallet: WalletRead | null;
  ratingLabel: string;
  planUnlocks: string;
  locale: string;
};

export function ProfilePrimarySection({
  user,
  summary,
  billing,
  onboardingProfile,
  wallet,
  ratingLabel,
  planUnlocks,
  locale,
}: ProfilePrimarySectionProps) {
  const { t } = useI18n();

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
      <ProfileAccountOverview
        user={user}
        summary={summary}
        ratingLabel={ratingLabel}
        locale={locale}
        wallet={wallet}
        t={t}
      />

      <div className="space-y-6">
        <ProfileMembershipPanel
          user={user}
          summary={summary}
          billing={billing}
          planUnlocks={planUnlocks}
          locale={locale}
        />
        <ProfileTelegramCard user={user} />
        <ProfileActionsPanel onboardingProfile={onboardingProfile} />
      </div>
    </div>
  );
}

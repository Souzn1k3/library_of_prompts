import type { TranslationKey } from "@/lib/i18n";

import {
  InstagramIcon,
  TelegramIcon,
  TikTokIcon,
  YouTubeIcon,
} from "@/components/layout/footer/footerIcons";
import type { FooterSection, SocialLink } from "@/components/layout/footer/footerTypes";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

export function getFooterSections(status: string, t: Translate): FooterSection[] {
  return [
    {
      id: "core",
      title: t("footer.product"),
      links: [
        { href: "/catalog", label: t("nav.catalog") },
        { href: "/learn", label: t("nav.learn") },
        { href: "/missions", label: t("nav.missions") },
        { href: "/pricing", label: t("nav.plans") },
      ],
    },
    {
      id: "resources",
      title: t("footer.resources"),
      links: [
        { href: "/learn", label: t("footer.guides") },
        { href: "/catalog", label: t("footer.promptTechniques") },
      ],
    },
    {
      id: "company",
      title: t("footer.company"),
      links: [
        { href: "/", label: t("footer.about") },
        { href: "/submit", label: t("footer.contribute") },
      ],
    },
    {
      id: "account",
      title: t("footer.account"),
      links:
        status === "authenticated"
          ? [
              { href: "/dashboard", label: t("nav.dashboard") },
              { href: "/profile", label: t("nav.profile") },
            ]
          : [
              { href: "/login", label: t("nav.login") },
              { href: "/signup", label: t("nav.signup") },
            ],
    },
  ];
}

export function getSocialLinks(t: Translate): SocialLink[] {
  return [
    {
      id: "telegram",
      href: "https://t.me/prompts_souz_bot",
      label: t("footer.telegramBot"),
      icon: TelegramIcon,
    },
    {
      id: "instagram",
      href: "https://instagram.com",
      label: "Instagram",
      icon: InstagramIcon,
    },
    {
      id: "tiktok",
      href: "https://www.tiktok.com",
      label: "TikTok",
      icon: TikTokIcon,
    },
    {
      id: "youtube",
      href: "https://www.youtube.com",
      label: "YouTube",
      icon: YouTubeIcon,
    },
  ];
}

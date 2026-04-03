"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { getHeaderNavigation, isHeaderNavigationItemActive } from "@/lib/navigation";

type HeaderPrimaryNavProps = {
  mobile?: boolean;
  onNavigate?: () => void;
};

export function HeaderPrimaryNav({ mobile = false, onNavigate }: HeaderPrimaryNavProps) {
  const pathname = usePathname();
  const { t } = useI18n();
  const items = getHeaderNavigation();

  return (
    <nav className={mobile ? "grid gap-1" : "flex items-center gap-1"}>
      {items.map((item) => {
        const isActive = isHeaderNavigationItemActive(pathname, item.id);
        return (
          <Link
            key={item.id}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            onClick={onNavigate}
            className={
              mobile
                ? `pv-header-mobile-link ${isActive ? "pv-header-mobile-link-active" : ""}`
                : `pv-header-link ${isActive ? "pv-header-link-active" : ""}`
            }
          >
            {t(item.labelKey)}
          </Link>
        );
      })}
    </nav>
  );
}

import type { TranslationKey } from "@/lib/i18n";

export type HeaderNavItemId = "catalog" | "learn" | "missions" | "pricing";

export type HeaderNavItem = {
  id: HeaderNavItemId;
  href: string;
  labelKey: TranslationKey;
};

export type AccountMenuItemId = "dashboard" | "profile" | "wallet" | "store";

export type AccountMenuItem = {
  id: AccountMenuItemId;
  href: string;
  labelKey: TranslationKey;
  isActive: (pathname: string) => boolean;
};

const HEADER_NAV_ITEMS: Record<HeaderNavItemId, HeaderNavItem> = {
  catalog: {
    id: "catalog",
    href: "/catalog",
    labelKey: "nav.catalog",
  },
  learn: {
    id: "learn",
    href: "/learn",
    labelKey: "nav.learn",
  },
  missions: {
    id: "missions",
    href: "/missions",
    labelKey: "nav.missions",
  },
  pricing: {
    id: "pricing",
    href: "/pricing",
    labelKey: "nav.plans",
  },
};

const HEADER_ORDER: HeaderNavItemId[] = ["catalog", "learn", "missions", "pricing"];

const ACCOUNT_MENU_ITEMS: AccountMenuItem[] = [
  {
    id: "dashboard",
    href: "/dashboard",
    labelKey: "nav.dashboard",
    isActive: (pathname) => pathname === "/dashboard",
  },
  {
    id: "profile",
    href: "/profile",
    labelKey: "nav.profile",
    isActive: (pathname) => pathname === "/profile",
  },
  {
    id: "wallet",
    href: "/wallet",
    labelKey: "nav.wallet",
    isActive: (pathname) => pathname === "/wallet",
  },
  {
    id: "store",
    href: "/store",
    labelKey: "nav.store",
    isActive: (pathname) => pathname === "/store",
  },
];

function matchesPath(pathname: string, prefixes: string[]) {
  return prefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

export function getHeaderNavigation(): HeaderNavItem[] {
  return HEADER_ORDER.map((id) => HEADER_NAV_ITEMS[id]);
}

export function isHeaderNavigationItemActive(pathname: string, itemId: HeaderNavItemId) {
  if (itemId === "catalog") {
    return matchesPath(pathname, ["/catalog", "/scenarios", "/prompt", "/category", "/contributors"]);
  }

  if (itemId === "learn") {
    return matchesPath(pathname, ["/learn"]);
  }

  if (itemId === "missions") {
    return matchesPath(pathname, ["/missions"]);
  }

  if (itemId === "pricing") {
    return matchesPath(pathname, ["/pricing", "/plans"]);
  }

  return false;
}

export function getAccountMenuItems(): AccountMenuItem[] {
  return ACCOUNT_MENU_ITEMS;
}

export function isAccountMenuItemActive(pathname: string) {
  return ACCOUNT_MENU_ITEMS.some((item) => item.isActive(pathname));
}

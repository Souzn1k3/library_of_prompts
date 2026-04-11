import type { TranslationKey } from "@/lib/i18n";

export type HeaderNavItemId = "catalog" | "dashboard" | "submit" | "pricing";

export type HeaderNavItem = {
  id: HeaderNavItemId;
  href: string;
  labelKey: TranslationKey;
};

export type AccountMenuItemId = "dashboard" | "submit" | "profile";

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
  dashboard: {
    id: "dashboard",
    href: "/dashboard",
    labelKey: "nav.dashboard",
  },
  submit: {
    id: "submit",
    href: "/submit",
    labelKey: "nav.submit",
  },
  pricing: {
    id: "pricing",
    href: "/pricing",
    labelKey: "nav.plans",
  },
};

const HEADER_ORDER: HeaderNavItemId[] = ["catalog", "dashboard", "submit", "pricing"];

const ACCOUNT_MENU_ITEMS: AccountMenuItem[] = [
  {
    id: "dashboard",
    href: "/dashboard",
    labelKey: "nav.dashboard",
    isActive: (pathname) => pathname === "/dashboard",
  },
  {
    id: "submit",
    href: "/submit",
    labelKey: "nav.submit",
    isActive: (pathname) => pathname === "/submit",
  },
  {
    id: "profile",
    href: "/profile",
    labelKey: "nav.profile",
    isActive: (pathname) => pathname === "/profile",
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
    return matchesPath(pathname, ["/catalog", "/prompt", "/category", "/contributors"]);
  }

  if (itemId === "dashboard") {
    return matchesPath(pathname, ["/dashboard"]);
  }

  if (itemId === "submit") {
    return matchesPath(pathname, ["/submit"]);
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

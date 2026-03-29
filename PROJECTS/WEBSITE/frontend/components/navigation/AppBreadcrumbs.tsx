import type { ReactNode } from "react";

import Link from "next/link";

type BreadcrumbItem = {
  label: ReactNode;
  href?: string;
};

export function AppBreadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  if (items.length === 0) {
    return null;
  }

  return (
    <nav aria-label="Breadcrumb" className="pv-breadcrumbs">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        return (
          <span key={`${String(item.href ?? item.label)}-${index}`} className="pv-breadcrumb-item">
            {item.href && !isLast ? (
              <Link href={item.href} className="pv-breadcrumb-link">
                {item.label}
              </Link>
            ) : (
              <span className={isLast ? "pv-breadcrumb-current" : "pv-breadcrumb-link"}>
                {item.label}
              </span>
            )}
            {!isLast ? <span className="pv-breadcrumb-separator">/</span> : null}
          </span>
        );
      })}
    </nav>
  );
}

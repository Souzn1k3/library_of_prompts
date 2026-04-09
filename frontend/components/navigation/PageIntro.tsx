import { isValidElement, type ReactNode } from "react";

import { T } from "@/components/i18n/T";
import { AppBreadcrumbs } from "@/components/navigation/AppBreadcrumbs";

type PageIntroProps = {
  breadcrumbs?: Array<{ label: ReactNode; href?: string }>;
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  hint?: ReactNode;
  hintLabel?: ReactNode;
  actions?: ReactNode;
  aside?: ReactNode;
  children?: ReactNode;
};

function getNodeText(node: ReactNode): string {
  if (node === null || node === undefined || typeof node === "boolean") {
    return "";
  }

  if (typeof node === "string" || typeof node === "number") {
    return String(node).trim();
  }

  if (Array.isArray(node)) {
    return node
      .map((entry) => getNodeText(entry))
      .filter(Boolean)
      .join(" ")
      .trim();
  }

  if (isValidElement(node)) {
    return getNodeText((node.props as { children?: ReactNode }).children);
  }

  return "";
}

export function PageIntro({
  breadcrumbs = [],
  eyebrow,
  title,
  description,
  hint,
  hintLabel,
  actions,
  aside,
  children,
}: PageIntroProps) {
  const lastBreadcrumbLabel = breadcrumbs[breadcrumbs.length - 1]?.label;
  const eyebrowText = getNodeText(eyebrow);
  const shouldShowEyebrow =
    eyebrowText.length > 0 &&
    eyebrowText !== getNodeText(title) &&
    eyebrowText !== getNodeText(lastBreadcrumbLabel);

  return (
    <section className="pv-page-intro">
      {breadcrumbs.length > 0 ? <AppBreadcrumbs items={breadcrumbs} /> : null}

      <div className={`pv-page-intro-grid ${aside ? "pv-page-intro-grid-has-aside" : ""}`}>
        <div className="pv-page-intro-main">
          <div className="space-y-4">
            {shouldShowEyebrow ? <p className="pv-kicker pv-page-intro-kicker">{eyebrow}</p> : null}
            <h1 className="pv-page-intro-title">{title}</h1>
            {description ? <p className="pv-page-intro-description">{description}</p> : null}
          </div>

          {children ? <div className="pv-page-intro-body">{children}</div> : null}
        </div>

        {hint || actions || aside ? (
          <div className="pv-page-intro-side">
            {hint ? (
              <div className="pv-note">
                <p className="pv-hint-badge">{hintLabel ?? <T k="common.hintBadge" />}</p>
                <div className="mt-1">{hint}</div>
              </div>
            ) : null}
            {actions ? <div className="pv-cta-group">{actions}</div> : null}
            {aside}
          </div>
        ) : null}
      </div>
    </section>
  );
}

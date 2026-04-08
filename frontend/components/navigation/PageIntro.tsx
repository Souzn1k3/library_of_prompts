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
  const hasRail = Boolean(actions || aside);
  const shouldShowEyebrow =
    eyebrowText.length > 0 &&
    eyebrowText !== getNodeText(title) &&
    eyebrowText !== getNodeText(lastBreadcrumbLabel);

  return (
    <section className="pv-hero px-6 py-7 sm:px-8 sm:py-8">
      {breadcrumbs.length > 0 ? <AppBreadcrumbs items={breadcrumbs} /> : null}

      <div className={`grid gap-6 ${hasRail ? "xl:grid-cols-[minmax(0,1fr)_minmax(280px,0.86fr)]" : ""}`}>
        <div className="pv-page-intro-main space-y-5">
          <div className="space-y-3">
            {shouldShowEyebrow ? <p className="pv-kicker">{eyebrow}</p> : null}
            <h1 className="pv-title max-w-4xl text-zinc-950">{title}</h1>
            {description ? <p className="pv-lead max-w-3xl">{description}</p> : null}
          </div>

          {hint ? (
            <div className="pv-note">
              <p className="pv-hint-badge">{hintLabel ?? <T k="common.hintBadge" />}</p>
              <div className="mt-1">{hint}</div>
            </div>
          ) : null}
          {children}
        </div>

        {hasRail ? (
          <div className="pv-page-intro-rail space-y-4">
            {actions ? <div className="pv-page-intro-actions">{actions}</div> : null}
            {aside ? <div className="pv-page-intro-aside">{aside}</div> : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}

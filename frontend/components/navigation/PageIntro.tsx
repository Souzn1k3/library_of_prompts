import { isValidElement, type ReactNode } from "react";

import { T } from "@/components/i18n/T";
import { AppBreadcrumbs } from "@/components/navigation/AppBreadcrumbs";

type PageIntroProps = {
  breadcrumbs?: Array<{ label: ReactNode; href?: string }>;
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  hint?: ReactNode;
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
    <section className="pv-hero px-6 py-7 sm:px-8 sm:py-8">
      {breadcrumbs.length > 0 ? <AppBreadcrumbs items={breadcrumbs} /> : null}

      <div className={`grid gap-6 ${aside ? "xl:grid-cols-[minmax(0,1.18fr)_minmax(280px,0.82fr)]" : ""}`}>
        <div className="space-y-5">
          <div className="space-y-3">
            {shouldShowEyebrow ? <p className="pv-kicker">{eyebrow}</p> : null}
            <h1 className="pv-title max-w-4xl text-zinc-950">{title}</h1>
            {description ? <p className="pv-lead max-w-3xl">{description}</p> : null}
          </div>

          {hint ? (
            <div className="pv-note">
              <p className="pv-hint-badge"><T k="common.hintBadge" /></p>
              <div className="mt-1">{hint}</div>
            </div>
          ) : null}
          {actions ? <div className="pv-cta-group">{actions}</div> : null}
          {children}
        </div>

        {aside ? <div>{aside}</div> : null}
      </div>
    </section>
  );
}

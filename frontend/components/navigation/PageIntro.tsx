import { isValidElement, type ReactNode } from "react";

import { T } from "@/components/i18n/T";
import { AppBreadcrumbs } from "@/components/navigation/AppBreadcrumbs";

type PageIntroProps = {
  breadcrumbs?: Array<{ label: ReactNode; href?: string }>;
  eyebrow?: ReactNode;
  title: ReactNode;
  titleAside?: ReactNode;
  titleClassName?: string;
  description?: ReactNode;
  showDescription?: boolean;
  hint?: ReactNode;
  hintLabel?: ReactNode;
  actions?: ReactNode;
  aside?: ReactNode;
  children?: ReactNode;
  className?: string;
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
  titleAside,
  titleClassName,
  description,
  showDescription = false,
  hint,
  hintLabel,
  actions,
  aside,
  children,
  className,
}: PageIntroProps) {
  const lastBreadcrumbLabel = breadcrumbs[breadcrumbs.length - 1]?.label;
  const eyebrowText = getNodeText(eyebrow);
  const shouldShowEyebrow =
    eyebrowText.length > 0 &&
    eyebrowText !== getNodeText(title) &&
    eyebrowText !== getNodeText(lastBreadcrumbLabel);

  return (
    <section className={`pv-hero px-5 py-4 sm:px-6 sm:py-5 ${className ?? ""}`}>
      {breadcrumbs.length > 0 ? <AppBreadcrumbs items={breadcrumbs} /> : null}

      <div
        className={`grid gap-4 ${aside ? "xl:grid-cols-[minmax(0,1.12fr)_minmax(320px,0.88fr)] xl:items-start" : ""}`}
      >
        <div className="space-y-3">
          <div className="space-y-2">
            {shouldShowEyebrow ? <p className="pv-kicker">{eyebrow}</p> : null}
            <div className={`gap-3 ${titleAside ? "flex flex-col sm:flex-row sm:items-start sm:justify-between" : ""}`}>
              <h1
                className={`max-w-4xl text-2xl font-semibold tracking-[-0.05em] text-zinc-950 sm:text-3xl ${titleClassName ?? ""}`}
              >
                {title}
              </h1>
              {titleAside ? <div className="shrink-0">{titleAside}</div> : null}
            </div>
            {showDescription && description ? <p className="pv-lead max-w-3xl">{description}</p> : null}
          </div>

          {hint ? (
            <div className="pv-note">
              <p className="pv-hint-badge">{hintLabel ?? <T k="common.hintBadge" />}</p>
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

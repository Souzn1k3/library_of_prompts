import { isValidElement, type ReactNode } from "react";

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

function getComparableValueSignature(value: unknown): string {
  if (value === null || value === undefined || typeof value === "boolean") {
    return "";
  }

  if (typeof value === "string" || typeof value === "number") {
    return `scalar:${String(value)}`;
  }

  if (Array.isArray(value)) {
    return `array:${value.map((entry) => getComparableValueSignature(entry)).join("|")}`;
  }

  if (isValidElement(value)) {
    return getComparableNodeSignature(value);
  }

  if (typeof value === "object") {
    return `object:${Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, entry]) => `${key}:${getComparableValueSignature(entry)}`)
      .join("|")}`;
  }

  return "";
}

function getComparableNodeSignature(node: ReactNode): string {
  if (node === null || node === undefined || typeof node === "boolean") {
    return "";
  }

  if (typeof node === "string" || typeof node === "number") {
    return `text:${String(node)}`;
  }

  if (Array.isArray(node)) {
    return `nodes:${node.map((entry) => getComparableNodeSignature(entry)).join("|")}`;
  }

  if (isValidElement(node)) {
    const props = node.props as Record<string, unknown>;
    const componentType = node.type as { displayName?: string; name?: string };
    const typeSignature =
      typeof node.type === "string"
        ? node.type
        : typeof node.type === "function"
          ? componentType.displayName ?? componentType.name ?? "component"
          : "component";

    return `element:${typeSignature}:${Object.entries(props)
      .filter(([key]) => key !== "children")
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, value]) => `${key}:${getComparableValueSignature(value)}`)
      .join("|")}:children:${getComparableValueSignature(props.children)}`;
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
  const eyebrowSignature = getComparableNodeSignature(eyebrow);
  const shouldShowEyebrow =
    eyebrowSignature.length > 0 &&
    eyebrowSignature !== getComparableNodeSignature(title) &&
    eyebrowSignature !== getComparableNodeSignature(lastBreadcrumbLabel);

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

          {hint ? <div className="pv-note">{hint}</div> : null}
          {actions ? <div className="pv-cta-group">{actions}</div> : null}
          {children}
        </div>

        {aside ? <div>{aside}</div> : null}
      </div>
    </section>
  );
}

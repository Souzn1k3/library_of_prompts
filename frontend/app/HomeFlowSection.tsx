import Link from "next/link";

import { T } from "@/components/i18n/T";

type HomeFlowSectionProps = {
  initialAuthenticated: boolean;
  heroPromptSlug: string | undefined;
};

type FlowStep = {
  id: string;
  step: string;
  titleKey: string;
  bodyKey: string;
  href: string;
  actionKey: string;
};

export function HomeFlowSection({ initialAuthenticated, heroPromptSlug }: HomeFlowSectionProps) {
  const stepTwoHref = heroPromptSlug
    ? `/prompt/${encodeURIComponent(heroPromptSlug)}`
    : "/catalog";

  const steps: FlowStep[] = [
    {
      id: "step-1",
      step: "01",
      titleKey: "home.flowStepOneTitle",
      bodyKey: "home.flowStepOneBody",
      href: "/catalog",
      actionKey: "home.flowStepOneAction",
    },
    {
      id: "step-2",
      step: "02",
      titleKey: "home.flowStepTwoTitle",
      bodyKey: "home.flowStepTwoBody",
      href: stepTwoHref,
      actionKey: "home.flowStepTwoAction",
    },
    {
      id: "step-3",
      step: "03",
      titleKey: initialAuthenticated ? "home.flowStepThreeTitleAuth" : "home.flowStepThreeTitleGuest",
      bodyKey: initialAuthenticated ? "home.flowStepThreeBodyAuth" : "home.flowStepThreeBodyGuest",
      href: initialAuthenticated ? "/dashboard" : "/signup",
      actionKey: initialAuthenticated ? "home.flowStepThreeActionAuth" : "home.flowStepThreeActionGuest",
    },
  ];

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker pv-home-section-kicker">
            <T k="home.flowKicker" />
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            <T k="home.flowTitle" />
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            <T k="home.flowSubtitle" />
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {steps.map((step) => (
          <article key={step.id} className="pv-flow-card">
            <p className="pv-flow-step">{step.step}</p>
            <h3 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">
              <T k={step.titleKey} />
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">
              <T k={step.bodyKey} />
            </p>
            <Link href={step.href} className="pv-inline-link mt-4 w-fit text-sm">
              <T k={step.actionKey} />
              <span aria-hidden="true">↗</span>
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}

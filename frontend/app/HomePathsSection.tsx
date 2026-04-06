import Link from "next/link";

import { T } from "@/components/i18n/T";

type HomePathsSectionProps = {
  initialAuthenticated: boolean;
};

type PathCard = {
  id: string;
  titleKey: string;
  bodyKey: string;
  href: string;
  actionKey: string;
};

export function HomePathsSection({ initialAuthenticated }: HomePathsSectionProps) {
  const cards: PathCard[] = [
    {
      id: "beginner",
      titleKey: "home.pathBeginnerTitle",
      bodyKey: "home.pathBeginnerBody",
      href: "/learn/start",
      actionKey: "home.pathBeginnerAction",
    },
    {
      id: "practitioner",
      titleKey: "home.pathPractitionerTitle",
      bodyKey: "home.pathPractitionerBody",
      href: "/catalog?sort=most_saved",
      actionKey: "home.pathPractitionerAction",
    },
    {
      id: "library",
      titleKey: initialAuthenticated ? "home.pathLibraryTitleAuth" : "home.pathLibraryTitleGuest",
      bodyKey: initialAuthenticated ? "home.pathLibraryBodyAuth" : "home.pathLibraryBodyGuest",
      href: initialAuthenticated ? "/dashboard" : "/signup",
      actionKey: initialAuthenticated ? "home.pathLibraryActionAuth" : "home.pathLibraryActionGuest",
    },
  ];

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker pv-home-section-kicker">
            <T k="home.pathKicker" />
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            <T k="home.pathTitle" />
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            <T k="home.pathSubtitle" />
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {cards.map((card) => (
          <article key={card.id} className="pv-path-card">
            <h3 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">
              <T k={card.titleKey} />
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">
              <T k={card.bodyKey} />
            </p>
            <Link href={card.href} className="pv-inline-link mt-4 w-fit text-sm">
              <T k={card.actionKey} />
              <span aria-hidden="true">↗</span>
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}

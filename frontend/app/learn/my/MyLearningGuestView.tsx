import Link from "next/link";

import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { APP_ROUTES } from "@/lib/constants/routes";
import { getTranslation, type Language } from "@/lib/i18n";

type MyLearningGuestViewProps = {
  language: Language;
};

export function MyLearningGuestView({ language }: MyLearningGuestViewProps) {
  return (
    <div className="pv-page-sm">
      <PageIntro
        breadcrumbs={[
          { label: getTranslation(language, "brand.name"), href: APP_ROUTES.home },
          { label: getTranslation(language, "nav.learn"), href: APP_ROUTES.learn },
          { label: getTranslation(language, "learn.myModules") },
        ]}
        eyebrow={<T k="learn.myModules" />}
        title={<T k="learn.signInTitle" />}
        description={<T k="learn.signInDescription" />}
        actions={
          <>
            <Link href={APP_ROUTES.login} className="pv-button-primary">
              <T k="nav.login" />
            </Link>
            <Link href={APP_ROUTES.learn} className="pv-button-secondary">
              <T k="learn.viewCatalog" />
            </Link>
          </>
        }
      />
    </div>
  );
}

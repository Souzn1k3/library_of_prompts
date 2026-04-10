import type { Metadata } from "next";
import { Suspense } from "react";
import Script from "next/script";
import localFont from "next/font/local";

import { AnalyticsPageTracker } from "@/components/analytics/AnalyticsPageTracker";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { LanguageProvider } from "@/components/i18n/LanguageProvider";
import { T } from "@/components/i18n/T";
import { OnboardingBanner } from "@/components/OnboardingBanner";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { RouteTransitionLoader } from "@/components/navigation/RouteTransitionLoader";
import { OrganizationJsonLd, WebSiteJsonLd } from "@/components/seo/JsonLd";
import { DEFAULT_LANGUAGE, getTranslation, languageToLocale } from "@/lib/i18n";
import { getSiteUrl } from "@/lib/site";

import "./globals.css";
import "./styles/base.css";
import "./styles/surfaces.css";
import "./styles/navigation.css";
import "./styles/components.css";
import "./styles/economy.css";
import "./styles/utility.css";
import "./styles/theme-dark.css";
import "./styles/redesign.css";

const ibmPlexMono = localFont({
  src: [
    {
      path: "./fonts/ibm-plex-mono/IBMPlexMono-Regular.ttf",
      weight: "400",
      style: "normal",
    },
    {
      path: "./fonts/ibm-plex-mono/IBMPlexMono-Medium.ttf",
      weight: "500",
      style: "normal",
    },
    {
      path: "./fonts/ibm-plex-mono/IBMPlexMono-SemiBold.ttf",
      weight: "600",
      style: "normal",
    },
  ],
  variable: "--font-mono",
  display: "swap",
  preload: false,
});

const siteUrl = getSiteUrl();
const themeInitScript = `
(() => {
  try {
    const key = "pv-theme";
    const stored = window.localStorage.getItem(key);
    const theme = stored === "dark" || stored === "light" ? stored : "light";
    document.documentElement.setAttribute("data-theme", theme);
  } catch {
    document.documentElement.setAttribute("data-theme", "light");
  }
})();
`;

export async function generateMetadata(): Promise<Metadata> {
  const language = DEFAULT_LANGUAGE;
  const siteTitle = getTranslation(language, "meta.siteTitle");
  const siteDescription = getTranslation(language, "meta.siteDescription");

  return {
    metadataBase: new URL(siteUrl),
    title: {
      default: siteTitle,
      template: `%s · ${siteTitle}`,
    },
    description: siteDescription,
    applicationName: siteTitle,
    keywords: [
      "prompt engineering",
      "AI prompts",
      "ChatGPT prompts",
      "few-shot prompting",
      "chain of thought",
      "zero-shot",
      "prompt library",
    ],
    authors: [{ name: siteTitle }],
    openGraph: {
      type: "website",
      locale: languageToLocale(language),
      url: siteUrl,
      siteName: siteTitle,
      title: siteTitle,
      description: siteDescription,
    },
    twitter: {
      card: "summary_large_image",
      title: siteTitle,
      description: siteDescription,
    },
    robots: {
      index: true,
      follow: true,
      googleBot: {
        index: true,
        follow: true,
      },
    },
  };
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const language = DEFAULT_LANGUAGE;

  return (
    <html lang={language} data-theme="light" suppressHydrationWarning>
      <body className={`${ibmPlexMono.variable} min-h-screen antialiased`}>
        <Script id="theme-init" strategy="beforeInteractive">
          {themeInitScript}
        </Script>
        <div className="relative isolate flex min-h-screen flex-col">
          <LanguageProvider initialLanguage={language}>
            <AuthProvider initialHasAuthCookie={false}>
              <Suspense fallback={null}>
                <AnalyticsPageTracker />
              </Suspense>
              <Suspense fallback={null}>
                <RouteTransitionLoader />
              </Suspense>
              <a href="#main-content" className="skip-link">
                <T k="a11y.skipToContent" />
              </a>
              <OrganizationJsonLd />
              <WebSiteJsonLd />
              <OnboardingBanner />
              <Header />
              <main
                id="main-content"
                className="pv-main-shell mx-auto w-full max-w-[1360px] flex-1 px-4 pb-16 pt-6 sm:px-6 sm:pb-20 sm:pt-8 lg:px-8"
                tabIndex={-1}
              >
                {children}
              </main>
              <Footer />
            </AuthProvider>
          </LanguageProvider>
        </div>
      </body>
    </html>
  );
}

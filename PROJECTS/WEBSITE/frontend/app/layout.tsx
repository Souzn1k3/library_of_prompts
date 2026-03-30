import type { Metadata } from "next";
import localFont from "next/font/local";

import { AnalyticsPageTracker } from "@/components/analytics/AnalyticsPageTracker";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { LanguageProvider } from "@/components/i18n/LanguageProvider";
import { T } from "@/components/i18n/T";
import { OnboardingBanner } from "@/components/OnboardingBanner";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { OrganizationJsonLd, WebSiteJsonLd } from "@/components/seo/JsonLd";
import { getTranslation, languageToLocale } from "@/lib/i18n";
import { getServerAuthCookieState } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";
import { getSiteUrl } from "@/lib/site";

import "./globals.css";
import "./styles/base.css";
import "./styles/surfaces.css";
import "./styles/navigation.css";
import "./styles/components.css";
import "./styles/economy.css";
import "./styles/utility.css";

const manrope = localFont({
  src: "./fonts/manrope/Manrope[wght].ttf",
  variable: "--font-sans",
  display: "swap",
  weight: "200 800",
});

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
});

const siteUrl = getSiteUrl();

export async function generateMetadata(): Promise<Metadata> {
  const language = await getServerLanguage();
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
  const [language, authState] = await Promise.all([
    getServerLanguage(),
    getServerAuthCookieState(),
  ]);

  return (
    <html lang={language}>
      <body className={`${manrope.variable} ${ibmPlexMono.variable} min-h-screen antialiased`}>
        <div className="relative isolate flex min-h-screen flex-col">
          <LanguageProvider initialLanguage={language}>
            <AuthProvider initialHasAuthCookie={authState.hasAnyAuthCookie}>
              <AnalyticsPageTracker />
              <a href="#main-content" className="skip-link">
                <T k="a11y.skipToContent" />
              </a>
              <OrganizationJsonLd />
              <WebSiteJsonLd />
              <OnboardingBanner />
              <Header />
              <main
                id="main-content"
                className="pv-main-shell mx-auto w-full max-w-[1280px] flex-1 px-4 pb-16 pt-8 sm:px-6 sm:pb-20 lg:px-8"
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

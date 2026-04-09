import type { Metadata } from "next";
import localFont from "next/font/local";
import Script from "next/script";

import { AnalyticsPageTracker } from "@/components/analytics/AnalyticsPageTracker";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { LanguageProvider } from "@/components/i18n/LanguageProvider";
import { T } from "@/components/i18n/T";
import { OnboardingBanner } from "@/components/OnboardingBanner";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { RouteTransitionLoader } from "@/components/navigation/RouteTransitionLoader";
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
import "./styles/theme-dark.css";
import "./styles/redesign.css";

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
  preload: false,
});

const siteUrl = getSiteUrl();
const themeInitScript = `
(() => {
  try {
    const key = "pv-theme";
    const stored = window.localStorage.getItem(key);
    const system = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    const theme = stored === "dark" || stored === "light" ? stored : system;
    document.documentElement.setAttribute("data-theme", theme);
  } catch {
    document.documentElement.setAttribute("data-theme", "light");
  }
})();
`;

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
    <html lang={language} data-theme="light" suppressHydrationWarning>
      <body className={`${manrope.variable} ${ibmPlexMono.variable} pv-app-body min-h-screen antialiased`}>
        <Script id="theme-init" strategy="beforeInteractive">
          {themeInitScript}
        </Script>
        <div className="pv-app-shell relative isolate flex min-h-screen flex-col">
          <LanguageProvider initialLanguage={language}>
            <AuthProvider initialHasAuthCookie={authState.hasAnyAuthCookie}>
              <AnalyticsPageTracker />
              <RouteTransitionLoader />
              <a href="#main-content" className="skip-link">
                <T k="a11y.skipToContent" />
              </a>
              <OrganizationJsonLd />
              <WebSiteJsonLd />
              <div className="mx-auto flex w-full max-w-[1600px] flex-1 flex-col gap-5 px-4 pb-10 pt-4 sm:px-6 lg:flex-row lg:gap-6 lg:px-8">
                <Header />
                <div className="min-w-0 flex-1">
                  <OnboardingBanner />
                  <main
                    id="main-content"
                    className="pv-main-shell min-w-0 pb-20 pt-0 sm:pb-24"
                    tabIndex={-1}
                  >
                    {children}
                  </main>
                </div>
              </div>
              <Footer />
            </AuthProvider>
          </LanguageProvider>
        </div>
      </body>
    </html>
  );
}

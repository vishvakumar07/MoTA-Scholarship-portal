import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { NetworkStatusBanner } from "@/components/ui/network-status";
import { ErrorBoundary } from "@/components/ui/error-boundary";

export const metadata: Metadata = {
  title: "MoTA Scholarship & Fellowship Portal | Ministry of Tribal Affairs",
  description:
    "Official Digital Platform for Scholarship and Fellowship Schemes for Scheduled Tribe (ST) students across India. Ministry of Tribal Affairs, Government of India.",
  keywords: [
    "MoTA", "Scholarship", "Fellowship", "Scheduled Tribes", "Tribal Affairs",
    "Pre-Matric", "Post-Matric", "Top Class Education", "NFST", "NOS", "DBT",
  ],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  minimumScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#0f2042" },
    { media: "(prefers-color-scheme: dark)",  color: "#091224" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900 selection:bg-amber-100 selection:text-amber-900 overflow-x-hidden">
        <NetworkStatusBanner />
        <Header />
        <main className="flex-1">
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>
        <Footer />
      </body>
    </html>
  );
}

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "RegIntel — every regulatory change, traced to your own policy",
  description:
    "RegIntel reads RBI and SEBI circulars, extracts the obligations, and checks them against the policies you already have. Every verdict quotes both sides.",
  robots: { index: true, follow: true },
  openGraph: {
    title: "RegIntel",
    description:
      "Regulatory change, mapped to the clause in your own policy. Every verdict quotes both sides.",
    type: "website",
  },
};

export default function LandingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="landing min-h-screen">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-black"
      >
        Skip to content
      </a>
      {children}
    </div>
  );
}

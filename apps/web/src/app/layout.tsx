import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Data Analyst — Evidence-Gated Autonomous Intelligence",
  description: "Deterministic analytics engine with Polars, DuckDB, and LangGraph hard evidence gate.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground antialiased selection:bg-brand-500 selection:text-black">
        {children}
      </body>
    </html>
  );
}

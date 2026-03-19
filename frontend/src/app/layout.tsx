// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { Manrope } from "next/font/google";
import "./globals.css";

const manrope = Manrope({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Cogni - Metacognitive Study Companion",
  description: "AI-powered study companion with persistent memory using Hindsight",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={manrope.className} suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
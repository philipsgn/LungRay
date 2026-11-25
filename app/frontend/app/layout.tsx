import type { Metadata } from "next";
import "./globals.css";
import localFont from "next/font/local";

const workstationFont = localFont({ src: "./fonts/GeistVF.woff", display: "swap" });

export const metadata: Metadata = {
  title: "LungRay · Intelligent Chest Diagnostics",
  description: "Clinical Chest Radiography AI & Visual Localization Workstation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${workstationFont.className} antialiased min-h-screen`}>{children}</body>
    </html>
  );
}

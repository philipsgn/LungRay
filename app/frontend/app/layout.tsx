import type { Metadata } from "next";
import "./globals.css";
import localFont from "next/font/local";

const workstationFont = localFont({ src: "./fonts/GeistVF.woff", display: "swap" });

export const metadata: Metadata = {
  title: "LungRay · CXR Diagnostics",
  description: "Chest Radiography Diagnostics & Visual Localization",
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

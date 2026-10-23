import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LungRay PACS Viewer",
  description: "Next.js Medical PACS Viewer for LungRay Multi-Task CXR AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen">{children}</body>
    </html>
  );
}

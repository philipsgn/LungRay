/** @type {import('next').NextConfig} */
const nextConfig = {
  // Development and production must not overwrite each other's generated chunks.
  distDir: process.env.NODE_ENV === "development" ? ".next-dev" : ".next",
  images: {
    unoptimized: true,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
};

export default nextConfig;

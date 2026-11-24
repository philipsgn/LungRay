import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: "#FFFFFF",
        border: "#E2E8F0",
        primary: { DEFAULT: "#0284C7", hover: "#0369A1" },
        accent: "#0EA5E9",
        muted: "#64748B",
        danger: "#E11D48",
        success: "#059669",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        heading: ["'Be Vietnam Pro'", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;

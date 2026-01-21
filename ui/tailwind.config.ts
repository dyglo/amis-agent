import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["\"Space Grotesk\"", "sans-serif"],
        body: ["\"Space Grotesk\"", "sans-serif"],
      },
      colors: {
        ink: "#111827",
        dusk: "#334155",
        sand: "#f8f5f0",
        amber: "#f59e0b",
        mint: "#16a34a",
        ocean: "#0ea5e9",
      },
      boxShadow: {
        glow: "0 0 0 2px rgba(14,165,233,0.15), 0 10px 30px -10px rgba(15,23,42,0.35)",
      },
    },
  },
  plugins: [],
} satisfies Config;

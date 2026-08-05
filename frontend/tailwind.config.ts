import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: { ink: "#0B1020", violet: { 500: "#7458FF", 600: "#6246EA" } },
      boxShadow: { glow: "0 24px 70px -30px rgba(116, 88, 255, .65)" },
    },
  },
  plugins: [],
} satisfies Config;


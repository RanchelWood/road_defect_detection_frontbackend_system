import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f6fbf7",
          100: "#e9f6eb",
          500: "#2f855a",
          700: "#1f5f3f",
        },
      },
    },
  },
  plugins: [],
};

export default config;
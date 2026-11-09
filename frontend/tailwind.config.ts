import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        apple: {
          bg: "#f5f5f7",
          text: "#1d1d1f",
          subtle: "#6e6e73",
          blue: "#0071e3",
        },
      },
      borderRadius: { xl2: "18px" },
    },
  },
  plugins: [],
};
export default config;

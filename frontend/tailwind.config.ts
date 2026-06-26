import type { Config } from "tailwindcss";
import flowbite from "flowbite/plugin";

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{vue,ts}",
    "./node_modules/flowbite/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        summit: {
          50: "#f2f7fb",
          100: "#e3edf6",
          200: "#c2d8eb",
          300: "#8fb8d9",
          400: "#5592c2",
          500: "#3274a8",
          600: "#235c8c",
          700: "#1e4b72",
          800: "#1d405f",
          900: "#1d3650",
          950: "#132335",
        },
        slate: {
          50: "#f8fafc",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "ridge-line":
          "linear-gradient(180deg, rgba(50,116,168,0) 0%, rgba(50,116,168,0.08) 100%)",
      },
    },
  },
  plugins: [flowbite],
};

export default config;

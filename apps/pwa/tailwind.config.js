/**
 * flavorwords design tokens (owner references, 2026-09-12):
 *  - palette from the "여덟 개의 우주" cover (muted retro blocks on grainy off-white) plus the green / terracotta of the lamp painting;
 *  - display type in the spirit of the Sesoni poster (tight, condensed grotesk, upper case for en) — "Stack Sans" (open) with condensed fallbacks;
 *  - Chinese in Xiaomi MiSans (open); the fonts are self-hosted from public/fonts (see public/fonts/README.md).
 */
import { fileURLToPath } from "node:url";
const here = (p) => fileURLToPath(new URL(p, import.meta.url));

export default {
  // absolute globs: the root scripts run with the repo as cwd
  content: [here("./index.html"), here("./src/**/*.{vue,ts}")],
  theme: {
    extend: {
      colors: {
        paper: "#FFFFFF",
        ink: "#1E1C1A",
        muted: "#6B6660",
        mint: "#86CBB4",
        violet: "#7268C9",
        mustard: "#F2C24E",
        sky: "#5FAEE8",
        pink: "#F5B0C6",
        salmon: "#EE8F70",
        brown: "#9B7B5D",
        slate: "#7F90B8",
        rose: "#DA8A80",
        maroon: "#8C4A4C",
        forest: "#2F7A4C",
        leaf: "#6FA85A",
        terracotta: "#B97C4E",
        cream: "#F3EEE2",
      },
      fontFamily: {
        display: ['"Stack Sans"', '"MiSans"', '"Helvetica Neue"', '"Arial Narrow"', "system-ui", "sans-serif"],
        sans: ['"MiSans"', '"Stack Sans"', "-apple-system", '"PingFang SC"', '"Noto Sans SC"', "system-ui", "sans-serif"],
      },
      borderRadius: { card: "22px" },
      boxShadow: { card: "0 10px 30px rgba(30, 28, 26, 0.10)", stack: "0 6px 16px rgba(30, 28, 26, 0.12)" },
      transitionTimingFunction: { fold: "cubic-bezier(0.22, 1, 0.36, 1)" },
    },
  },
  plugins: [],
};

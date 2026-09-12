/**
 * flavorwords design tokens (owner references, 2026-09-12):
 *  - palette aligned with the owner's Big Sur Coffee bag cards (2026-09-12): off-white ground, black type, one flat colour block
 *    each — navy (深烘), lavender / lime (东非拼配), mustard, pink, terracotta, peach, olive (水洗 马森秋); the retro-cover tokens stay for the stack;
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
        navy: "#1F3B5C",
        lavender: "#A995E3",
        lime: "#C9DB6E",
        olive: "#6F8B5A",
        peach: "#F2C7B5",
        blossom: "#E97BAF",
        clay: "#E4724B",
        ochre: "#CBBB4C",
        sun: "#FFD54A",
        mint2: "#7BE0C8",
      },
      fontFamily: {
        display: ['"Stack Sans"', '"MiSans"', '"Helvetica Neue"', '"Arial Narrow"', "system-ui", "sans-serif"],
        words: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"MiSans"', '"Stack Sans"', "-apple-system", '"PingFang SC"', '"Noto Sans SC"', "system-ui", "sans-serif"],
      },
      borderRadius: { card: "22px" },
      boxShadow: { card: "0 10px 30px rgba(30, 28, 26, 0.10)", stack: "0 6px 16px rgba(30, 28, 26, 0.12)" },
      transitionTimingFunction: { fold: "cubic-bezier(0.22, 1, 0.36, 1)" },
    },
  },
  plugins: [],
};

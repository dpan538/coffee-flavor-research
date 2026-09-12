import { fileURLToPath } from "node:url";
// Tailwind must be pointed at this app's config; the root scripts run with the repo as cwd.
export default {
  plugins: {
    tailwindcss: {
      config: fileURLToPath(new URL("./tailwind.config.js", import.meta.url)),
    },
    autoprefixer: {},
  },
};

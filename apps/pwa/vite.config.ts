// Isolated Vue 3 + Tailwind v3 PWA entry (owner R3-D14). The React app under app/ is untouched and not built here.
import { fileURLToPath, URL } from "node:url";
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

const here = (p: string) => fileURLToPath(new URL(p, import.meta.url));

export default defineConfig({
  root: here("."),
  publicDir: here("public"),
  plugins: [
    vue(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icons/icon.svg", "robots.txt", "sitemap.xml", "llms.txt", "humans.txt"],
      manifest: {
        name: "flavorwords — Put this cup into words",
        short_name: "flavorwords",
        description: "Every taste has its own vocabulary. A few questions turn what you taste into a flavor card. Works offline.",
        lang: "zh-CN",
        start_url: "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#ffffff",
        categories: ["food", "lifestyle"],
        icons: [{ src: "icons/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any maskable" }],
      },
      workbox: { globPatterns: ["**/*.{js,css,html,json,svg,woff2}"] },
    }),
  ],
  resolve: {
    alias: {
      "@": here("src"),
      "flavor-data": here("../../packages/flavor-data/src"),
    },
  },
  build: { outDir: here("dist"), emptyOutDir: true },
});

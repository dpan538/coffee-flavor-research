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
      includeAssets: [],
      manifest: {
        name: "flavorwords — coffee flavor diagnosis",
        short_name: "flavorwords",
        description: "Sensory attribution and flavor diagnosis, offline.",
        start_url: "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#ffffff",
        icons: [],
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

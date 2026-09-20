// Isolated Vue 3 + Tailwind v3 PWA entry (owner R3-D14). The React app under app/ is untouched and not built here.
import { execSync } from "node:child_process";
import { fileURLToPath, URL } from "node:url";
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

const here = (p: string) => fileURLToPath(new URL(p, import.meta.url));

// the build identifier shown at the end of About and set on <html data-build>: commit + day (Vercel exposes the commit
// as VERCEL_GIT_COMMIT_SHA; locally git answers); FLAVORWORDS_BUILD_ID overrides it, which the update test uses
function buildId(): string {
  if (process.env.FLAVORWORDS_BUILD_ID) return process.env.FLAVORWORDS_BUILD_ID;
  let sha = (process.env.VERCEL_GIT_COMMIT_SHA ?? "").slice(0, 7);
  if (!sha) {
    try {
      sha = execSync("git rev-parse --short HEAD", { encoding: "utf8" }).trim();
    } catch {
      sha = "dev";
    }
  }
  return `${sha} · ${new Date().toISOString().slice(0, 10)}`;
}

const BUILD_ID = buildId();

export default defineConfig({
  root: here("."),
  publicDir: here("public"),
  plugins: [
    vue(),
    {
      // version.json names the build the server is offering; the app reads it from the network (never from the
      // service worker's cache) to notice that it is running an older one — see src/update.ts
      name: "flavorwords-version-file",
      generateBundle() {
        this.emitFile({
          type: "asset",
          fileName: "version.json",
          source: JSON.stringify({ build: BUILD_ID }),
        });
      },
    },
    VitePWA({
      // "prompt": a new build waits until the app applies it (src/update.ts), instead of taking over mid-session
      registerType: "prompt",
      injectRegister: null,
      includeAssets: [
        "icons/icon.svg",
        "icons/icon-192.png",
        "icons/icon-512.png",
        "icons/apple-touch-icon.png",
        "robots.txt",
        "sitemap.xml",
        "llms.txt",
        "humans.txt",
      ],
      manifest: {
        name: "flavorwords — Put this cup into words",
        short_name: "flavorwords",
        description:
          "Six guided questions, a choice of flavor words, and a personal flavor card. Works offline, in Chinese and English.",
        lang: "zh-CN",
        start_url: "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#ffffff",
        categories: ["food", "lifestyle"],
        icons: [
          {
            src: "icons/icon.svg",
            sizes: "any",
            type: "image/svg+xml",
            purpose: "any",
          },
          {
            src: "icons/icon-192.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "icons/icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "icons/icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,json,svg,png,woff2}"],
        globIgnores: ["version.json"],
        cleanupOutdatedCaches: true,
        clientsClaim: true,
      },
    }),
  ],
  resolve: {
    alias: {
      "@": here("src"),
      "flavor-data": here("../../packages/flavor-data/src"),
    },
  },
  define: { __BUILD_ID__: JSON.stringify(BUILD_ID) },
  build: { outDir: here("dist"), emptyOutDir: true },
});

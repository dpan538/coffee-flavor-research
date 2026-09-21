// The share image (og:image, twitter:image): public/og.png, 1200 × 630. The wordmark is taken from public/icons/icon.svg,
// so it is the same drawing; under it the two taglines and what the site is; beside it the five simple shapes of the
// brand motif (half, triangle, circle, quarter, diamond — the only shapes the motif uses).
// Run: node apps/pwa/scripts/build-og-image.mjs  (uses the Playwright Chromium already installed for the smoke tests)
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "playwright";

const pub = join(dirname(fileURLToPath(import.meta.url)), "..", "public");
const icon = readFileSync(join(pub, "icons", "icon.svg"), "utf8");
const paths = [...icon.matchAll(/<path d="([^"]+)" fill="([^"]+)"\/>/g)].map(
  (m) => `<path d="${m[1]}" fill="${m[2]}"/>`,
);
const font = (file) => pathToFileURL(join(pub, "fonts", file)).href;
const shapes = [
  // half, triangle, circle, quarter, diamond — each in a 120 box
  `<path d="M0 120a60 60 0 0 1 120 0z" fill="#7268C9"/>`,
  `<path d="M60 8 116 112H4z" fill="#E4724B"/>`,
  `<circle cx="60" cy="60" r="56" fill="#2EC27E"/>`,
  `<path d="M4 116V4a112 112 0 0 1 112 112z" fill="#FFB300"/>`,
  `<path d="M60 4 116 60 60 116 4 60z" fill="#1F3B5C"/>`,
];
const html = `<!doctype html><meta charset="utf-8"><style>
@font-face { font-family: "Stack"; src: url("${font("StackSansText-Variable.woff2")}") format("woff2"); font-weight: 200 700; }
@font-face { font-family: "MiSans"; src: url("${font("MiSans-Medium.woff2")}") format("woff2"); font-weight: 500; }
html, body { margin: 0; width: 1200px; height: 630px; background: #fff; color: #1e1c1a; }
body { font-family: "Stack", "MiSans", "PingFang SC", system-ui, sans-serif; position: relative; overflow: hidden; }
.mark { position: absolute; left: 88px; top: 70px; }
.en { position: absolute; left: 96px; top: 380px; font-size: 44px; font-weight: 600; letter-spacing: -0.01em; }
.zh { position: absolute; left: 96px; top: 450px; font-size: 34px; font-weight: 500; font-family: "MiSans", "PingFang SC", sans-serif; color: #3a3632; }
.what { position: absolute; left: 96px; top: 530px; font-size: 24px; color: #6b6660; letter-spacing: 0.01em; }
.shapes { position: absolute; right: 84px; top: 96px; display: grid; grid-template-columns: repeat(2, 120px); gap: 28px; }
.shapes svg:last-child { grid-column: 1 / span 2; justify-self: center; }
</style>
<svg class="mark" width="560" height="264" viewBox="78 170 360 170">${paths.join("")}</svg>
<div class="en">Put this cup of coffee into words.</div>
<div class="zh">风味，自有表达。</div>
<div class="what">A free coffee-tasting app · 免费的咖啡品鉴应用 · flavorwords.com</div>
<div class="shapes">${shapes.map((s) => `<svg width="120" height="120" viewBox="0 0 120 120">${s}</svg>`).join("")}</div>`;

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1200, height: 630 },
  deviceScaleFactor: 1,
});
await page.setContent(html, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: join(pub, "og.png"), type: "png" });
await browser.close();
console.log("wrote", join(pub, "og.png"));

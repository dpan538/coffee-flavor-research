// PNG icons from public/icons/icon.svg (build-icons.py): 192 / 512 for the manifest, 180 for apple-touch-icon.
// Run: node apps/pwa/scripts/rasterize-icons.mjs  (uses the Playwright Chromium already installed for the smoke tests)
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const icons = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "public",
  "icons",
);
const svg = readFileSync(join(icons, "icon.svg"), "utf8");
const data = `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`;
const browser = await chromium.launch();
for (const [name, size] of [
  ["icon-192.png", 192],
  ["icon-512.png", 512],
  ["apple-touch-icon.png", 180],
]) {
  const page = await browser.newPage({
    viewport: { width: size, height: size },
    deviceScaleFactor: 1,
  });
  await page.setContent(
    `<body style="margin:0;background:#fff"><img src="${data}" width="${size}" height="${size}" style="display:block"></body>`,
  );
  await page.screenshot({
    path: join(icons, name),
    clip: { x: 0, y: 0, width: size, height: size },
  });
  await page.close();
  console.log(`wrote icons/${name} ${size}×${size}`);
}
await browser.close();

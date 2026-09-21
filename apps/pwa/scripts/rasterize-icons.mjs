// PNG icons from public/icons/icon.svg (build-icons.py): 192 / 512 for the manifest, 180 for apple-touch-icon, and
// public/favicon.ico (16 / 32 / 48, PNG entries) for the readers that ask for /favicon.ico whatever the page declares:
// Bing, Baidu, Safari's history and favourites, link previews. The small sizes crop the square to the wordmark so that
// it fills the icon; the drawing is the same.
// Run: node apps/pwa/scripts/rasterize-icons.mjs  (uses the Playwright Chromium already installed for the smoke tests)
import { readFileSync, writeFileSync } from "node:fs";
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

// favicon.ico: an ICONDIR, one ICONDIRENTRY per size, then the PNG files themselves (PNG entries are valid in .ico)
const tight = svg
  .replace('viewBox="0 0 512 512"', 'viewBox="69 66 380 380"')
  .replace(
    /<rect[^>]*\/>/,
    '<rect x="69" y="66" width="380" height="380" fill="#FFFFFF"/>',
  );
const tightData = `data:image/svg+xml;base64,${Buffer.from(tight).toString("base64")}`;
const entries = [];
for (const size of [16, 32, 48]) {
  const page = await browser.newPage({
    viewport: { width: size, height: size },
    deviceScaleFactor: 1,
  });
  await page.setContent(
    `<body style="margin:0;background:#fff"><img src="${tightData}" width="${size}" height="${size}" style="display:block"></body>`,
  );
  entries.push({
    size,
    png: await page.screenshot({
      type: "png",
      clip: { x: 0, y: 0, width: size, height: size },
    }),
  });
  await page.close();
}
const header = Buffer.alloc(6 + 16 * entries.length);
header.writeUInt16LE(0, 0);
header.writeUInt16LE(1, 2);
header.writeUInt16LE(entries.length, 4);
let offset = header.length;
entries.forEach(({ size, png }, i) => {
  const at = 6 + 16 * i;
  header.writeUInt8(size, at);
  header.writeUInt8(size, at + 1);
  header.writeUInt16LE(1, at + 4);
  header.writeUInt16LE(32, at + 6);
  header.writeUInt32LE(png.length, at + 8);
  header.writeUInt32LE(offset, at + 12);
  offset += png.length;
});
writeFileSync(
  join(icons, "..", "favicon.ico"),
  Buffer.concat([header, ...entries.map((e) => e.png)]),
);
console.log("wrote favicon.ico 16 / 32 / 48");
await browser.close();

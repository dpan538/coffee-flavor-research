import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDirectory, "..");
const outputDirectory = path.join(repositoryRoot, "docs/portfolio/assets");
const manifestPath = path.join(
  repositoryRoot,
  "docs/portfolio/SCREENSHOT_MANIFEST.md",
);
const baseURL =
  process.env.COFFEE_SCREENSHOT_BASE_URL ?? "http://127.0.0.1:4321";
const commitSha = execFileSync("git", ["rev-parse", "HEAD"], {
  cwd: repositoryRoot,
  encoding: "utf8",
}).trim();
const captureDate = new Date().toISOString().slice(0, 10);

const captures = [
  {
    filename: "desktop-home.png",
    route: "/",
    viewport: { width: 1440, height: 1100 },
    fullPage: true,
  },
  {
    filename: "mobile-home.png",
    route: "/",
    viewport: { width: 390, height: 900 },
    fullPage: true,
  },
  {
    filename: "desktop-atlas-interaction.png",
    route: "/atlas?view=index&q=cacao&compare=jasmine,dark-chocolate",
    viewport: { width: 1440, height: 1100 },
    fullPage: false,
    ready: { role: "heading", name: /Descriptor comparison/ },
  },
  {
    filename: "desktop-project-status.png",
    route: "/methodology#project-status",
    viewport: { width: 1440, height: 1100 },
    fullPage: false,
    locator: "#project-status",
  },
];

await mkdir(outputDirectory, { recursive: true });
const browser = await chromium.launch(
  process.env.CI
    ? {}
    : { channel: process.env.COFFEE_BROWSER_CHANNEL ?? "chrome" },
);
const rows = [];

try {
  for (const capture of captures) {
    const context = await browser.newContext({
      viewport: capture.viewport,
      reducedMotion: "reduce",
      colorScheme: "light",
    });
    const page = await context.newPage();
    const errors = [];
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("pageerror", (error) => errors.push(error.message));

    await page.goto(new URL(capture.route, baseURL).toString(), {
      waitUntil: "networkidle",
    });
    await page.evaluate(() => document.fonts.ready);
    if (capture.ready) {
      await page
        .getByRole(capture.ready.role, { name: capture.ready.name })
        .waitFor();
    }
    if (capture.locator) {
      await page.locator(capture.locator).scrollIntoViewIfNeeded();
    }
    if (errors.length) {
      throw new Error(
        `${capture.route} emitted console errors: ${errors.join(" | ")}`,
      );
    }

    const outputPath = path.join(outputDirectory, capture.filename);
    await page.screenshot({
      path: outputPath,
      fullPage: capture.fullPage,
      animations: "disabled",
    });
    const digest = createHash("sha256")
      .update(await readFile(outputPath))
      .digest("hex");
    rows.push({
      ...capture,
      browser: `Chromium ${browser.version()}`,
      digest,
    });
    await context.close();
  }
} finally {
  await browser.close();
}

const manifest = `# Screenshot manifest

These screenshots were captured from the production frontend preview with
reduced motion enabled. They show the real current interface; no model output or
restricted source content is present.

| File | Route | Viewport | Capture date | Browser | Commit SHA | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
${rows
  .map(
    (row) =>
      `| \`${row.filename}\` | \`${row.route}\` | \`${row.viewport.width}x${row.viewport.height}\` | ${captureDate} | ${row.browser} | \`${commitSha}\` | \`${row.digest}\` |`,
  )
  .join("\n")}

## Reproduce

\`\`\`bash
npm run build
npm run preview -- --host 127.0.0.1 --port 4321
# In another shell:
npm run portfolio:screenshots
npm run public:screenshots:check
\`\`\`

The file hashes will change if browser rendering, fonts, viewport, application
code, or browser version changes. Regenerated captures must be reviewed and
committed with their new manifest.
`;

await writeFile(manifestPath, manifest, "utf8");
console.log(`SCREENSHOT_CAPTURE_COUNT=${rows.length}`);
console.log(`SCREENSHOT_SOURCE_SHA=${commitSha}`);

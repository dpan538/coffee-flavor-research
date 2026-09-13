// Portfolio screenshots of the live product (flavorwords PWA), captured from the built preview with reduced motion.
// Run: npm run pwa:build && npx vite preview --config apps/pwa/vite.config.ts --port 4173 --strictPort
//      node scripts/capture-portfolio-screenshots.mjs && npm run public:screenshots:check
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
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
  process.env.COFFEE_SCREENSHOT_BASE_URL ?? "http://127.0.0.1:4173";
const commitSha = execFileSync("git", ["rev-parse", "HEAD"], {
  cwd: repositoryRoot,
  encoding: "utf8",
}).trim();
const captureDate = new Date().toISOString().slice(0, 10);
const phoneUA =
  "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const clickText = async (page, text) => {
  const handle = await page.evaluateHandle((t) => {
    const norm = (s) => s.replace(/\s+/g, " ").trim();
    return [...document.querySelectorAll("button")].find(
      (b) =>
        !b.disabled &&
        (norm(b.textContent) === t || norm(b.textContent).startsWith(t)),
    );
  }, text);
  const el = handle.asElement();
  if (!el) throw new Error(`button not found: ${text}`);
  await el.click();
  await sleep(700);
};
const clickCta = async (page) => {
  await page.click("button.cta:not([disabled])");
  await sleep(800);
};
// the flavor-card walk is recipe 6 of docs/product/Q6_TRIGGER_TEST_SET.md (opens the second look, then confirms)
const cardWalk = async (page) => {
  await page.click('[data-action="start"]');
  await sleep(900);
  for (const chip of ["摩卡壶", "中深烘", "铁皮卡", "水洗", "巴西"]) {
    await clickText(page, chip);
    await clickCta(page);
  }
  for (const answer of [
    "乳酸 / 发酵果酸",
    "热带水果",
    "浓郁的焦糖",
    "顺滑，像牛奶",
    "苦得明显",
    "能分清楚多种味道",
  ]) {
    await clickText(page, answer);
  }
  await page.waitForSelector('[data-words="main"]');
  for (const word of ["朗姆酒", "黑巧克力", "水蜜桃", "烤榛果", "葡萄柚"])
    await clickText(page, word);
  await clickCta(page);
  await page.waitForSelector('[data-component="EscalationModal"]');
  for (const word of ["朗姆酒", "黑巧克力"]) await clickText(page, word);
  await page.click('[data-component="EscalationModal"] button.cta');
  await page.waitForSelector('[data-component="FinalAttributionCard"]');
  await sleep(900);
};
const aboutPage = (n) => async (page) => {
  await page.click('[data-action="about"]');
  await sleep(900);
  await page.evaluate((p) => {
    const aside = document.querySelector("aside");
    const track = document.querySelector(`section[data-page="${p}"]`);
    aside.scrollTop =
      track.offsetTop +
      Math.max(0, track.offsetHeight - aside.clientHeight) * 0.95;
  }, n);
  await sleep(1200);
};

const captures = [
  {
    filename: "pwa-mobile-home.png",
    route: "/",
    viewport: { width: 390, height: 844 },
    mobile: true,
  },
  {
    filename: "pwa-mobile-card.png",
    route: "/ (flow → flavor card)",
    viewport: { width: 390, height: 844 },
    mobile: true,
    walk: cardWalk,
  },
  {
    filename: "pwa-desktop-home.png",
    route: "/",
    viewport: { width: 1440, height: 900 },
  },
  {
    filename: "pwa-desktop-context.png",
    route: "/ (start → context card)",
    viewport: { width: 1440, height: 900 },
    walk: async (page) => {
      await page.click('[data-action="start"]');
      await sleep(1200);
    },
  },
  {
    filename: "pwa-desktop-about-sources.png",
    route: "/ (about → sources poster)",
    viewport: { width: 1440, height: 900 },
    walk: aboutPage(3),
  },
  {
    filename: "pwa-desktop-about-profiles.png",
    route: "/ (about → profile network)",
    viewport: { width: 1440, height: 900 },
    walk: aboutPage(4),
  },
];

await mkdir(outputDirectory, { recursive: true });
const browser = await chromium.launch();
const version = browser.version();
const rows = [];
for (const capture of captures) {
  const context = await browser.newContext({
    viewport: capture.viewport,
    deviceScaleFactor: 1,
    reducedMotion: "reduce",
    userAgent: capture.mobile ? phoneUA : undefined,
  });
  const page = await context.newPage();
  await page.goto(`${baseURL}/`, { waitUntil: "networkidle" });
  await sleep(600);
  if (capture.walk) await capture.walk(page);
  const target = path.join(outputDirectory, capture.filename);
  await page.screenshot({ path: target });
  const { readFile } = await import("node:fs/promises");
  const hash = createHash("sha256")
    .update(await readFile(target))
    .digest("hex");
  rows.push({ ...capture, hash });
  console.log(
    `captured ${capture.filename} (${capture.viewport.width}x${capture.viewport.height})`,
  );
  await context.close();
}
await browser.close();

const table = [
  "| File | Route | Viewport | Capture date | Browser | Commit SHA | SHA-256 |",
  "| --- | --- | --- | --- | --- | --- | --- |",
  ...rows.map(
    (r) =>
      `| \`${r.filename}\` | \`${r.route}\` | \`${r.viewport.width}x${r.viewport.height}\` | ${captureDate} | Chromium ${version} | \`${commitSha}\` | \`${r.hash}\` |`,
  ),
].join("\n");
const manifest = `# Screenshot manifest

These screenshots were captured from the built flavorwords PWA (\`apps/pwa/dist\`
served by \`vite preview\`) with reduced motion enabled. They show the real
current interface; no model output or restricted source content is present.
Routes in parentheses are on-screen states of the single-page app, reached by
the listed action.

<!-- prettier-ignore -->
${table}

## Reproduce

\`\`\`bash
npm run pwa:build
npx vite preview --config apps/pwa/vite.config.ts --host 127.0.0.1 --port 4173 --strictPort
# In another shell:
npm run portfolio:screenshots
npm run public:screenshots:check
\`\`\`

The file hashes will change if browser rendering, fonts, viewport, application
code, or browser version changes. Regenerated captures must be reviewed and
committed with their new manifest.
`;
await writeFile(manifestPath, manifest);
console.log(
  `manifest written: ${rows.length} rows, commit ${commitSha.slice(0, 10)}`,
);

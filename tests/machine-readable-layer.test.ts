/**
 * The machine-readable layer (owner, 2026-09-21, R3-D51/D52): what a search crawler, a link preview or an assistant's
 * page fetcher learns about flavorwords without running the app — index.html, the one-language pages /zh and /en,
 * sitemap.xml, robots.txt, llms.txt. These files are written by hand or by apps/pwa/scripts/build-static-pages.mjs, so
 * the things that silently break are checked here: the three pages must name each other the same way (a search engine
 * drops an hreflang cluster that is not reciprocal), every page says which language it is in, the structured data has
 * to parse, the sitemap lists exactly the pages that exist, and the figures are the ones the data bundle carries.
 */
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { aboutStats } from "../packages/flavor-data/src/product-vector-v1/about";
import { productVectorBundle } from "../packages/flavor-data/src/product-vector-v1";

const SITE = "https://flavorwords.com";
const pwa = join(__dirname, "..", "apps", "pwa");
const read = (...parts: string[]) => readFileSync(join(pwa, ...parts), "utf8");
const PAGES = {
  "/": { html: read("index.html"), lang: "zh-CN" },
  "/zh": { html: read("public", "zh.html"), lang: "zh-CN" },
  "/en": { html: read("public", "en.html"), lang: "en" },
};
const attribute = (tag: string, name: string) =>
  new RegExp(`${name}="([^"]*)"`).exec(tag)?.[1] ?? "";
const tags = (html: string, name: string) =>
  html.match(new RegExp(`<${name}\\b[^>]*>`, "g")) ?? [];

describe("machine-readable layer", () => {
  it("names the language pages the same way on all three pages, each page canonical to itself", () => {
    for (const [path, page] of Object.entries(PAGES)) {
      const links = tags(page.html, "link");
      const cluster = Object.fromEntries(
        links
          .filter((l) => attribute(l, "hreflang"))
          .map((l) => [attribute(l, "hreflang"), attribute(l, "href")]),
      );
      expect(cluster, path).toEqual({
        "zh-CN": `${SITE}/zh`,
        en: `${SITE}/en`,
        "x-default": `${SITE}/`,
      });
      const canonical = links.find((l) => attribute(l, "rel") === "canonical")!;
      expect(attribute(canonical, "href"), path).toBe(`${SITE}${path}`);
      expect(attribute(tags(page.html, "html")[0]!, "lang"), path).toBe(
        page.lang,
      );
    }
  });

  it("says coffee in every title and description, and carries a share image", () => {
    for (const [path, page] of Object.entries(PAGES)) {
      const title = /<title>([\s\S]*?)<\/title>/.exec(page.html)![1]!;
      const metas = tags(page.html, "meta");
      const content = (key: string, value: string) =>
        attribute(
          metas.find((m) => attribute(m, key) === value) ?? "",
          "content",
        );
      for (const text of [title, content("name", "description")])
        expect(text, path).toMatch(/coffee|咖啡/i);
      for (const image of [
        content("property", "og:image"),
        content("name", "twitter:image"),
        content("itemprop", "image"),
      ])
        expect(image, path).toBe(`${SITE}/og.png`);
    }
    expect(existsSync(join(pwa, "public", "og.png"))).toBe(true);
  });

  it("has structured data that parses, with the app, the brand and the two language pages", () => {
    const types: string[] = [];
    for (const page of Object.values(PAGES))
      for (const block of page.html.matchAll(
        /<script type="application\/ld\+json">([\s\S]*?)<\/script>/g,
      )) {
        const data = JSON.parse(block[1]!);
        for (const node of data["@graph"] ?? [data]) types.push(node["@type"]);
      }
    expect(types.sort()).toEqual(
      [
        "AboutPage",
        "AboutPage",
        "Brand",
        "FAQPage",
        "Person",
        "WebApplication",
        "WebSite",
      ].sort(),
    );
  });

  it("lists in the sitemap exactly the pages that exist, and points robots.txt to it", () => {
    const sitemap = read("public", "sitemap.xml");
    const listed = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(
      (m) => m[1]!,
    );
    expect(listed).toEqual([
      `${SITE}/`,
      `${SITE}/zh`,
      `${SITE}/en`,
      `${SITE}/llms.txt`,
    ]);
    for (const file of ["zh.html", "en.html", "llms.txt", "404.html"])
      expect(existsSync(join(pwa, "public", file)), file).toBe(true);
    expect(read("public", "robots.txt")).toContain(
      `Sitemap: ${SITE}/sitemap.xml`,
    );
  });

  it("states the figures of the data bundle, the same ones everywhere", () => {
    const stats = Object.fromEntries(
      aboutStats("en").map((s) => [s.key, s.value]),
    );
    const figures = [stats.coffees, stats.assertions].map((n) =>
      Number(n).toLocaleString("en-US"),
    );
    const texts = {
      ...Object.fromEntries(
        Object.entries(PAGES).map(([path, page]) => [path, page.html]),
      ),
      "/llms.txt": read("public", "llms.txt"),
    };
    for (const [path, text] of Object.entries(texts)) {
      for (const figure of figures) expect(text, path).toContain(figure);
      expect(text, path).toMatch(
        new RegExp(`\\b${productVectorBundle.profiles.length}\\b`),
      );
      expect(text, path).toMatch(
        new RegExp(`\\b${productVectorBundle.dimensions.length}\\b`),
      );
      expect(text, path).not.toContain(`${SITE}/about`);
    }
  });
});

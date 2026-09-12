/**
 * App-layer interfaces (owner, 2026-09-12; interfaces first, no visual design):
 * blends and origin bias in V_pred, the context catalog and screen models, the Dexie user library, About content.
 */
import "fake-indexeddb/auto";
import { describe, expect, it } from "vitest";
import {
  DIMENSIONS,
  buildVPred,
  cosine,
  productVectorBundle,
} from "../packages/flavor-data/src/product-vector-v1";
import {
  aboutApproach,
  aboutAuthor,
  aboutCitations,
  aboutExample,
  aboutScope,
  aboutSections,
  aboutStats,
} from "../packages/flavor-data/src/product-vector-v1/about";
import {
  answer,
  createSession,
  firstDescription,
  nextStep,
  submitPicks,
} from "../packages/flavor-data/src/product-vector-v1/session";
import {
  appShell,
  contextCatalog,
  normalizeContext,
  screenModel,
} from "../packages/flavor-data/src/product-vector-v1/view";
import {
  addBean,
  beansAsVectors,
  clearBeans,
  conceptIdsFromLabel,
  deleteBean,
  listBeans,
  userDatabase,
} from "../packages/flavor-data/src/user-db";

describe("C2 blends and optional origin", () => {
  it("a blend of up to 3 varieties is the normalised mean of their rows; a 4th is dropped", () => {
    const single = buildVPred({ c2_variety: "gesha" });
    const blend = buildVPred({
      c2_variety: ["gesha", "ethiopian_landrace", "typica"],
    });
    const four = buildVPred({
      c2_variety: ["gesha", "ethiopian_landrace", "typica", "bourbon"],
    });
    expect(
      blend.contextBasis.filter((b) => b.axis === "C2_variety"),
    ).toHaveLength(3);
    expect(
      blend.contextBasis.every((b) => b.basis.includes("BLEND_MEMBER_3")),
    ).toBe(true);
    expect(
      four.contextBasis.filter((b) => b.axis === "C2_variety"),
    ).toHaveLength(3);
    expect(cosine(single.vPred, blend.vPred)).toBeGreaterThan(0.8);
    expect(cosine(single.vPred, blend.vPred)).toBeLessThan(1);
    expect(Math.abs(Math.hypot(...blend.vPred) - 1)).toBeLessThan(1e-6);
  });

  it("origin is optional: it adds a delta-0.1 bias on the region's axes and never dominates", () => {
    const plain = buildVPred({ c1_roast: "light", c2_process: "washed" });
    const eth = buildVPred({
      c1_roast: "light",
      c2_process: "washed",
      c2_origin: "ethiopia",
    });
    const floral = DIMENSIONS.indexOf("floral");
    expect(eth.vPred[floral]!).toBeGreaterThan(plain.vPred[floral]!);
    expect(cosine(plain.vPred, eth.vPred)).toBeGreaterThan(0.95);
    expect(
      eth.contextBasis.some(
        (b) =>
          b.axis === "C2_origin" && b.basis.startsWith("ORIGIN_BIAS_DELTA_0.1"),
      ),
    ).toBe(true);
    expect(
      buildVPred({ c1_roast: "light", c2_origin: "mars" }).contextBasis.some(
        (b) => b.basis === "UNKNOWN_OPTION",
      ),
    ).toBe(true);
  });
});

describe("context catalog and screen models", () => {
  it("the catalog carries every corpus-backed option, the blend toggle and the optional origin chips, in both languages", () => {
    const zh = contextCatalog("zh-CN");
    const en = contextCatalog("en");
    expect(zh.map((c) => c.key)).toEqual([
      "c0_preparation",
      "c1_roast",
      "c2_variety",
      "c2_process",
      "c2_origin",
    ]);
    const variety = zh.find((c) => c.key === "c2_variety")!;
    expect(variety.multi).toBe(true);
    if (variety.key === "c2_variety") {
      expect(variety.max).toBe(3);
      expect(variety.toggle.blend).toContain("拼配");
      expect(variety.chips.map((c) => c.value)).toContain("gesha");
    }
    const origin = zh.find((c) => c.key === "c2_origin")!;
    expect(origin.optional).toBe(true);
    // the owner's origin chart: countries grouped by continent, the chip shows only the place name
    expect(origin.chips).toHaveLength(19);
    expect(origin.chips.map((c) => c.value)).toContain("yunnan");
    expect(new Set(origin.chips.map((c) => c.group))).toEqual(
      new Set(["africa", "asia", "americas"]),
    );
    if (origin.key === "c2_origin")
      expect(origin.groups.map((g) => g.label)).toEqual([
        "非洲",
        "亚洲",
        "美洲",
      ]);
    expect(origin.chips.every((c) => !/[（(]/.test(c.label))).toBe(true);
    expect(
      en.find((c) => c.key === "c1_roast")!.chips.map((c) => c.label),
    ).toContain("Light");
    expect(
      normalizeContext({
        c2_variety: ["gesha", "gesha", "typica", "bourbon", "sl28_sl34"],
      }).c2_variety,
    ).toEqual(["gesha", "typica", "bourbon"]);
    expect(normalizeContext({ c2_variety: ["gesha"] }).c2_variety).toBe(
      "gesha",
    );
  });

  it("screenModel walks question → first description → result with plain data a component can bind", () => {
    let s = createSession(
      {
        c0_preparation: "pour_over_v60",
        c1_roast: "light",
        c2_variety: ["gesha", "ethiopian_landrace"],
        c2_process: "washed",
        c2_origin: "ethiopia",
      },
      "zh-CN",
    );
    let m = screenModel(s);
    expect(m.kind).toBe("question");
    const answers: Record<string, string> = {
      Q0: "A",
      Q1: "A",
      Q2: "A",
      Q3: "A",
      Q4: "B",
      Q5: "A",
    };
    let guard = 0;
    while (m.kind === "question" && guard < 10) {
      s = answer(s, m.slot as never, answers[m.slot]!);
      m = screenModel(s);
      guard += 1;
    }
    expect(m.kind).toBe("describe_ready");
    s = firstDescription(s);
    m = screenModel(s);
    expect(m.kind).toBe("first_description");
    if (m.kind === "first_description") {
      expect(m.main).toHaveLength(3);
      expect(m.pickCount).toBe(5);
      s = submitPicks(s, [...m.main, ...m.secondary.slice(0, 2)]);
    }
    m = screenModel(s);
    expect(["result", "escalation"]).toContain(m.kind);
    if (m.kind === "result") {
      expect(m.picked).toHaveLength(5);
      // the card's top layer: only what was entered, in reading order (copy review 3)
      expect(m.cupInfo.map((c) => c.key)).toEqual([
        "c0_preparation",
        "c1_roast",
        "c2_variety",
        "c2_process",
        "c2_origin",
      ]);
      expect(m.cupInfo.find((c) => c.key === "c2_origin")!.value).toBe(
        "埃塞俄比亚",
      );
      expect(m.cupInfo.find((c) => c.key === "c2_variety")!.value).toContain(
        " + ",
      );
      expect(m.shareText).toContain("|");
      expect(m.corrected).toBe(false);
      // owner R3-D14: every science line declares its evidence state and its source at the UI level
      expect(m.science.length).toBeGreaterThan(0);
      expect(m.science.every((l) => l.evidenceState && l.sourceTitle)).toBe(
        true,
      );
      expect(
        m.science.some((l) => l.evidenceState.startsWith("LITERATURE_CLAIM")),
      ).toBe(true);
    }
    expect(nextStep(s).kind === "final" || nextStep(s).kind === "q6").toBe(
      true,
    );
  });

  it("app shell copy exists in both languages", () => {
    expect(appShell("zh-CN").start).toBe("开始");
    expect(appShell("zh-CN").startLink).toBe("从这一口开始");
    expect(appShell("zh-CN").title).toBe("风味，自有表达。");
    expect(appShell("zh-CN").slogan).toBe(appShell("en").slogan);
    expect(appShell("zh-CN").claim).toBe("Put this cup into words.");
    expect(appShell("en").title).toBe("Put this cup into words.");
    expect(appShell("en").localeSwitch).toBe("中");
  });
});

describe("user bean library (Dexie over IndexedDB)", () => {
  it("adds, lists, projects and deletes beans locally", async () => {
    const db = userDatabase(
      "test-user-db-" + Math.random().toString(36).slice(2),
    );
    await clearBeans(db);
    const tags = productVectorBundle.presentation.concept_tags as Record<
      string,
      { "zh-CN": string; en: string }
    >;
    const ids = conceptIdsFromLabel("玉兰花 | 水蜜桃 | 佛手柑 | 青柠", tags);
    expect(ids).toContain("sensory.peach");
    expect(ids).toContain("sensory.bergamot");
    const id = await addBean(db, {
      name: "Ethiopia Washed Sewda",
      roast_level: "light",
      process: "washed",
      variety: "ethiopian_landrace",
      concept_ids: ids,
    });
    await addBean(db, {
      name: "No notes yet",
      roast_level: "",
      process: "",
      variety: "",
      concept_ids: [],
    });
    const beans = await listBeans(db);
    expect(beans).toHaveLength(2);
    const vectors = await beansAsVectors(db);
    expect(vectors).toHaveLength(1);
    expect(vectors[0]!.source).toBe("user");
    expect(vectors[0]!.vector[DIMENSIONS.indexOf("fruity")]!).toBeGreaterThan(
      0,
    );
    await deleteBean(db, id);
    expect(await listBeans(db)).toHaveLength(1);
    await expect(
      addBean(db, {
        name: "  ",
        roast_level: "",
        process: "",
        variety: "",
        concept_ids: [],
      }),
    ).rejects.toThrow();
  });

  it("user beans enter a session as candidates and get ranked with tags", async () => {
    const db = userDatabase(
      "test-user-db-session-" + Math.random().toString(36).slice(2),
    );
    const tags = productVectorBundle.presentation.concept_tags as Record<
      string,
      { "zh-CN": string; en: string }
    >;
    await addBean(db, {
      name: "Washed Masincho",
      roast_level: "light",
      process: "washed",
      variety: "ethiopian_landrace",
      concept_ids: conceptIdsFromLabel(
        "白花 | 柑橘 | 茉莉绿茶 | 杏桃 | 茉莉花",
        tags,
      ),
    });
    await addBean(db, {
      name: "Dark blend",
      roast_level: "dark",
      process: "natural",
      variety: "bourbon",
      concept_ids: conceptIdsFromLabel("黑巧克力 | 烟熏 | 焦糖", tags),
    });
    const beans = await beansAsVectors(db);
    let s = createSession(
      {
        c0_preparation: "pour_over_v60",
        c1_roast: "light",
        c2_process: "washed",
      },
      "zh-CN",
      beans,
    );
    for (const [slot, option] of Object.entries({
      Q0: "A",
      Q1: "A",
      Q2: "A",
      Q3: "A",
      Q4: "B",
    }))
      s = answer(s, slot as never, option);
    s = firstDescription(s);
    expect(s.result!.beans).toHaveLength(2);
    expect(s.result!.beans[0]!.bean.label).toBe("Washed Masincho");
  });
});

describe("about content", () => {
  it("is bilingual, reads live numbers from the bundle, folds its details, and states every citation's licence", () => {
    const zh = aboutSections("zh-CN");
    const en = aboutSections("en");
    // owner copy review 2 (2026-09-12): three folded entries — vocabulary & groups, how the questions work, data & method
    expect(zh.map((s) => s.id)).toEqual(["vocabulary", "questions", "data"]);
    expect(
      zh.every((s) => s.folded && s.summary.length > 0 && s.blocks.length > 0),
    ).toBe(true);
    expect(zh[1]!.title).toBe("动态问答模型");
    expect(zh[1]!.blocks.map((b) => b.title)).toEqual([
      "提问顺序",
      "描述的选择与确认",
    ]);
    expect(zh[2]!.blocks.map((b) => b.title)).toEqual([
      "资料范围",
      "初始参考如何形成",
      "结果的适用范围",
      "技术说明",
      "来源",
    ]);
    expect(zh[0]!.blocks.some((b) => /V_pred|余弦|ΔV/.test(b.body))).toBe(
      false,
    );
    expect(zh[1]!.blocks.some((b) => /V_pred|余弦|ΔV/.test(b.body))).toBe(
      false,
    );
    expect(en[2]!.blocks[3]!.body).toContain("0.8");
    // boundary statements live once, where they belong
    expect(zh[2]!.blocks[2]!.body).toContain(
      "不构成对杯中成分或风味成因的测定",
    );
    expect(JSON.stringify(zh)).not.toContain("83K");
    expect(JSON.stringify(zh)).not.toContain("不是质量保证");
    const cites = aboutCitations("en");
    // UC Davis is withdrawn (its DOI resolves to a turmeric paper): only sources with a note in use are listed for the reader
    expect(cites.map((c) => c.id)).toEqual([
      "wcr_sensory_lexicon",
      "coffee_ad_astra",
      "gactt",
    ]);
    expect(
      cites
        .slice(0, 2)
        .every(
          (c) =>
            c.claimsLive > 0 &&
            c.locator &&
            c.terms &&
            c.use &&
            c.evidenceState === "LITERATURE_CLAIM",
        ),
    ).toBe(true);
    expect(cites.find((c) => c.id === "coffee_ad_astra")!.title).toContain(
      "Jonathan Gagné",
    );
    expect(
      cites.find((c) => c.id === "wcr_sensory_lexicon")!.terms,
    ).not.toContain("CC BY-SA");
    expect(cites.reduce((a, c) => a + c.claimsLive, 0)).toBe(6);
    const stats = aboutStats("zh-CN");
    expect(stats.find((s) => s.key === "assertions")!.value).toBeGreaterThan(
      80000,
    );
    expect(stats.find((s) => s.key === "consumers")!.value).toBe(4042);
    expect(stats.find((s) => s.key === "pending")!.value).toBe(5);
  });

  it("says what the product is for before any implementation word, names the author's work, and gives every number a unit and a use", () => {
    const author = aboutAuthor("zh-CN");
    expect(author.name).toContain("潘岱");
    expect(author.title).toBe("为品味而设计");
    expect(author.credit).toContain("潘岱");
    expect(aboutApproach("zh-CN").intro).toHaveLength(3);
    expect(aboutApproach("zh-CN").intro[2]).toContain("最后由你确认");
    expect(aboutApproach("zh-CN").title).toBe("从品味，到表达");
    expect(author.contributions.map((c) => c.value)).toEqual([94, 12, 16]);
    expect(author.contributions.every((c) => c.use.length > 0)).toBe(true);
    const scope = aboutScope("zh-CN");
    expect(scope.items.map((s) => s.key)).toEqual([
      "assertions",
      "coffees",
      "consumers",
      "sources",
    ]);
    expect(scope.items.find((s) => s.key === "coffees")!.note).toContain(
      "8,142",
    );
    expect(scope.items.find((s) => s.key === "consumers")!.label).toContain(
      "GACTT",
    );
    expect(scope.items.find((s) => s.key === "sources")!.value).toBe(2);
    expect(scope.items.every((s) => s.unit.length > 0)).toBe(true);
    const example = aboutExample("zh-CN");
    expect(example.words).toHaveLength(5);
    expect(example.eyebrow).toContain("示例");
    // three layers, no group title repeating the words (copy review 3)
    expect(example.cup.map((c) => c.label)).toEqual(["冲煮", "烘焙"]);
    expect(example.reference).toContain("参考风味");
    expect(example.brand).toBe("flavorwords");
    expect(aboutExample("en").words.some((w) => /[一-鿿]/.test(w))).toBe(false);
  });
});

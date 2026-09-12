import { describe, expect, it } from "vitest";
import {
  DIMENSIONS,
  buildVPred,
  buildVUser,
  cosine,
  displayTags,
  infer,
  present,
  productVectorBundle,
  projectConcepts,
  statementsFor,
} from "../packages/flavor-data/src/product-vector-v1";

describe("product-vector-v1 engine", () => {
  it("runs in the 12-dimension space of the design", () => {
    expect(DIMENSIONS).toEqual([
      "acidity", "sweetness", "body", "floral", "fruity", "nutty_chocolate", "fermented_winey", "bitter_roasted",
      "spice", "herbal_green", "woody_earthy", "defect",
    ]);
    expect(productVectorBundle.training_run_count).toBe(0);
    expect(productVectorBundle.alpha_default).toBe(0.5);
  });

  it("builds V_user from the owner's Q5-Q10 increments", () => {
    const v = buildVUser({ Q8_aroma: "A" }); // floral +3 only
    expect(v[DIMENSIONS.indexOf("floral")] ?? 0).toBeCloseTo(1, 6);
    expect(v.filter((x) => x !== 0)).toHaveLength(1);
    const mixed = buildVUser({ Q5_acid: "A", Q6_sweet: "C" }); // acidity 2, fruity 1+2, sweetness 2
    const idx = (d: string) => mixed[DIMENSIONS.indexOf(d)] ?? 0;
    expect(idx("fruity")).toBeGreaterThan(idx("acidity"));
    expect(idx("acidity")).toBeCloseTo(idx("sweetness"), 6);
  });

  it("reports the basis of every context option and ignores options without a corpus row", () => {
    const { vPred, contextBasis } = buildVPred({ c0_preparation: "cold_brew", c1_roast: "light" });
    expect(contextBasis.map((b) => b.basis)).toEqual(["NO_CORPUS_ROW_LITERATURE_CLAIM_PENDING", "CORPUS_MEASURED"]);
    expect(Math.abs(Math.hypot(...vPred) - 1)).toBeLessThan(1e-6);
  });

  it("ranks profiles by cosine and keeps scores as similarities", () => {
    const result = infer({ c0_preparation: "pour_over_v60", c1_roast: "light", c2_process: "washed" }, { Q5_acid: "A", Q8_aroma: "A", Q10_clean: "A" });
    expect(result.profiles).toHaveLength(3);
    expect(result.profiles[0]!.similarity).toBeGreaterThanOrEqual(result.profiles[1]!.similarity);
    expect(result.profiles[0]!.similarity).toBeLessThanOrEqual(1);
    expect(result.scoreSemantics).toContain("not a probability");
    expect(cosine(result.vTarget, result.vTarget)).toBeCloseTo(1, 6);
  });

  it("projects user-entered tasting notes through the same matrix and lets defect lower the match", () => {
    const clean = projectConcepts(["sensory.jasmine", "sensory.lemon"]);
    const tainted = projectConcepts(["sensory.jasmine", "sensory.lemon", "sensory.musty", "sensory.paper"]);
    const user = buildVUser({ Q8_aroma: "A", Q5_acid: "A" });
    expect(cosine(user, clean)).toBeGreaterThan(cosine(user, tainted));
  });
});

describe("product-vector-v1 presentation layer", () => {
  it("priority 1: concept-level minimalist tags in the Chinese specialty vocabulary, ranked by projection weight", () => {
    const ids = ["sensory.jasmine", "sensory.peach", "sensory.bergamot", "sensory.lime", "sensory.green_tea"];
    const vector = projectConcepts(ids);
    const zh = displayTags(vector, "zh-CN", 4, ids);
    const en = displayTags(vector, "en", 4, ids);
    expect(zh).toHaveLength(4);
    expect(zh).toContain("茉莉花");
    expect(zh).toContain("水蜜桃");
    expect(en).toContain("jasmine");
    expect(en).toContain("peach");
  });

  it("priority 2: dimension-level tags for a bare vector, from the owner's CN tag lists, without abstract dimension names", () => {
    const floralFruity = [0.3, 0.2, 0, 0.8, 0.6, 0, 0, 0, 0, 0, 0, 0];
    const zh = displayTags(floralFruity, "zh-CN");
    expect(zh[0]).toBe("茉莉花");
    expect(zh[1]).toBe("水蜜桃");
    expect(zh.some((t) => t.includes("floral") || t.includes("fruity"))).toBe(false);
  });

  it("defect guard: no defect tag on a clean vector, defect tag when defect dominates", () => {
    const clean = [0.5, 0.5, 0, 0.5, 0.5, 0, 0, 0, 0, 0, 0, 0.2];
    expect(displayTags(clean, "zh-CN")).not.toContain("风味瑕疵");
    const bad = [0.1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.95];
    expect(displayTags(bad, "zh-CN")).toContain("风味瑕疵");
    expect(displayTags(bad, "zh-CN", 4, ["sensory.musty", "sensory.jasmine"])).toContain("霉味");
  });

  it("science fold: combination statements only when every part is answered, most specific first, with evidence state", () => {
    const lines = statementsFor({ c0_preparation: "pour_over_v60", c1_roast: "light" }, "en");
    expect(lines[0]!.about).toBe("C0_V60__C1_LIGHT");
    expect(lines.map((l) => l.about)).toContain("C1_LIGHT");
    expect(lines.every((l) => ["OWNER_STATEMENT", "CORPUS_MEASURED", "LITERATURE_CLAIM"].includes(l.evidenceState))).toBe(true);
    expect(statementsFor({ c1_roast: "light" }, "en").map((l) => l.about)).not.toContain("C0_V60__C1_LIGHT");
  });

  it("renders one vector backend in two languages: minimalist tags for zh-CN, scientific wording for en", () => {
    const result = infer({ c0_preparation: "pour_over_v60", c1_roast: "light", c2_process: "washed" }, { Q5_acid: "A", Q8_aroma: "A", Q10_clean: "A" });
    const zh = present(result, "zh-CN");
    const en = present(result, "en");
    expect(zh.headline).not.toBeNull();
    expect(zh.headline!.tags.length).toBeGreaterThanOrEqual(3);
    expect(zh.headline!.tags.length).toBeLessThanOrEqual(4);
    expect(en.headline!.profileId).toBe(zh.headline!.profileId);
    expect(en.headline!.title).not.toBe(zh.headline!.title);
    expect(zh.science.some((l) => l.about === "C0_V60__C1_LIGHT")).toBe(true);
    expect(en.science.every((l) => l.evidenceState && l.citationRef)).toBe(true);
  });
});

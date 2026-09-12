import { describe, expect, it } from "vitest";
import {
  DIMENSIONS,
  buildVPred,
  buildVUser,
  cosine,
  infer,
  productVectorBundle,
  projectConcepts,
} from "../packages/flavor-data/src/product-vector-v1";

describe("product-vector-v1 engine", () => {
  it("runs in the 12-dimension space of the design", () => {
    expect(DIMENSIONS).toEqual([
      "acidity", "sweetness", "body", "floral", "fruity", "nutty_chocolate", "fermented_winey", "bitter_roasted",
      "spice", "herbal_green", "woody_earthy", "defect",
    ]);
    expect(productVectorBundle.training_run_count).toBe(0);
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

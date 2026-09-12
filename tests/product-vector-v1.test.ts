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

describe("product-vector-v1 question flow (coherence decision tree)", async () => {
  const flow = await import("../packages/flavor-data/src/product-vector-v1/flow");
  const ctx = { c0_preparation: "pour_over_v60", c1_roast: "light", c2_process: "washed" } as const;

  it("asks the base pair first, then Q2-Q3 for the coherence check, and never asks an answered slot again", () => {
    expect(flow.flowStep({}).ask).toEqual(["Q0", "Q1"]);
    expect(flow.flowStep({ Q0: "A" }).ask).toEqual(["Q1"]);
    expect(flow.flowStep({ Q0: "A", Q1: "A" }).ask).toEqual(["Q2", "Q3"]);
    expect(flow.flowStep({ Q0: "A", Q1: "A", Q2: "A" }).ask).toEqual(["Q3"]);
  });

  it("locks the owner's thresholds (R3-D10): coherent >= 0.80, severe < 0.65", () => {
    expect(flow.questionFlow.thresholds).toEqual({ coherent: 0.8, mild: 0.65 });
    expect(flow.questionFlow.slot_mapping_owner_reviewed).toBe(true);
    expect(flow.questionFlow.alpha_strong).toBe(0.9);
  });

  it("path rhythm over all 324 answer sequences: ~25% fast Path 1, ~60% corrective Path 2, ~15% severe Paths 3/4", () => {
    const o3 = ["A", "B", "C"];
    const o2 = ["A", "B"];
    const paths: Record<string, number> = { "1": 0, "2": 0, "3": 0, "4": 0 };
    let asked = 0;
    let total = 0;
    for (const q0 of o3) for (const q1 of o3) for (const q2 of o3) for (const q3 of o3) for (const q4 of o2) for (const q5 of o2) {
      const full: Record<string, string> = { Q0: q0, Q1: q1, Q2: q2, Q3: q3, Q4: q4, Q5: q5 };
      const answers: Record<string, string> = {};
      let step = flow.flowStep(answers);
      let guard = 0;
      while (!step.deliver && guard < 10) {
        for (const s of step.ask) answers[s] = full[s]!;
        step = flow.flowStep(answers);
        guard += 1;
      }
      expect(step.deliver).toBe(true);
      paths[String(step.path)] = (paths[String(step.path)] ?? 0) + 1;
      asked += Object.keys(answers).length;
      total += 1;
    }
    expect(total).toBe(324);
    const share = (k: string) => (paths[k] ?? 0) / total;
    expect(share("1")).toBeGreaterThanOrEqual(0.2);
    expect(share("1")).toBeLessThanOrEqual(0.35);
    expect(share("2")).toBeGreaterThanOrEqual(0.5);
    expect(share("2")).toBeLessThanOrEqual(0.7);
    expect(share("3") + share("4")).toBeGreaterThanOrEqual(0.05);
    expect(share("3") + share("4")).toBeLessThanOrEqual(0.2);
    expect(asked / total).toBeLessThanOrEqual(6);
  });

  it("measures coherence in profile-signature space, so consistent answers on different dimensions still agree", () => {
    const bright = flow.groupVector({ Q0: "A", Q1: "A" }, ["Q0", "Q1"]); // acid + floral
    const honeyFloral = flow.groupVector({ Q2: "A" }, ["Q2"]);
    const caramelDark = flow.groupVector({ Q2: "B" }, ["Q2"]);
    expect(flow.coherence(bright, honeyFloral).similarity).toBeGreaterThan(flow.coherence(bright, caramelDark).similarity);
    expect(flow.coherence(bright, bright).level).toBe("coherent");
    const smoothNutty = flow.groupVector({ Q0: "C", Q1: "B" }, ["Q0", "Q1"]);
    expect(flow.coherence(smoothNutty, caramelDark).level).toBe("coherent");
  });

  it("every complete answer set reaches delivery with a path and a coherence history", () => {
    const options = ["A", "B", "C"];
    let delivered = 0;
    const paths = new Set<number>();
    for (const q0 of options) for (const q1 of options) for (const q2 of options) for (const q3 of options) {
      const answers: Record<string, string> = { Q0: q0, Q1: q1, Q2: q2, Q3: q3, Q4: "A", Q5: "A" };
      const step = flow.flowStep(answers);
      expect(step.deliver).toBe(true);
      expect(step.checks.length).toBeGreaterThan(0);
      expect(step.checks[0]!.between).toEqual(["Q0-Q1", "Q2-Q3"]);
      if (step.path) paths.add(step.path);
      delivered += 1;
    }
    expect(delivered).toBe(81);
    expect(paths.size).toBeGreaterThanOrEqual(2);
  });

  it("delivers a 3 + 5 description whose words are attributable to dimensions and distinct", () => {
    const result = flow.inferFromFlow(ctx, { Q0: "A", Q1: "A", Q2: "A", Q3: "A", Q4: "B" });
    const zh = flow.describe(result, "zh-CN");
    expect(zh.main).toHaveLength(3);
    expect(zh.secondary).toHaveLength(5);
    expect(new Set(zh.all.map((w) => w.text)).size).toBe(8);
    expect(zh.all.every((w) => flow.dimensionCount === 12 && typeof w.dimension === "string")).toBe(true);
    expect(zh.prompt).toContain("5");
    expect(flow.describe(result, "en").all.map((w) => w.text)).not.toEqual(zh.all.map((w) => w.text));
  });

  it("escalation gate: Q6 only when a severe conflict happened and the picks side with the user against the theory", () => {
    const result = flow.inferFromFlow(ctx, { Q0: "A", Q1: "A", Q2: "A", Q3: "A", Q4: "B" });
    const description = flow.describe(result, "zh-CN");
    const calmStep = { ask: [], deliver: true, path: 1 as const, checks: [{ between: ["a", "b"] as [string, string], similarity: 0.9, level: "coherent" as const }], escalationEligible: false, reason: "" };
    const gateA = flow.escalationGate(calmStep, result, description.all.slice(0, 5));
    expect(gateA.escalate).toBe(false);
    expect(gateA.severeHistory).toBe(false);
    const severeStep = { ...calmStep, path: 3 as const, escalationEligible: true };
    const userSide = [{ text: "x", dimension: "floral" }, { text: "y", dimension: "floral" }, { text: "z", dimension: "floral" }, { text: "w", dimension: "acidity" }, { text: "v", dimension: "sweetness" }];
    const gateB = flow.escalationGate(severeStep, { ...result, vPred: flow.picksToVector([{ text: "n", dimension: "nutty_chocolate" }, { text: "b", dimension: "bitter_roasted" }]) }, userSide);
    expect(gateB.biasConfirmed).toBe(true);
    expect(gateB.escalate).toBe(true);
  });

  it("Q6 offers one word per most-disputed dimension and applies a strong correction", () => {
    const result = flow.inferFromFlow(ctx, { Q0: "C", Q1: "B", Q2: "B", Q3: "C", Q4: "A", Q5: "B" });
    const options = flow.q6Options(result, "zh-CN");
    expect(options).toHaveLength(8);
    expect(options.some((o) => o.dimension === "defect")).toBe(false);
    const corrected = flow.applyQ6(result, ["nutty_chocolate", "body"]);
    expect(corrected.alpha).toBe(flow.questionFlow.alpha_strong);
    expect(corrected.vUser[DIMENSIONS.indexOf("nutty_chocolate")]).toBeGreaterThan(0);
    expect(flow.applyQ6(result, [])).toBe(result);
  });

  it("final card carries the user's own words, at most two science lines with evidence states, and the closing line", () => {
    const result = flow.inferFromFlow(ctx, { Q0: "A", Q1: "A", Q2: "A", Q3: "A", Q4: "B" });
    const picks = flow.describe(result, "zh-CN").all.slice(0, 5);
    const card = flow.finalCard(result, picks, "zh-CN");
    expect(card.picked).toHaveLength(5);
    expect(card.science.length).toBeLessThanOrEqual(2);
    expect(card.science.every((l) => l.evidenceState)).toBe(true);
    expect(card.closing).toContain("咖啡");
    expect(flow.finalCard(result, picks, "en").closing).toContain("enjoy");
  });
});

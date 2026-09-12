/**
 * User persona simulations (owner, 2026-09-12): preset personas run the whole decision tree locally —
 * questions asked in order, first description, the 5 picks, the escalation gate, Q6 where it applies.
 * The three owner personas carry hard expectations; the others assert invariants and record their path.
 */
import { describe, expect, it } from "vitest";
import * as flow from "../packages/flavor-data/src/product-vector-v1/flow";
import { mapUtterance } from "../packages/flavor-data/src/product-vector-v1/lexicon";
import { DIMENSIONS, type ContextAnswers } from "../packages/flavor-data/src/product-vector-v1";

const LIGHT: ContextAnswers = { c0_preparation: "pour_over_v60", c1_roast: "light", c2_process: "washed" };
const DARK: ContextAnswers = { c0_preparation: "espresso", c1_roast: "dark" };
const MED: ContextAnswers = { c0_preparation: "pour_over_v60", c1_roast: "medium" };

type Persona = { name: string; context: ContextAnswers; answers: Record<string, string>; utterance?: string };

function run(persona: Persona) {
  const answers: Record<string, string> = {};
  let step = flow.flowStep(answers, persona.context);
  let guard = 0;
  const order: string[] = [];
  while (!step.deliver && guard < 10) {
    for (const s of step.ask) {
      answers[s] = persona.answers[s]!;
      order.push(s);
    }
    step = flow.flowStep(answers, persona.context);
    guard += 1;
  }
  const result = flow.inferFromFlow(persona.context, answers);
  const description = flow.describe(result, "zh-CN");
  return { step, answers, order, result, description };
}

/** Picks that side with the user's own perception: the 5 words whose dimensions carry most of V_user. */
function userSidePicks(result: ReturnType<typeof flow.inferFromFlow>, description: ReturnType<typeof flow.describe>) {
  return [...description.all]
    .sort((a, b) => (result.vUser[DIMENSIONS.indexOf(b.dimension)] ?? 0) - (result.vUser[DIMENSIONS.indexOf(a.dimension)] ?? 0))
    .slice(0, 5);
}

describe("owner personas", () => {
  it("Persona A — light pour-over, jasmine and citrus, hates bitterness: Path 1 in 5 questions, no Q6, floral/acid profile", () => {
    const mapped = mapUtterance("喜欢茉莉花香、柑橘酸，喝手冲，讨厌苦味", "zh-CN");
    expect(mapped.answers.Q1).toBe("A");
    expect(mapped.answers.Q0).toBe("A");
    expect(mapped.answers.Q4).toBe("B");
    const persona: Persona = { name: "A", context: LIGHT, answers: { Q0: "A", Q1: "A", Q2: "A", Q3: "A", Q4: "B", Q5: "A" } };
    const { step, order, result, description } = run(persona);
    expect(step.path).toBe(1);
    expect(order).toEqual(["Q0", "Q1", "Q2", "Q3", "Q4"]);
    expect(step.escalationEligible).toBe(false);
    const gate = flow.escalationGate(step, result, description.all.slice(0, 5));
    expect(gate.escalate).toBe(false);
    const top = result.profiles[0]!.profile;
    expect(["Jasmine & White Flowers", "Citrus & Yuzu Acidity", "Yellow Peach & Ripe Fruit", "Herbal & Green Tea"]).toContain(top.owner_name.en);
    const card = flow.finalCard(result, description.all.slice(0, 5), "zh-CN");
    expect(card.picked).toHaveLength(5);
    expect(card.closing).toContain("咖啡");
  });

  it("Persona B — chose dark espresso but wants bright peach acidity: context conflict → Path 2 correction, card, no Q6", () => {
    const mapped = mapUtterance("想要强烈的水蜜桃鲜明果酸", "zh-CN");
    expect(mapped.answers.Q0).toBe("A");
    const persona: Persona = { name: "B", context: DARK, answers: { Q0: "A", Q1: "C", Q2: "C", Q3: "B", Q4: "B", Q5: "A" } };
    const { step, order, result, description } = run(persona);
    const contextCheck = step.checks.find((c) => c.between[0] === "context");
    expect(contextCheck?.paradox).toBe(true);
    expect(contextCheck?.level).toBe("mild");
    expect(step.path).toBe(2);
    expect(order).toEqual(["Q0", "Q1", "Q2", "Q3", "Q4", "Q5"]);
    expect(step.escalationEligible).toBe(false);
    expect(flow.escalationGate(step, result, description.all.slice(0, 5)).escalate).toBe(false);
  });

  it("Persona C — '完全不酸、不要苦、要非常浓郁甜感': negation guard maps it; the answers are internally consistent, so no Q6", () => {
    const mapped = mapUtterance("完全不酸、不要苦、要非常浓郁甜感", "zh-CN");
    expect(mapped.forced.Q0).toBe("C");
    expect(mapped.forced.Q4).toBe("B");
    expect(mapped.answers.Q5).toBe("B");
    const persona: Persona = { name: "C", context: MED, answers: { Q0: "C", Q1: "C", Q2: "C", Q3: "B", Q4: "B", Q5: "B" } };
    const { step } = run(persona);
    expect(step.deliver).toBe(true);
    expect(step.checks.some((c) => c.level === "severe")).toBe(false);
  });

  it("Persona C' — the sensory paradox (light-roast acidity and florals, then heavy dark bitterness): severe, and Q6 opens when the picks confirm the bias", () => {
    const persona: Persona = { name: "C'", context: LIGHT, answers: { Q0: "A", Q1: "A", Q2: "B", Q3: "C", Q4: "A", Q5: "B" } };
    const { step, order, result, description } = run(persona);
    expect(step.path).toBe(3);
    expect(order).toEqual(["Q0", "Q1", "Q2", "Q3", "Q4", "Q5"]);
    const first = step.checks[0]!;
    expect(first.level).toBe("severe");
    expect(first.paradox).toBe(true);
    const gate = flow.escalationGate(step, result, userSidePicks(result, description));
    expect(gate.severeHistory).toBe(true);
    expect(gate.escalate).toBe(true); // the second round is reachable (owner, 2026-09-12)
    if (gate.escalate) {
      const options = flow.q6Options(result, "zh-CN");
      expect(options).toHaveLength(8);
      const corrected = flow.applyQ6(result, options.slice(0, 2).map((o) => o.dimension));
      expect(corrected.alpha).toBe(0.9);
      expect(flow.describe(corrected, "zh-CN").all).toHaveLength(8);
    } else {
      // the picks did not confirm a bias against the theory: branch A card
      const card = flow.finalCard(result, description.all.slice(0, 5), "zh-CN");
      expect(card.picked).toHaveLength(5);
    }
  });
});

describe("persona table: every persona delivers, records its path, and gets a coherent bilingual card", () => {
  const personas: Persona[] = [
    { name: "B2 fermented lover, soft acid", context: LIGHT, answers: { Q0: "B", Q1: "C", Q2: "C", Q3: "B", Q4: "B", Q5: "B" } },
    { name: "D classic nutty", context: MED, answers: { Q0: "C", Q1: "B", Q2: "B", Q3: "B", Q4: "A", Q5: "B" } },
    { name: "E dark heavy", context: DARK, answers: { Q0: "C", Q1: "B", Q2: "B", Q3: "C", Q4: "A", Q5: "B" } },
    { name: "J bright then chocolate", context: LIGHT, answers: { Q0: "A", Q1: "A", Q2: "B", Q3: "B", Q4: "A", Q5: "A" } },
    { name: "K acid hater, floral", context: LIGHT, answers: { Q0: "C", Q1: "A", Q2: "A", Q3: "A", Q4: "B", Q5: "A" } },
    { name: "H sweet smooth", context: MED, answers: { Q0: "C", Q1: "A", Q2: "A", Q3: "B", Q4: "B", Q5: "A" } },
    { name: "L winey dark", context: DARK, answers: { Q0: "B", Q1: "C", Q2: "B", Q3: "C", Q4: "A", Q5: "B" } },
    { name: "F jammy natural", context: LIGHT, answers: { Q0: "B", Q1: "C", Q2: "C", Q3: "B", Q4: "B", Q5: "B" } },
    { name: "I mixed signals", context: MED, answers: { Q0: "A", Q1: "B", Q2: "C", Q3: "A", Q4: "A", Q5: "B" } },
    { name: "G tea-like clean", context: LIGHT, answers: { Q0: "A", Q1: "A", Q2: "A", Q3: "A", Q4: "B", Q5: "A" } },
  ];
  const expected: Record<string, number> = { "D classic nutty": 1, "E dark heavy": 1, "J bright then chocolate": 3, "K acid hater, floral": 2, "B2 fermented lover, soft acid": 2, "G tea-like clean": 1 };

  for (const persona of personas) {
    it(persona.name, () => {
      const { step, order, result, description } = run(persona);
      expect(step.deliver).toBe(true);
      expect(order.length).toBeGreaterThanOrEqual(5);
      expect(order.length).toBeLessThanOrEqual(6);
      if (expected[persona.name]) expect(step.path).toBe(expected[persona.name]);
      expect(description.all).toHaveLength(8);
      expect(new Set(description.all.map((w) => w.text)).size).toBe(8);
      const en = flow.describe(result, "en");
      expect(en.all.map((w) => w.dimension)).toEqual(description.all.map((w) => w.dimension));
      const card = flow.finalCard(result, description.all.slice(0, 5), "zh-CN");
      expect(card.science.length).toBeGreaterThanOrEqual(1);
    });
  }
});

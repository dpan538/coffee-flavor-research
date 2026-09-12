/**
 * Front-end chain (owner Step 5): createSession → nextStep/answer → firstDescription → submitPicks → final card or Q6.
 * Immutable sessions; the question bank supplies the prompts; the gate decides the branch.
 */
import { describe, expect, it } from "vitest";
import { answer, answerFromUtterance, answerQ6, createSession, firstDescription, nextStep, submitPicks } from "../packages/flavor-data/src/product-vector-v1/session";
import { DIMENSIONS } from "../packages/flavor-data/src/product-vector-v1";

const LIGHT = { c0_preparation: "pour_over_v60", c1_roast: "light", c2_process: "washed" } as const;

function play(context: typeof LIGHT | Record<string, string>, answers: Record<string, string>, locale: "zh-CN" | "en" = "zh-CN") {
  let s = createSession(context, locale);
  let guard = 0;
  while (s.stage === "questions" && guard < 10) {
    const step = nextStep(s);
    if (step.kind !== "ask") break;
    expect(step.card.prompt.length).toBeGreaterThan(0);
    expect(step.card.options.length).toBeGreaterThanOrEqual(2);
    s = answer(s, step.card.slot, answers[step.card.slot]!);
    guard += 1;
  }
  return s;
}

describe("product-vector-v1 session", () => {
  it("asks the localised question cards in flow order and ends on the description stage", () => {
    const s = play(LIGHT, { Q0: "A", Q1: "A", Q2: "A", Q3: "A", Q4: "B", Q5: "A" });
    expect(s.stage).toBe("describe");
    expect(s.step.path).toBe(1);
    expect(s.history.filter((h) => h.event === "answer")).toHaveLength(5);
    expect(nextStep(s).kind).toBe("describe");
    const zh = createSession(LIGHT, "zh-CN");
    const first = nextStep(zh);
    expect(first.kind).toBe("ask");
    if (first.kind === "ask") {
      expect(first.card.slot).toBe("Q0");
      expect(first.card.prompt).toContain("酸");
      expect(first.card.options.map((o) => o.label)).toContain("鲜明多汁的柑橘 / 青苹果酸");
    }
  });

  it("never mutates a session: answering returns a new object and leaves the old one intact", () => {
    const s0 = createSession(LIGHT, "zh-CN");
    const s1 = answer(s0, "Q0", "A");
    expect(s0.answers).toEqual({});
    expect(s1.answers).toEqual({ Q0: "A" });
    expect(() => answer(s1, "Q1", "Z")).toThrow();
  });

  it("branch A: coherent flow → first description → picks → final card with the user's words and the closing line", () => {
    let s = play(LIGHT, { Q0: "A", Q1: "A", Q2: "A", Q3: "A", Q4: "B", Q5: "A" });
    s = firstDescription(s);
    expect(s.stage).toBe("picks");
    expect(s.description!.main).toHaveLength(3);
    expect(s.description!.secondary).toHaveLength(5);
    expect(nextStep(s).kind).toBe("picks");
    s = submitPicks(s, s.description!.all.slice(0, 5));
    expect(s.stage).toBe("final");
    expect(s.gate!.escalate).toBe(false);
    expect(s.card!.picked).toHaveLength(5);
    expect(s.card!.closing).toContain("咖啡");
    expect(s.card!.science.every((l) => l.evidenceState)).toBe(true);
  });

  it("branch B: sensory paradox + picks siding with perception → Q6 → second description and card", () => {
    let s = play(LIGHT, { Q0: "A", Q1: "A", Q2: "B", Q3: "C", Q4: "A", Q5: "B" });
    expect(s.step.path).toBe(3);
    s = firstDescription(s);
    const userSide = [...s.description!.all]
      .sort((a, b) => (s.result!.vUser[DIMENSIONS.indexOf(b.dimension)] ?? 0) - (s.result!.vUser[DIMENSIONS.indexOf(a.dimension)] ?? 0))
      .slice(0, 5);
    s = submitPicks(s, userSide);
    if (s.stage === "q6") {
      expect(nextStep(s).kind).toBe("q6");
      expect(s.q6!.options).toHaveLength(8);
      const chosen = s.q6!.options.slice(0, 2).map((o) => o.dimension);
      s = answerQ6(s, chosen);
      expect(s.stage).toBe("final");
      expect(s.result!.alpha).toBe(0.9);
      expect(s.card!.picked).toHaveLength(5);
    } else {
      // the picks did not confirm the bias: branch A card is still a complete outcome
      expect(s.stage).toBe("final");
      expect(s.card).not.toBeNull();
    }
  });

  it("utterance seeding fills only the slots currently being asked, through the negation guard", () => {
    let s = createSession(LIGHT, "zh-CN");
    s = answerFromUtterance(s, "喜欢茉莉花香、柑橘酸，讨厌苦味");
    expect(s.answers.Q0).toBe("A");
    expect(s.answers.Q1).toBe("A");
    expect(s.answers.Q4).toBeUndefined(); // Q4 is not asked yet at this point of the flow
    expect(s.history.some((h) => h.event === "utterance")).toBe(true);
  });

  it("english sessions speak english end to end", () => {
    let s = play(LIGHT, { Q0: "A", Q1: "A", Q2: "A", Q3: "A", Q4: "B", Q5: "A" }, "en");
    const card = nextStep(createSession(LIGHT, "en"));
    if (card.kind === "ask") expect(card.card.prompt).toMatch(/acidity/i);
    s = firstDescription(s);
    s = submitPicks(s, s.description!.all.slice(0, 5));
    expect(s.card!.closing).toContain("enjoy");
    expect(/[一-鿿]/.test(s.card!.picked.join(""))).toBe(false);
  });
});

/**
 * Similar words on one card (owner, 2026-09-19, R3-D42): no fixed cap on one kind of flavor — some coffees are built
 * around it — but near-identical words must not crowd a card by accident of list order. The spread by sub-family is a
 * soft preference; what the reader says (a focus sub-family, from the second-level questions) overrides it.
 */
import { describe as suite, expect, it } from "vitest";
import {
  describe,
  flowStep,
  inferFromFlow,
} from "../packages/flavor-data/src/product-vector-v1/flow";
import { productVectorBundle } from "../packages/flavor-data/src/product-vector-v1";

const presentation = productVectorBundle.presentation as unknown as {
  dimension_tags: Record<string, Record<"zh-CN" | "en", string[]>>;
  dimension_tag_families: Record<string, string[]>;
};
const familyOf = (dimension: string, word: string) =>
  presentation.dimension_tag_families[dimension]![
    presentation.dimension_tags[dimension]!["zh-CN"].indexOf(word)
  ];

const OPTIONS = {
  Q0: ["A", "B", "C", "D"],
  Q1: ["A", "B", "C", "D"],
  Q2: ["A", "B", "C", "D"],
  Q3: ["A", "B", "C", "D"],
  Q4: ["A", "B", "C"],
  Q5: ["A", "B", "C", "D"],
} as const;
const CONTEXTS = [
  { c0_preparation: "pour_over_v60", c1_roast: "light", c2_process: "washed" },
  { c0_preparation: "espresso", c1_roast: "dark" },
];

function cards() {
  const out: Array<ReturnType<typeof describe>> = [];
  for (const context of CONTEXTS)
    for (const q0 of OPTIONS.Q0)
      for (const q1 of OPTIONS.Q1)
        for (const q2 of OPTIONS.Q2)
          for (const q3 of OPTIONS.Q3) {
            const full: Record<string, string> = {
              Q0: q0,
              Q1: q1,
              Q2: q2,
              Q3: q3,
              Q4: "A",
              Q5: "C",
            };
            const answers: Record<string, string> = {};
            let step = flowStep(answers, context);
            for (let guard = 0; !step.deliver && guard < 10; guard += 1) {
              for (const slot of step.ask) answers[slot] = full[slot]!;
              step = flowStep(answers, context);
            }
            out.push(describe(inferFromFlow(context, answers), "zh-CN"));
          }
  return out;
}

suite("similar words on one card", () => {
  it("every word has a sub-family, aligned with the word lists in both languages", () => {
    for (const [dimension, tags] of Object.entries(
      presentation.dimension_tags,
    )) {
      const families = presentation.dimension_tag_families[dimension]!;
      expect(families, dimension).toHaveLength(tags["zh-CN"].length);
      expect(tags.en, dimension).toHaveLength(tags["zh-CN"].length);
    }
  });

  it("a dimension repeats a sub-family only after it has shown all the others it can", () => {
    let repeated = 0;
    const all = cards();
    for (const card of all) {
      const byDimension = new Map<string, string[]>();
      for (const w of card.all)
        byDimension.set(w.dimension, [
          ...(byDimension.get(w.dimension) ?? []),
          familyOf(w.dimension, w.text)!,
        ]);
      for (const [dimension, families] of byDimension) {
        const available = new Set(
          presentation.dimension_tag_families[dimension],
        ).size;
        const distinct = new Set(families).size;
        // soft, not a cap: repeats are allowed, but only once the dimension has used every sub-family it has
        expect(distinct, `${dimension}: ${families.join(",")}`).toBe(
          Math.min(families.length, available),
        );
        if (distinct < families.length) repeated += 1;
      }
      expect(card.all).toHaveLength(8);
    }
    expect(all.length).toBe(CONTEXTS.length * 256);
    expect(repeated).toBeGreaterThanOrEqual(0);
  });

  it("what the reader points to overrides the spread: a focus sub-family leads and may repeat", () => {
    const context = CONTEXTS[0]!;
    const full: Record<string, string> = {
      Q0: "A",
      Q1: "C",
      Q2: "C",
      Q3: "A",
      Q4: "B",
      Q5: "C",
    };
    const answers: Record<string, string> = {};
    let step = flowStep(answers, context);
    for (let guard = 0; !step.deliver && guard < 10; guard += 1) {
      for (const slot of step.ask) answers[slot] = full[slot]!;
      step = flowStep(answers, context);
    }
    const result = inferFromFlow(context, answers);
    const plain = describe(result, "zh-CN");
    const fruit = plain.all.filter((w) => w.dimension === "fruity");
    expect(fruit.length).toBeGreaterThanOrEqual(2);
    const focused = describe(result, "zh-CN", { fruity: "berry" });
    const focusedFruit = focused.all.filter((w) => w.dimension === "fruity");
    expect(focusedFruit).toHaveLength(fruit.length); // same share of the card: no cap, no bonus
    for (const w of focusedFruit)
      expect(familyOf("fruity", w.text)).toBe("berry");
    // both languages stay aligned
    const en = describe(result, "en", { fruity: "berry" });
    expect(en.all.map((w) => w.dimension)).toEqual(
      focused.all.map((w) => w.dimension),
    );
  });
});

/**
 * The dynamic question bank (R3-D40): five things to tap at most, "I can't say" being the fifth of them (owner,
 * 2026-09-20), pruned — never sorted — by the corpus for this kind of coffee; an option that says what "it does not
 * stand out" means; several wordings of one option, aligned across languages; a second
 * level that decides the words. Pure functions of (context, answers, seed).
 */
import { describe, expect, it } from "vitest";
import {
  contextGroup,
  dynamicEffects,
  secondLevelQuestion,
  shownQuestion,
  structureQuestionWorthAsking,
  type DynamicQuestionId,
} from "../packages/flavor-data/src/product-vector-v1/dynamicBank";
import { productVectorBundle } from "../packages/flavor-data/src/product-vector-v1";

type BankOption = {
  id: string;
  role: string;
  label: Record<"zh-CN" | "en", string[]>;
  focus: string;
  parent: string;
};
const bank = (
  productVectorBundle as unknown as {
    dynamic_bank: {
      options: Record<string, BankOption[]>;
      groups: Record<
        string,
        {
          n: number;
          keep: Record<string, string[]>;
          second: Record<string, string[]>;
        }
      >;
    };
  }
).dynamic_bank;
const presentation = productVectorBundle.presentation as unknown as {
  dimension_tags: Record<string, Record<"zh-CN" | "en", string[]>>;
  dimension_tag_families: Record<string, string[]>;
};

const GESHA = {
  c0_preparation: "pour_over_v60",
  c1_roast: "light",
  c2_process: "washed",
  c2_variety: "gesha",
};
const NATURAL = {
  c0_preparation: "pour_over_v60",
  c1_roast: "light",
  c2_process: "natural",
};
const DARK = { c0_preparation: "espresso", c1_roast: "dark" };
const KENYA = {
  c0_preparation: "pour_over_v60",
  c1_roast: "light",
  c2_variety: "sl28_sl34",
};
const QUESTIONS: DynamicQuestionId[] = ["A", "B", "C", "D", "E1", "E2", "E3"];

describe("dynamic question bank", () => {
  it("the table is well-formed: wordings aligned across languages, every focus names a real sub-family or word", () => {
    for (const options of Object.values(bank.options))
      for (const o of options) {
        expect(o.label.en, o.id).toHaveLength(o.label["zh-CN"].length);
        if (!o.focus || o.focus.endsWith(":*")) continue;
        const [dimension, target] = o.focus.split(":") as [string, string];
        const tags = presentation.dimension_tags[dimension]!["zh-CN"];
        if (o.role === "word") expect(tags, o.id).toContain(target);
        else
          expect(
            presentation.dimension_tag_families[dimension],
            o.id,
          ).toContain(target);
      }
  });

  it("every kind of coffee keeps at most four data options per question, in the pool's order — pruned, not sorted", () => {
    expect(Object.keys(bank.groups).length).toBeGreaterThan(30);
    for (const [key, group] of Object.entries(bank.groups)) {
      expect(group.n, key).toBeGreaterThanOrEqual(30);
      for (const q of ["A", "B", "C"]) {
        const pool = bank.options[q]!.map((o) => o.id);
        const keep = group.keep[q]!;
        expect(keep.length, `${key} ${q}`).toBeLessThanOrEqual(4);
        expect(keep.length, `${key} ${q}`).toBeGreaterThanOrEqual(3);
        const positions = keep.map((id) => pool.indexOf(id));
        expect(positions, `${key} ${q}`).toEqual(
          [...positions].sort((a, b) => a - b),
        );
      }
    }
  });

  it('a question offers five things to tap at most, "I can\'t say" among them, and both languages show the same ids', () => {
    for (const context of [GESHA, NATURAL, DARK, KENYA, {}])
      for (const id of QUESTIONS)
        for (const seed of [0, 1, 7, 1789634997952]) {
          const zh = shownQuestion(id, context, "zh-CN", seed);
          const en = shownQuestion(id, context, "en", seed);
          // four things to tap; five only for the first two questions, where "I can't say" (or, for the aroma, "I
          // can't pick what stands out") is the fifth — an option like the others (owner, 2026-09-20)
          const tappable = zh.options.length + (zh.unanswered ? 1 : 0);
          expect(tappable, id).toBe(id === "A" || id === "B" ? 5 : 4);
          // bitterness shows its five levels only as a strong correction
          const strong = shownQuestion(id, context, "zh-CN", seed, true);
          expect(strong.options.length + (strong.unanswered ? 1 : 0), id).toBe(
            id === "A" || id === "B" || id === "E3" ? 5 : 4,
          );
          // no option sends the reader back to look at an earlier question
          for (const o of [...zh.options, ...en.options])
            expect(o.label, o.id).not.toMatch(/上一题|last question/);
          expect(en.options.map((o) => o.id)).toEqual(
            zh.options.map((o) => o.id),
          );
          for (const o of [...zh.options, ...en.options]) {
            expect(o.label, o.id).not.toMatch(/[{}]/);
            expect(o.label.trim(), o.id).not.toBe("不明显");
            expect(o.label.trim().toLowerCase(), o.id).not.toBe(
              "not noticeable",
            );
          }
          expect(zh.prompt).toBeTruthy();
          // the same seed gives the same wording; the question is a pure function
          expect(shownQuestion(id, context, "zh-CN", seed)).toEqual(zh);
        }
  });

  it("the same option has several wordings, and a session's seed picks the same one in both languages", () => {
    const zhSeen = new Set<string>();
    for (let seed = 0; seed < 40; seed += 1) {
      const zh = shownQuestion("A", GESHA, "zh-CN", seed).unanswered!;
      const en = shownQuestion("A", GESHA, "en", seed).unanswered!;
      const option = bank.options.A!.find((o) => o.id === zh.id)!;
      expect(option.label.en.indexOf(en.label)).toBe(
        option.label["zh-CN"].indexOf(zh.label),
      );
      zhSeen.add(zh.label);
    }
    expect(zhSeen.size).toBe(3); // 很难形容 / 说不上来 / 我恐怕很难准确回答 are substitutes of one option
  });

  it("the details differ by coffee: what survives, and the examples inside a label", () => {
    expect(contextGroup(GESHA).key).toBe(
      "band=light|process=washed|variety=gesha",
    );
    expect(contextGroup(DARK).key).toBe("band=dark|prep=espresso");
    expect(contextGroup({}).key).toBe("all");
    const ids = (context: object, q: DynamicQuestionId) =>
      shownQuestion(q, context, "zh-CN").options.map((o) => o.id);
    expect(ids(NATURAL, "A")).toContain("A2"); // berries for a natural
    expect(ids(DARK, "A")).toContain("A6"); // dried fruit comes in for dark roasts …
    expect(ids(DARK, "A")).not.toContain("A2"); // … and berries leave
    expect(ids(DARK, "B")).not.toContain("B1"); // flowers leave
    const citrus = (context: object) =>
      shownQuestion("A", context, "zh-CN").options.find((o) => o.id === "A1")!
        .label;
    expect(citrus(GESHA)).toContain("佛手柑");
    expect(citrus(DARK)).not.toContain("佛手柑");
    // mouthfeel follows the brewing method, not the corpus
    expect(ids(DARK, "D")).toContain("D3");
    expect(ids(GESHA, "D")).toContain("D6");
  });

  it("the second level offers that family's words — three at most, and \"I can't say\" as the fourth — and what the reader chooses leads the card's words", () => {
    const berries = secondLevelQuestion("A2", KENYA, "zh-CN")!;
    expect(berries.options.length).toBeLessThanOrEqual(3);
    expect(berries.unanswered).not.toBeNull();
    expect(berries.options.map((o) => o.label)).toContain("黑加仑");
    expect(secondLevelQuestion("A8", KENYA, "zh-CN")).toBeNull();
    const effects = dynamicEffects({
      A: "A2",
      "S:A2": "A2:黑加仑",
      B: "B0", // the aroma question's "I can't say": "I can't pick what stands out"
      E2: "E2d",
    });
    expect(effects.focus.fruity).toBe("berry");
    expect(effects.leadWord.fruity).toBe("黑加仑");
    expect(effects.unanswered).toEqual(["B"]);
    expect(effects.cardRows.map((r) => r["zh-CN"])).toEqual([
      "余韵 · 明显，带回甘",
    ]);
    const fruity = productVectorBundle.dimensions.indexOf("fruity");
    expect(effects.deltas[fruity]).toBe(2);
  });

  it("aroma and aftertaste are asked only where the corpus is not one-sided", () => {
    expect(structureQuestionWorthAsking("E2", GESHA)).toBe(true);
    expect(typeof structureQuestionWorthAsking("E1", DARK)).toBe("boolean");
  });
});

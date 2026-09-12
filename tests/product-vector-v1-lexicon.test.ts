/**
 * Semantic disambiguation test (owner, 2026-09-12): typical mainland-China consumer utterances must map
 * to the intended Q0–Q5 options through the hybrid mapper, with no conflicting answer on the same question.
 * Expected answers are the operator's reading of each sentence (owner review welcome).
 */
import { describe, expect, it } from "vitest";
import { mapUtterance, utteranceVector } from "../packages/flavor-data/src/product-vector-v1/lexicon";
import { DIMENSIONS } from "../packages/flavor-data/src/product-vector-v1";

type Case = { text: string; expect: Record<string, string>; note?: string };

const ZH: Case[] = [
  { text: "入口像柠檬一样酸，很亮", expect: { Q0: "A" } },
  { text: "酸得很柔和，有点像酸奶", expect: { Q0: "B" } },
  { text: "几乎不酸，很顺", expect: { Q0: "C" }, note: "negation forcing" },
  { text: "感觉像喝一杯带花香的清茶", expect: { Q1: "A", Q3: "A" } },
  { text: "闻起来像烤面包和榛果", expect: { Q1: "B" } },
  { text: "有热带水果和一点酒香", expect: { Q1: "C" } },
  { text: "回甘像蜂蜜和蔗糖", expect: { Q2: "A" } },
  { text: "很苦但是像黑巧克力一样甜", expect: { Q2: "B", Q4: "A" }, note: "bittersweet: dark chocolate sweetness + slight bitterness" },
  { text: "甜得像果酱", expect: { Q2: "C" } },
  { text: "口感很轻，像果汁", expect: { Q3: "A" } },
  { text: "顺滑像牛奶", expect: { Q3: "B" } },
  { text: "很厚重，像糖浆", expect: { Q3: "C" } },
  { text: "有一点苦，但回甘", expect: { Q4: "A" } },
  { text: "完全不苦", expect: { Q4: "B" }, note: "negation forcing" },
  { text: "层次很清楚，很干净", expect: { Q5: "A" } },
  { text: "味道混在一起，很浓郁", expect: { Q5: "B" } },
  { text: "桂花香很明显，酸质像青苹果", expect: { Q1: "A", Q0: "A" } },
  { text: "有米酒的发酵感，酸不刺激", expect: { Q0: "B" } },
  { text: "黑芝麻和烤杏仁的香气", expect: { Q1: "B" } },
  { text: "像荔枝和芒果，有点微醺", expect: { Q1: "C" } },
  { text: "冰糖雪梨那种清甜", expect: { Q2: "A" } },
  { text: "厌氧酒香很重，像朗姆酒", expect: { Q1: "C" } },
  { text: "茉莉花和佛手柑，很干净", expect: { Q1: "A", Q5: "A" } },
  { text: "焦糖和太妃糖的甜，尾段微苦", expect: { Q2: "B", Q4: "A" } },
  { text: "怕酸，喜欢丝绒一样顺滑的", expect: { Q0: "C", Q3: "B" }, note: "怕酸 → no-acid option" },
  { text: "不要苦，要非常浓郁的甜感", expect: { Q4: "B", Q5: "B" }, note: "owner Persona C fragment" },
  { text: "喜欢茉莉花香、柑橘酸，喝手冲，讨厌苦味", expect: { Q1: "A", Q0: "A", Q4: "B" }, note: "owner Persona A" },
  { text: "想要强烈的水蜜桃鲜明果酸", expect: { Q0: "A" }, note: "owner Persona B perception" },
  // owner copy review 2026-09-12: the exits — no sweetness, clearly bitter
  { text: "没什么甜味，尾段很苦", expect: { Q2: "D", Q4: "C" }, note: "absence of sweetness + clearly bitter" },
  { text: "不甜，有一点苦但回甘", expect: { Q2: "D", Q4: "A" }, note: "negation forcing on 甜" },
  { text: "太苦了，苦味盖过其他味道", expect: { Q4: "C" } },
];

const EN: Case[] = [
  { text: "bright lemon acidity, very lively", expect: { Q0: "A" } },
  { text: "smells like jasmine and green tea", expect: { Q1: "A" } },
  { text: "no bitterness at all, smooth like milk", expect: { Q4: "B", Q3: "B" } },
  { text: "caramel and dark chocolate sweetness, a little bitter", expect: { Q2: "B", Q4: "A" } },
  { text: "not sour, heavy and syrupy", expect: { Q0: "C", Q3: "C" } },
  { text: "no sweetness, very bitter", expect: { Q2: "D", Q4: "C" } },
];

function check(cases: Case[], locale: "zh-CN" | "en") {
  const failures: string[] = [];
  for (const c of cases) {
    const m = mapUtterance(c.text, locale);
    for (const [slot, option] of Object.entries(c.expect)) {
      const got = (m.answers as Record<string, string>)[slot];
      if (got !== option) failures.push(`${c.text} → ${slot}: expected ${option}, got ${got ?? "∅"} (scores ${JSON.stringify(m.scores[slot as keyof typeof m.scores]?.map((s) => `${s.option}:${s.score.toFixed(2)}`))})`);
    }
  }
  return failures;
}

describe("semantic disambiguation: consumer utterances → Q0-Q5 options", () => {
  it("negation guard: '不酸' and '不苦' never add acidity or bitterness", () => {
    const acid = mapUtterance("完全不酸，很顺", "zh-CN");
    expect(acid.vector[DIMENSIONS.indexOf("acidity")]).toBe(0);
    expect(acid.matched.some((t) => t.negated)).toBe(true);
    expect(acid.forced.Q0).toBe("C");
    expect(utteranceVector("清冽果酸", "zh-CN").vector[DIMENSIONS.indexOf("acidity")]).toBeGreaterThan(0);
    const bitter = mapUtterance("毫无苦味", "zh-CN");
    expect(bitter.forced.Q4).toBe("B");
    expect(bitter.answers.Q4).toBe("B");
  });

  it("zh-CN: every fixture maps to its intended options", () => {
    const failures = check(ZH, "zh-CN");
    expect(failures, failures.join("\n")).toEqual([]);
  });

  it("en: the same mapper works on English wording", () => {
    const failures = check(EN, "en");
    expect(failures, failures.join("\n")).toEqual([]);
  });

  it("never produces two answers for one question and reports its evidence", () => {
    for (const c of ZH) {
      const m = mapUtterance(c.text, "zh-CN");
      for (const [slot, rows] of Object.entries(m.scores)) {
        if ((m.answers as Record<string, string>)[slot]) expect(rows![0]!.option).toBe((m.answers as Record<string, string>)[slot]);
      }
      expect(m.matched.length).toBeGreaterThan(0);
    }
  });
});

/**
 * Q6 reachability (owner, 2026-09-12): the second round must open for a real share of sessions, never on Path 1
 * (coherent answers have nothing to resolve), and the front-of-house test set in docs/product/Q6_TRIGGER_TEST_SET.md
 * must keep opening it. Rates are measured by enumerating every answer combination of the bank.
 */
import { describe, expect, it } from "vitest";
import {
  describe as describeResult,
  escalationGate,
  flowStep,
  inferFromFlow,
} from "../packages/flavor-data/src/product-vector-v1/flow";
import type { FlowAnswers } from "../packages/flavor-data/src/product-vector-v1/flow";
import {
  answer,
  answerQ6,
  createSession,
  firstDescription,
  nextStep,
  submitPicks,
} from "../packages/flavor-data/src/product-vector-v1/session";
import { DIMENSIONS } from "../packages/flavor-data/src/product-vector-v1";

const OPTIONS: Record<string, string[]> = {
  Q0: ["A", "B", "C", "D"],
  Q1: ["A", "B", "C", "D"],
  Q2: ["A", "B", "C", "D"],
  Q3: ["A", "B", "C", "D"],
  Q4: ["A", "B", "C"],
  Q5: ["A", "B", "C", "D"],
};

type Ctx = Record<string, string | string[]>;

/** the five candidates that side with the reader's own answers (highest V_user weight) */
function userSide(
  result: ReturnType<typeof inferFromFlow>,
  description: ReturnType<typeof describeResult>,
) {
  return [...description.all]
    .sort(
      (a, b) =>
        (result.vUser[DIMENSIONS.indexOf(b.dimension as never)] ?? 0) -
        (result.vUser[DIMENSIONS.indexOf(a.dimension as never)] ?? 0),
    )
    .slice(0, 5);
}

function enumerate(context: Ctx) {
  const byPath: Record<number, { n: number; first: number; user: number }> = {};
  for (const q0 of OPTIONS.Q0!)
    for (const q1 of OPTIONS.Q1!)
      for (const q2 of OPTIONS.Q2!)
        for (const q3 of OPTIONS.Q3!)
          for (const q4 of OPTIONS.Q4!)
            for (const q5 of OPTIONS.Q5!) {
              const full: Record<string, string> = {
                Q0: q0,
                Q1: q1,
                Q2: q2,
                Q3: q3,
                Q4: q4,
                Q5: q5,
              };
              const answers: FlowAnswers = {};
              let step = flowStep(answers, context as never);
              let guard = 0;
              while (!step.deliver && guard < 10) {
                for (const slot of step.ask)
                  (answers as Record<string, string>)[slot] = full[slot]!;
                step = flowStep(answers, context as never);
                guard += 1;
              }
              const result = inferFromFlow(context as never, answers);
              const description = describeResult(result, "zh-CN");
              const bucket = (byPath[step.path ?? 0] ??= {
                n: 0,
                first: 0,
                user: 0,
              });
              bucket.n += 1;
              if (
                escalationGate(step, result, description.all.slice(0, 5))
                  .escalate
              )
                bucket.first += 1;
              if (
                escalationGate(step, result, userSide(result, description))
                  .escalate
              )
                bucket.user += 1;
            }
  const total = Object.values(byPath).reduce(
    (acc, b) => ({
      n: acc.n + b.n,
      first: acc.first + b.first,
      user: acc.user + b.user,
    }),
    { n: 0, first: 0, user: 0 },
  );
  return { byPath, total };
}

describe("Q6 trigger rate (all 3,072 answer combinations per context)", () => {
  it.each([
    {
      name: "dark espresso, natural bourbon",
      context: {
        c0_preparation: "espresso",
        c1_roast: "dark",
        c2_variety: "bourbon",
        c2_process: "natural",
      },
    },
    {
      name: "light pour-over, washed",
      context: {
        c0_preparation: "pour_over_v60",
        c1_roast: "light",
        c2_process: "washed",
      },
    },
  ])(
    "$name: Path 1 never opens Q6; ≥20% of sequences do with the first five words, ≥45% when the picks side with the reader",
    ({ context }) => {
      const { byPath, total } = enumerate(context);
      expect(total.n).toBe(3072);
      expect(byPath[1]!.n).toBeGreaterThan(0);
      expect(byPath[1]!.first).toBe(0);
      expect(byPath[1]!.user).toBe(0);
      expect(total.first / total.n).toBeGreaterThanOrEqual(0.2);
      expect(total.user / total.n).toBeGreaterThanOrEqual(0.45);
      // every conflict path stays reachable for Q6
      for (const path of [2, 3, 4])
        expect(byPath[path]!.user / byPath[path]!.n).toBeGreaterThanOrEqual(
          0.25,
        );
    },
    60_000,
  );
});

/** the sequences handed to the owner for the front-of-house check (docs/product/Q6_TRIGGER_TEST_SET.md) */
const RECIPES: Array<{
  name: string;
  context: Ctx;
  answers: Record<string, string>;
  tap: string[];
}> = [
  {
    name: "1 深烘 意式 · 日晒 波本",
    context: {
      c0_preparation: "espresso",
      c1_roast: "dark",
      c2_variety: "bourbon",
      c2_process: "natural",
    },
    answers: { Q0: "A", Q1: "A", Q2: "A", Q3: "A", Q4: "B", Q5: "A" },
    tap: ["茉莉花", "蔗糖", "葡萄柚", "水蜜桃", "丝绒奶油"],
  },
  {
    name: "2 深烘 意式 · 日晒 波本 (Path 3)",
    context: {
      c0_preparation: "espresso",
      c1_roast: "dark",
      c2_variety: "bourbon",
      c2_process: "natural",
    },
    answers: { Q0: "B", Q1: "B", Q2: "A", Q3: "A", Q4: "A", Q5: "A" },
    tap: ["烤榛果", "朗姆酒", "蔗糖", "丝绒奶油", "葡萄柚"],
  },
  {
    name: "3 浅烘 手冲 · 水洗 瑰夏 · 埃塞俄比亚",
    context: {
      c0_preparation: "pour_over_v60",
      c1_roast: "light",
      c2_process: "washed",
      c2_variety: "gesha",
      origin: ["ethiopia"],
    },
    answers: { Q0: "A", Q1: "C", Q2: "A", Q3: "C", Q4: "C", Q5: "D" },
    tap: ["水蜜桃", "丝绒奶油", "黑巧克力", "葡萄柚", "蔗糖"],
  },
  {
    name: "4 中烘 法压",
    context: { c0_preparation: "french_press", c1_roast: "medium" },
    answers: { Q0: "B", Q1: "C", Q2: "A", Q3: "B", Q4: "C", Q5: "A" },
    tap: ["朗姆酒", "水蜜桃", "丝绒奶油", "蔗糖", "黑巧克力"],
  },
  {
    name: "5 中浅烘 冷萃 · 日晒",
    context: {
      c0_preparation: "cold_brew",
      c1_roast: "medium_light",
      c2_process: "natural",
    },
    answers: { Q0: "B", Q1: "C", Q2: "B", Q3: "A", Q4: "A", Q5: "C" },
    tap: ["朗姆酒", "水蜜桃", "烤榛果", "葡萄柚", "黑巧克力"],
  },
  {
    name: "6 中深烘 摩卡壶 · 水洗 铁皮卡 · 巴西",
    context: {
      c0_preparation: "moka_pot",
      c1_roast: "medium_dark",
      c2_process: "washed",
      c2_variety: "typica",
      origin: ["brazil"],
    },
    answers: { Q0: "B", Q1: "C", Q2: "B", Q3: "B", Q4: "C", Q5: "C" },
    tap: ["朗姆酒", "黑巧克力", "水蜜桃", "烤榛果", "葡萄柚"],
  },
  {
    name: "7 浅烘 爱乐压 · 厌氧 (Path 3)",
    context: {
      c0_preparation: "aeropress",
      c1_roast: "light",
      c2_process: "anaerobic",
    },
    answers: { Q0: "A", Q1: "A", Q2: "B", Q3: "A", Q4: "B", Q5: "A" },
    tap: ["茉莉花", "葡萄柚", "烤榛果", "水蜜桃", "丝绒奶油"],
  },
];

function play(context: Ctx, answers: Record<string, string>) {
  let s = createSession(context as never, "zh-CN");
  let guard = 0;
  while (s.stage === "questions" && guard < 10) {
    const step = nextStep(s);
    if (step.kind !== "ask") break;
    expect(
      step.card.options.some((o) => o.option === answers[step.card.slot]),
    ).toBe(true);
    s = answer(s, step.card.slot, answers[step.card.slot]!);
    guard += 1;
  }
  return firstDescription(s);
}

describe("Q6 front-of-house test set", () => {
  it.each(RECIPES)(
    "$name opens Q6 with the listed taps and lands on a confirmed card",
    ({ context, answers, tap }) => {
      const s = play(context, answers);
      expect(s.stage).toBe("picks");
      const shown = s.description!.all.map((w) => w.text);
      for (const word of tap) expect(shown).toContain(word);
      const picks = tap.map(
        (t) => s.description!.all.find((w) => w.text === t)!,
      );
      const gated = submitPicks(s, picks);
      expect(gated.stage).toBe("q6");
      expect(gated.q6!.options).toHaveLength(8);
      const done = answerQ6(
        gated,
        gated.q6!.options.slice(0, 2).map((o) => o.dimension),
      );
      expect(done.stage).toBe("final");
      expect(done.q6!.selected).toHaveLength(2);
      expect(done.card).not.toBeNull();
      expect(done.description!.all.map((w) => w.text)).not.toEqual(shown); // the second description moved
    },
  );

  it("control: coherent light pour-over answers stay on Path 1 and go straight to the final card", () => {
    const s = play(
      {
        c0_preparation: "pour_over_v60",
        c1_roast: "light",
        c2_process: "washed",
        c2_variety: "gesha",
        origin: ["ethiopia"],
      },
      { Q0: "A", Q1: "A", Q2: "A", Q3: "A", Q4: "B" },
    );
    expect(s.step.path).toBe(1);
    expect(s.stage).toBe("picks");
    const done = submitPicks(s, userSide(s.result!, s.description!));
    expect(done.stage).toBe("final");
    expect(done.q6).toBeNull();
  });
});

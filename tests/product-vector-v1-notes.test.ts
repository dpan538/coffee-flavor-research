/**
 * The card's notes, "关于这段描述" (owner, 2026-09-18): the reference is interpreted against all review records
 * instead of repeating the reader's choices, the statistics bear on the confirmed words and may differ between visits,
 * the description note says what the answers moved — and a card says the same thing in both languages.
 */
import { describe, expect, it } from "vitest";
import { productVectorBundle } from "../packages/flavor-data/src/product-vector-v1";
import {
  answer,
  answerQ6,
  createSession,
  firstDescription,
  nextStep,
  relocalize,
  submitPicks,
} from "../packages/flavor-data/src/product-vector-v1/session";
import type { Session } from "../packages/flavor-data/src/product-vector-v1/session";
import type { Slot } from "../packages/flavor-data/src/product-vector-v1/flow";

type Ctx = Record<string, string>;
const CONTEXTS: Ctx[] = [
  {
    c0_preparation: "pour_over_v60",
    c1_roast: "light",
    c2_variety: "gesha",
    c2_process: "washed",
    c2_origin: "ethiopia",
  },
  {
    c0_preparation: "moka_pot",
    c1_roast: "medium_dark",
    c2_variety: "typica",
    c2_process: "washed",
    c2_origin: "brazil",
  },
  {
    c0_preparation: "espresso",
    c1_roast: "dark",
    c2_variety: "bourbon",
    c2_process: "natural",
  },
  {
    c0_preparation: "french_press",
    c1_roast: "medium_light",
    c2_variety: "caturra",
    c2_process: "washed",
  },
  {
    c0_preparation: "cold_brew",
    c1_roast: "medium",
    c2_variety: "robusta",
    c2_process: "honey",
  },
  {
    c0_preparation: "milk_coffee",
    c1_roast: "very_dark",
    c2_variety: "castillo",
    c2_process: "anaerobic",
  },
];
const ANSWERS: Array<Record<string, string>> = [
  { Q0: "A", Q1: "A", Q2: "A", Q3: "A", Q4: "B", Q5: "A" },
  { Q0: "B", Q1: "C", Q2: "B", Q3: "B", Q4: "C", Q5: "C" },
  { Q0: "C", Q1: "B", Q2: "B", Q3: "C", Q4: "A", Q5: "B" },
  { Q0: "D", Q1: "D", Q2: "D", Q3: "D", Q4: "C", Q5: "D" },
  { Q0: "A", Q1: "C", Q2: "C", Q3: "A", Q4: "B", Q5: "C" },
];

function finished(
  context: Ctx,
  answers: Record<string, string>,
  locale: "zh-CN" | "en",
  nonce: number,
  pickFrom = 0,
): Session {
  let s = createSession(context as never, locale, [], nonce);
  let guard = 0;
  while (s.stage === "questions" && guard < 10) {
    const step = nextStep(s);
    if (step.kind !== "ask") break;
    s = answer(s, step.card.slot as Slot, answers[step.card.slot]!);
    guard += 1;
  }
  s = firstDescription(s);
  s = submitPicks(s, s.description!.all.slice(pickFrom, pickFrom + 5));
  if (s.stage === "q6") s = answerQ6(s, [s.q6!.options[0]!.dimension]);
  expect(s.stage).toBe("final");
  return s;
}
// the numbers a note carries, as a multiset: "每 10 款约 5 款" and "about 5 in 10" say the same thing in another order
const numbers = (text: string) =>
  (text.match(/\d(?:[\d,]*\d)?/g) ?? []).sort().join(" ");

describe("card notes", () => {
  it("every template has the same variants, in the same order and with the same placeholders, in both languages", () => {
    const notes = (
      productVectorBundle.presentation as unknown as {
        card_notes: Record<"zh-CN" | "en", Record<string, string | string[]>>;
      }
    ).card_notes;
    expect(Object.keys(notes.en)).toEqual(Object.keys(notes["zh-CN"]));
    // the same information in both languages: a slot may be said twice in one language and once in the other
    const slots = (t: string) =>
      [...new Set([...t.matchAll(/\{(\w+)\}/g)].map((m) => m[1]))].sort();
    for (const [key, zh] of Object.entries(notes["zh-CN"])) {
      const zhList = Array.isArray(zh) ? zh : [zh];
      const enList = ([] as string[]).concat(notes.en[key]!);
      expect(enList, key).toHaveLength(zhList.length);
      zhList.forEach((template, i) =>
        expect(slots(enList[i]!), `${key}[${i}]`).toEqual(slots(template)),
      );
    }
  });

  it("a card says the same thing in both languages: same notes, same scopes, same numbers — also after switching language", () => {
    let cards = 0;
    for (const context of CONTEXTS)
      for (const answers of ANSWERS)
        for (const nonce of [0, 1, 17, 1789634997952])
          for (const pickFrom of [0, 3]) {
            const zh = finished(context, answers, "zh-CN", nonce, pickFrom);
            const en = finished(context, answers, "en", nonce, pickFrom);
            const switched = relocalize(zh, "en");
            for (const other of [en, switched]) {
              expect(
                other.card!.science.map((l) => `${l.evidenceState}|${l.about}`),
              ).toEqual(
                zh.card!.science.map((l) => `${l.evidenceState}|${l.about}`),
              );
              expect(other.card!.science.map((l) => numbers(l.text))).toEqual(
                zh.card!.science.map((l) => numbers(l.text)),
              );
            }
            for (const session of [zh, en]) {
              const science = session.card!.science;
              expect(science.length).toBeGreaterThanOrEqual(2);
              expect(science.length).toBeLessThanOrEqual(5);
              expect(science[0]!.evidenceState).toBe("REFERENCE_BASIS");
              expect(
                science.filter((l) => l.evidenceState === "COMPUTED_DELTA"),
              ).toHaveLength(1);
              // one note from the data, never two under the same label (owner, 2026-09-19)
              expect(
                science.filter((l) => l.evidenceState === "CORPUS_MEASURED")
                  .length,
              ).toBeLessThanOrEqual(1);
              // shares are said as frequencies against "all coffees": no percentage, no undefined "overall"
              for (const l of science.filter((x) =>
                ["CORPUS_MEASURED", "REFERENCE_BASIS"].includes(
                  x.evidenceState,
                ),
              ))
                expect(l.text, l.about).not.toMatch(/%|整体|overall/);
              for (const l of science) {
                expect(l.text, l.about).not.toMatch(/[{}]/); // no unfilled placeholder
                expect(l.label).toBeTruthy();
              }
            }
            // the exported card's sentence is about the cup, never addressed to the reader (owner, 2026-09-19)
            expect(zh.card!.cardNote).toBeTruthy();
            expect(zh.card!.cardNote).not.toMatch(/你|您/);
            expect(en.card!.cardNote).not.toMatch(/\byou(r)?\b/i);
            expect(switched.card!.cardNote).toBe(en.card!.cardNote);
            // the mechanical sentence is gone, and the reference no longer lists the reader's own choices back
            expect(zh.card!.science.map((l) => l.text).join("")).not.toContain(
              "只是起点",
            );
            for (const l of en.card!.science)
              expect(l.text.charAt(0)).toMatch(/[A-Z0-9“"]/);
            cards += 1;
          }
    expect(cards).toBe(CONTEXTS.length * ANSWERS.length * 4 * 2);
  }, 120_000);

  it("the notes read the review records in plain words and show no figures", () => {
    const stats = productVectorBundle.corpus_stats as unknown as {
      all: { n: number; presence: number[] };
      options: Record<
        string,
        Record<string, { n: number; presence: number[] }>
      >;
    };
    const floral = productVectorBundle.dimensions.indexOf("floral");
    const gesha = stats.options.C2_variety!.gesha!;
    const s = finished(CONTEXTS[0]!, ANSWERS[0]!, "zh-CN", 0);
    // the reference says the direction in plain words and carries no figures
    const reference = s.card!.science[0]!.text;
    expect(reference).toContain("瑰夏");
    expect(reference).toMatch(/更常写到花香/);
    expect(reference).not.toMatch(/\d/);
    // the one data note compares this kind of coffee with coffee generally — and gives no figures (owner, 2026-09-20:
    // "of the 738 coffees about 4 in 10 … against 3" reads as heavy averaging and invites the suspicion of over-fitting)
    const data = s.card!.science.find(
      (l) => l.evidenceState === "CORPUS_MEASURED",
    )!;
    const [, scopeKey, dimension] = data.about.match(
      /^corpus_support:(.+):(\w+)$/,
    )!;
    const pairs = (
      productVectorBundle.corpus_stats as unknown as {
        pairs: Array<{
          a: [string, string];
          b: [string, string];
          n: number;
          presence: number[];
        }>;
      }
    ).pairs;
    const scope = scopeKey!.includes("+")
      ? pairs.find((x) => `${x.a.join(":")}+${x.b.join(":")}` === scopeKey)!
      : stats.options[scopeKey!.split(":")[0]!]![scopeKey!.split(":")[1]!]!;
    const d = productVectorBundle.dimensions.indexOf(dimension!);
    expect(gesha.n).toBeGreaterThan(0);
    expect(floral).toBeGreaterThanOrEqual(0);
    expect(data.text).not.toMatch(/\d/);
    // "more often" / "less often" stand on a gap of at least ten points; anything closer reads "about the same"
    const gap = scope.presence[d]! - stats.all.presence[d]!;
    expect(data.text).toMatch(
      gap >= 0.1 ? /更常/ : gap <= -0.1 ? /更少|少见/ : /差不多/,
    );
    expect(scope.n).toBeGreaterThan(0);
    // a method with no review records is named as left out instead of being listed as if it counted
    const moka = finished(CONTEXTS[1]!, ANSWERS[1]!, "zh-CN", 0).card!
      .science[0]!.text;
    expect(moka).toContain("摩卡壶");
    expect(moka).toMatch(/没有足够的评审记录|记录太少|缺少评审记录/);
  });

  it("the supporting statistics bear on the confirmed words and may differ between visits, never within one", () => {
    const seen = new Set<string>();
    for (let nonce = 1; nonce <= 12; nonce += 1) {
      const s = finished(CONTEXTS[0]!, ANSWERS[0]!, "zh-CN", nonce);
      const data = s.card!.science.filter(
        (l) => l.evidenceState === "CORPUS_MEASURED",
      );
      expect(data).toHaveLength(1);
      const picked = new Set(s.picks.map((w) => w.dimension));
      for (const l of data)
        expect(picked.has(l.about.split(":").pop()!)).toBe(true);
      seen.add(data.map((l) => l.text).join(" + "));
      const again = finished(CONTEXTS[0]!, ANSWERS[0]!, "zh-CN", nonce);
      expect(again.card!.science.map((l) => l.text)).toEqual(
        s.card!.science.map((l) => l.text),
      );
    }
    expect(seen.size).toBeGreaterThan(1);
  });

  it("the description note names what the answers moved and which words on the card come from it", () => {
    const s = finished(CONTEXTS[1]!, ANSWERS[1]!, "zh-CN", 0);
    const note = s.card!.science.find(
      (l) => l.evidenceState === "COMPUTED_DELTA",
    )!;
    expect(note.text).toContain("初始参考");
    const shown = [...s.card!.picked, ...s.card!.evaluation.map((e) => e.text)];
    expect(shown.some((word) => note.text.includes(word))).toBe(true);
  });
});

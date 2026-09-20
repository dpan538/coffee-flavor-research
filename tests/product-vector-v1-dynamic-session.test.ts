/**
 * The dynamic question bank behind the session API (R3-D40): four core questions, then two follow-ups at most; five
 * options at most per question; what the reader chooses at the second level leads the card's words; aroma, aftertaste
 * and bitterness answers become evaluation rows; editing an earlier answer replays to exactly the session a fresh
 * reader with the same final answers would get; both languages ask the same questions with the same option ids.
 */
import { describe, expect, it } from "vitest";
import {
  answer,
  answerAndReplay,
  answerQ6,
  createSession,
  firstDescription,
  nextStep,
  relocalize,
  reopenQuestion,
  submitPicks,
  type Session,
} from "../packages/flavor-data/src/product-vector-v1/session";

const CONTEXTS = [
  {
    c0_preparation: "pour_over_v60",
    c1_roast: "light",
    c2_process: "washed",
    c2_variety: "gesha",
  },
  { c0_preparation: "espresso", c1_roast: "dark", c2_process: "natural" },
  { c0_preparation: "french_press", c1_roast: "medium" },
];

type Chooser = (key: string, options: string[], unanswered?: string) => string;
function walk(
  context: object,
  choose: Chooser,
  locale: "zh-CN" | "en" = "zh-CN",
  nonce = 0,
) {
  let s = createSession(context, locale, [], nonce, "dynamic");
  const asked: Array<{ key: string; options: string[]; prompt: string }> = [];
  for (let guard = 0; s.stage === "questions" && guard < 10; guard += 1) {
    const step = nextStep(s);
    if (step.kind !== "ask") break;
    const options = step.card.options.map((o) => o.option);
    asked.push({ key: step.card.slot, options, prompt: step.card.prompt });
    s = answer(
      s,
      step.card.slot,
      choose(step.card.slot, options, step.card.unanswered?.option),
    );
  }
  return { session: s, asked };
}
function finish(s: Session): Session {
  let out = firstDescription(s);
  out = submitPicks(out, out.description!.all.slice(0, 5));
  if (out.stage === "q6") out = answerQ6(out, [out.q6!.options[0]!.dimension]);
  return out;
}

describe("dynamic session", () => {
  it("asks the four core questions, then two follow-ups at most; five options at most; always reaches a card", () => {
    let walks = 0;
    const counts = new Set<number>();
    for (const context of CONTEXTS)
      for (let a = 0; a < 6; a += 1)
        for (let b = 0; b < 6; b += 1)
          for (let c = 0; c < 6; c += 1)
            for (const d of [0, 3])
              for (const f of [0, 4]) {
                const pick = [a, b, c, d];
                const { session, asked } = walk(
                  context,
                  (key, options, unanswered) => {
                    const core = ["Q0", "Q1", "Q2", "Q3"].indexOf(key);
                    const i = core >= 0 ? pick[core]! : f;
                    return i >= options.length
                      ? (unanswered ?? options[options.length - 1]!)
                      : options[i]!;
                  },
                );
                expect(asked.slice(0, 4).map((q) => q.key)).toEqual([
                  "Q0",
                  "Q1",
                  "Q2",
                  "Q3",
                ]);
                expect(asked.length).toBeLessThanOrEqual(6);
                expect(asked.length).toBeGreaterThanOrEqual(5);
                for (const q of asked) {
                  expect(q.options.length, q.key).toBeLessThanOrEqual(5);
                  expect(q.options.length, q.key).toBeGreaterThanOrEqual(2);
                  expect(q.prompt, q.key).toBeTruthy();
                  expect(q.prompt, q.key).not.toMatch(/[{}]/);
                }
                expect(session.stage).toBe("describe");
                const done = finish(session);
                expect(done.stage).toBe("final");
                expect(done.description!.all).toHaveLength(8);
                expect(done.card!.picked).toHaveLength(5);
                expect(done.card!.evaluation.length).toBeLessThanOrEqual(4);
                counts.add(asked.length);
                walks += 1;
              }
    expect(walks).toBe(CONTEXTS.length * 6 * 6 * 6 * 2 * 2);
    expect([...counts].sort()).toEqual([5, 6]); // five when the reader could not answer two of the core questions
  }, 240_000);

  it("the confirmation step keeps its floors: never on the coherent path, almost never for the first five words, often for a reader's own picks", () => {
    const DIMS = [
      "acidity",
      "sweetness",
      "body",
      "floral",
      "fruity",
      "nutty_chocolate",
      "fermented_winey",
      "bitter_roasted",
      "spice",
      "herbal_green",
      "woody_earthy",
      "defect",
    ];
    const byPath: Record<number, [number, number, number]> = {};
    let total = 0;
    let firstFive = 0;
    let readerSide = 0;
    const visit = (s: Session, depth: number) => {
      if (s.stage === "questions") {
        const step = nextStep(s);
        if (step.kind === "ask") {
          // everything a reader can tap: the options and, where there is one, "I can't say" (the fifth of them)
          const options = [
            ...step.card.options.map((o) => o.option),
            ...(step.card.unanswered ? [step.card.unanswered.option] : []),
          ];
          const chosen =
            depth < 4
              ? options
              : [...new Set([options[0]!, options[options.length - 1]!])];
          for (const o of chosen)
            visit(answer(s, step.card.slot, o), depth + 1);
          return;
        }
      }
      const described = firstDescription(s);
      const all = described.description!.all;
      const own = [...all]
        .sort(
          (x, y) =>
            (described.result!.vUser[DIMS.indexOf(y.dimension)] ?? 0) -
            (described.result!.vUser[DIMS.indexOf(x.dimension)] ?? 0),
        )
        .slice(0, 5);
      const row = (byPath[s.step.path!] ??= [0, 0, 0]);
      row[0] += 1;
      total += 1;
      if (submitPicks(described, all.slice(0, 5)).stage === "q6") {
        row[1] += 1;
        firstFive += 1;
      }
      if (submitPicks(described, own).stage === "q6") {
        row[2] += 1;
        readerSide += 1;
      }
    };
    for (const context of [CONTEXTS[0]!, CONTEXTS[1]!])
      visit(createSession(context, "zh-CN", [], 0, "dynamic"), 0);
    // five things to tap in the first two questions, four in the next two; two follow-ups with two answers each (one
    // follow-up for a reader who could not answer two core questions)
    expect(total).toBeGreaterThan(2 * 1000);
    expect(total).toBeLessThanOrEqual(2 * 5 * 5 * 4 * 4 * 2 * 2);
    // the first five words span the card's dimensions, so they almost never lean the reader's way
    expect(firstFive / total).toBeLessThan(0.01);
    expect(firstFive).toBeLessThanOrEqual(readerSide);
    expect(byPath[1]![1] + byPath[1]![2]).toBe(0);
    expect(readerSide / total).toBeGreaterThanOrEqual(0.45);
    for (const path of [2, 3, 4])
      if (byPath[path])
        expect(
          byPath[path]![2] / byPath[path]![0],
          `path ${path}`,
        ).toBeGreaterThanOrEqual(0.25);
  }, 240_000);

  it("the prompt follows the previous answer, and a second level names its family", () => {
    const { asked } = walk(CONTEXTS[0]!, (key, options) =>
      key === "Q0" ? "A1" : options[0]!,
    );
    expect(asked[1]!.prompt).toBe("柑橘那种酸之后，闻起来、喝起来最像哪一类？");
    const second = asked.find((q) => q.key === "S:A1");
    expect(second?.prompt).toBe("柑橘里，更像哪一个？");
    expect(second!.options.length).toBeLessThanOrEqual(5);
  });

  it("the word chosen at the second level leads that dimension's words on the card", () => {
    // a natural light roast: berries survive the pruning of the fruit question there
    const natural = {
      c0_preparation: "pour_over_v60",
      c1_roast: "light",
      c2_process: "natural",
    };
    let chosenWord = "";
    const { session, asked } = walk(natural, (key, options) => {
      if (key === "Q0") return "A2";
      if (key === "S:A2") {
        chosenWord = options[options.length - 1]!.split(":")[1]!;
        return options[options.length - 1]!;
      }
      return options[0]!;
    });
    expect(asked.map((q) => q.key)).toContain("S:A2");
    const described = firstDescription(session);
    const fruit = described.description!.all.filter(
      (w) => w.dimension === "fruity",
    );
    expect(chosenWord).toBeTruthy();
    expect(fruit[0]?.text).toBe(chosenWord);
    // a first-level answer alone already points the words at its sub-family (the soft constraint of R3-D42)
    const berries = new Set([
      "黑加仑",
      "蔓越莓",
      "蓝莓",
      "草莓",
      "树莓",
      "黑莓",
      "石榴",
    ]);
    for (const w of fruit) expect(berries.has(w.text), w.text).toBe(true);
  });

  it("aroma, aftertaste and bitterness answers become evaluation rows; 'no bitterness' removes the derived row", () => {
    const seen = new Set<string>();
    for (let nonce = 0; nonce < 6; nonce += 1) {
      const { session, asked } = walk(
        CONTEXTS[1]!,
        (key, options) =>
          key === "Q4"
            ? "E3d"
            : key === "E2"
              ? "E2d"
              : key === "E1"
                ? "E1b"
                : options[0]!,
        "zh-CN",
        nonce,
      );
      asked.forEach((q) => seen.add(q.key.split(":")[0]!));
      const card = finish(session).card!;
      if (session.answers.Q4)
        expect(
          card.evaluation.find((r) => r.dimension === "bitter_roasted")?.text,
        ).toBe("烟熏可可");
      if (session.answers.E2)
        expect(
          card.evaluation.find((r) => r.dimension === "aftertaste")?.text,
        ).toBe("明显，带回甘");
    }
    expect(seen.has("Q4")).toBe(true); // a dark roast is asked about bitterness first
    const none = walk(CONTEXTS[1]!, (key, options) =>
      key === "Q4" ? "E3a" : options[0]!,
    );
    const card = finish(none.session).card!;
    expect(card.evaluation.some((r) => r.dimension === "bitter_roasted")).toBe(
      false,
    );
  });

  it("a clear aftertaste is read against coffees of the same roast — in the place of the single data note, the same in both languages", () => {
    let structureNotes = 0;
    for (let nonce = 0; nonce < 24; nonce += 1) {
      const choose: Chooser = (key, options) =>
        key === "E2" ? "E2c" : key === "E1" ? "E1b" : options[0]!;
      const zh = walk(CONTEXTS[0]!, choose, "zh-CN", nonce);
      if (!zh.session.answers.E2) continue;
      const zhCard = finish(zh.session).card!;
      const enCard = finish(
        walk(CONTEXTS[0]!, choose, "en", nonce).session,
      ).card!;
      const data = zhCard.science.filter(
        (l) => l.evidenceState === "CORPUS_MEASURED",
      );
      expect(data.length).toBeLessThanOrEqual(1);
      const note = data.find((l) => l.about.startsWith("corpus_structure:"));
      if (!note) continue;
      structureNotes += 1;
      expect(note.text).toContain("瑰夏");
      expect(note.text).toContain("余韵");
      expect(note.text).toContain("同样烘焙度");
      expect(note.text).not.toMatch(/[{}%]/);
      const en = enCard.science.find((l) => l.about === note.about)!;
      const digits = (t: string) => (t.match(/\d+/g) ?? []).sort().join(" ");
      expect(digits(en.text)).toBe(digits(note.text));
      expect(en.text).toContain("Gesha");
    }
    expect(structureNotes).toBeGreaterThan(0);
  });

  it("a reader who cannot answer anything still gets a card", () => {
    const { session, asked } = walk(
      CONTEXTS[2]!,
      (_key, options, unanswered) => unanswered ?? options[0]!,
    );
    expect(asked.length).toBe(5); // no second follow-up for a reader who cannot describe the cup
    expect(finish(session).stage).toBe("final");
  });

  it("both languages ask the same questions with the same option ids, and switching language keeps the card", () => {
    for (const context of CONTEXTS)
      for (const nonce of [0, 3]) {
        const choose: Chooser = (_key, options) => options[1] ?? options[0]!;
        const zh = walk(context, choose, "zh-CN", nonce);
        const en = walk(context, choose, "en", nonce);
        expect(en.asked.map((q) => [q.key, q.options])).toEqual(
          zh.asked.map((q) => [q.key, q.options]),
        );
        for (const q of en.asked) expect(q.prompt).not.toMatch(/[一-鿿]/);
        const done = finish(zh.session);
        const switched = relocalize(done, "en");
        expect(switched.card!.picked).toHaveLength(5);
        expect(switched.card!.picked.join("")).not.toMatch(/[一-鿿]/);
        expect(switched.card!.evaluation.map((r) => r.dimension)).toEqual(
          done.card!.evaluation.map((r) => r.dimension),
        );
      }
  });

  it("editing an earlier answer replays to the session a fresh reader with the same final answers would get", () => {
    let edits = 0;
    for (const context of CONTEXTS)
      for (const seed of [0, 1, 2, 3, 4, 5]) {
        const choose: Chooser = (key, options) =>
          options[(seed + key.length) % options.length]!;
        const original = walk(context, choose, "zh-CN", seed);
        for (const target of original.asked.slice(0, -1))
          for (const alternative of target.options) {
            if (alternative === original.session.answers[target.key]) continue;
            // edit: reopen the question, answer it differently, replay what was kept, then answer what is newly asked
            const reopened = reopenQuestion(original.session, target.key);
            const replay = answerAndReplay(
              reopened.session,
              target.key,
              alternative,
              reopened.kept,
            );
            // the progress row: answered questions, the one on screen, the kept answers after it — never more than the
            // six questions a cup is asked (the owner saw eight bars: answers kept for follow-ups the new path never asks)
            for (const state of [reopened, replay]) {
              const onScreen = state.session.stage === "questions" ? 1 : 0;
              const keptAfter = Object.keys(state.kept).filter(
                (slot) =>
                  !(slot in state.session.answers) &&
                  slot !== state.session.step.ask[0],
              ).length;
              const bars =
                Object.keys(state.session.answers).length +
                onScreen +
                keptAfter;
              expect(
                bars,
                `${target.key} → ${alternative}`,
              ).toBeLessThanOrEqual(6);
              if (state.session.step.plannedKeys)
                for (const slot of Object.keys(state.kept))
                  expect(state.session.step.plannedKeys).toContain(slot);
            }
            let edited = replay.session;
            for (
              let guard = 0;
              edited.stage === "questions" && guard < 10;
              guard += 1
            ) {
              const step = nextStep(edited);
              if (step.kind !== "ask") break;
              edited = answer(
                edited,
                step.card.slot,
                step.card.options[0]!.option,
              );
            }
            // fresh: a new session given the same final answers, in the order asked
            let fresh = createSession(context, "zh-CN", [], seed, "dynamic");
            for (
              let guard = 0;
              fresh.stage === "questions" && guard < 10;
              guard += 1
            ) {
              const step = nextStep(fresh);
              if (step.kind !== "ask") break;
              fresh = answer(
                fresh,
                step.card.slot,
                edited.answers[step.card.slot]!,
              );
            }
            expect(edited.stage).toBe("describe");
            expect(fresh.answers).toEqual(edited.answers);
            expect(fresh.step).toEqual(edited.step);
            expect(firstDescription(fresh).description).toEqual(
              firstDescription(edited).description,
            );
            edits += 1;
          }
      }
    expect(edits).toBeGreaterThan(200);
  }, 240_000);
});

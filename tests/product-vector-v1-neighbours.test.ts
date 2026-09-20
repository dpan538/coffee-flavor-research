/**
 * The neighbour fill (owner, 2026-09-20, R3-D47): in a dimension the reader gave no signal for, a word that is
 * DISTINCTIVE of coffees like this one leads instead of coming and going with the rotation. The owner's rule is the
 * contract here: it steadies what is evident for the cup, it never reinforces what is strong on every cup; the reader's
 * own answer always wins; the six fixed questions keep their rotation bit for bit.
 */
import { describe as suite, expect, it } from "vitest";
import index from "../db/data/product-vector-v1/product-vector-v1-neighbours.json" with { type: "json" };
import { productVectorBundle } from "../packages/flavor-data/src/product-vector-v1";
import {
  shownQuestion,
  wordHints,
} from "../packages/flavor-data/src/product-vector-v1/dynamicBank";
import {
  describe,
  inferFromFlow,
  picksToVector,
  q6Word,
} from "../packages/flavor-data/src/product-vector-v1/flow";
import { neighbourWordScores } from "../packages/flavor-data/src/product-vector-v1/neighbours";
import {
  answer,
  answerQ6,
  createSession,
  firstDescription,
  nextStep,
  relocalize,
  submitPicks,
  type Session,
} from "../packages/flavor-data/src/product-vector-v1/session";

const presentation = productVectorBundle.presentation as unknown as {
  dimension_tags: Record<string, Record<"zh-CN" | "en", string[]>>;
  dimension_roles: Record<string, string>;
};
const CONTEXTS = [
  { c0_preparation: "pour_over_v60", c1_roast: "light", c2_process: "washed" },
  {
    c0_preparation: "pour_over_v60",
    c1_roast: "light",
    c2_process: "natural",
    c2_variety: "gesha",
  },
  { c0_preparation: "french_press", c1_roast: "medium" },
  { c0_preparation: "espresso", c1_roast: "dark" },
];

/** Dynamic walks of a context — all options of the four core questions, the first option of each follow-up — thinned
 *  to every `stride`-th walk: the properties below hold per card, a sample of a few hundred cards is enough. */
function* walks(
  context: (typeof CONTEXTS)[number],
  stride = 9,
): Generator<Session> {
  let n = 0;
  for (const session of everyWalk(context))
    if (n++ % stride === 0) yield session;
}

function* everyWalk(context: (typeof CONTEXTS)[number]): Generator<Session> {
  function* from(session: Session, depth: number): Generator<Session> {
    const step = session.stage === "questions" ? nextStep(session) : null;
    if (!step || step.kind !== "ask") {
      yield session;
      return;
    }
    const options = step.card.options.map((o) => o.option);
    for (const option of depth < 4 ? options : options.slice(0, 1))
      yield* from(answer(session, step.card.slot, option), depth + 1);
  }
  yield* from(createSession(context, "zh-CN", [], 0, "dynamic"), 0);
}

suite("neighbour index (what ships in the app)", () => {
  it("holds vectors and concept indices only — no id, name, source, text or score", () => {
    expect(Object.keys(index).sort()).toEqual(
      [
        "basis",
        "concept_share",
        "concepts",
        "contract_version",
        "dimensions",
        "family_weight",
        "holdout_records",
        "lift",
        "mentions",
        "neighbours",
        "power",
        "records",
        "support",
        "vectors",
        "word_concepts",
      ].sort(),
    );
    expect(index.holdout_records).toBe(0);
    const vectors = atob(index.vectors);
    expect(vectors.length).toBe(index.records * index.dimensions.length);
    const mentions = atob(index.mentions);
    let at = 0;
    for (let r = 0; r < index.records; r += 1) {
      const count = mentions.charCodeAt(at);
      for (let i = 1; i <= count; i += 1)
        expect(mentions.charCodeAt(at + i)).toBeLessThan(index.concepts.length);
      at += 1 + count;
    }
    expect(at).toBe(mentions.length);
  });

  it("scores the candidate words of the bundle, position by position", () => {
    const candidates = Object.keys(presentation.dimension_tags).filter(
      (d) => presentation.dimension_roles[d] !== "evaluation",
    );
    expect(Object.keys(index.word_concepts).sort()).toEqual(candidates.sort());
    for (const d of candidates)
      expect(
        (index.word_concepts as Record<string, unknown[]>)[d],
      ).toHaveLength(presentation.dimension_tags[d]!["zh-CN"].length);
  });
});

suite("neighbour fill", () => {
  it("scores only what is distinctive: at least `lift` times the corpus rate, never a word for being common", () => {
    let scored = 0;
    for (const context of CONTEXTS)
      for (const session of walks(context)) {
        const result = firstDescription(session).result!;
        const scores = neighbourWordScores(result.vTarget)!;
        expect(neighbourWordScores(result.vTarget)).toBe(scores); // one computation per target
        for (const [d, list] of Object.entries(scores))
          list.forEach((score, i) => {
            if (!score) return;
            scored += 1;
            const word = (
              index.word_concepts as Record<
                string,
                Array<{ exact?: number; family?: number[] } | null>
              >
            )[d]![i]!;
            // an exact word carries its concept's ratio; a word scored through its sub-family carries a share of it
            if (word.exact !== undefined)
              expect(score).toBeGreaterThanOrEqual(index.lift);
            else
              expect(score).toBeGreaterThanOrEqual(
                (index.family_weight * index.lift) / word.family!.length,
              );
          });
      }
    expect(scored).toBeGreaterThan(0);
    expect(neighbourWordScores(new Array(12).fill(0))).toBeNull();
  }, 120_000);

  it("a distinctive word leads its dimension; without one the rotation stands; the reader's answer always wins", () => {
    let changed = 0;
    let same = 0;
    for (const context of CONTEXTS)
      for (const session of walks(context)) {
        const result = firstDescription(session).result!;
        const scores = neighbourWordScores(result.vTarget)!;
        const plain = describe(result, "zh-CN");
        const filled = describe(result, "zh-CN", {}, { neighbours: true });
        expect(filled.all).toHaveLength(plain.all.length);
        const dimensions = [...new Set(plain.all.map((w) => w.dimension))];
        for (const d of dimensions) {
          const before = plain.all.filter((w) => w.dimension === d);
          const after = filled.all.filter((w) => w.dimension === d);
          expect(after).toHaveLength(before.length); // the fill reorders words inside a dimension, nothing else
          const words = presentation.dimension_tags[d]!["zh-CN"];
          if (scores[d]!.every((s) => !s)) {
            expect(after).toEqual(before);
            same += 1;
          } else if (after[0]!.text !== before[0]!.text) {
            expect(scores[d]![words.indexOf(after[0]!.text)]).toBeGreaterThan(
              0,
            );
            changed += 1;
          }
          // the reader pointed at a word of this dimension: their word leads, scores or not
          const lead = words[words.length - 1]!;
          const hinted = describe(
            result,
            "zh-CN",
            { [d]: { lead } },
            { neighbours: true },
          );
          expect(hinted.all.find((w) => w.dimension === d)!.text).toBe(lead);
        }
      }
    expect(changed).toBeGreaterThan(0);
    expect(same).toBeGreaterThan(0);
  }, 120_000);

  it("keeps both languages aligned and the six fixed questions on their rotation", () => {
    const context = CONTEXTS[0]!;
    for (const session of walks(context)) {
      const described = firstDescription(session);
      const zh = described.description!.all;
      const en = describe(
        described.result!,
        "en",
        {},
        { neighbours: true },
      ).all;
      const plainZh = describe(described.result!, "zh-CN").all;
      const plainEn = describe(described.result!, "en").all;
      // same positions in both languages: the en word sits where the zh word sits in the dimension's list
      const filledZh = describe(
        described.result!,
        "zh-CN",
        {},
        { neighbours: true },
      ).all;
      filledZh.forEach((w, i) => {
        const tags = presentation.dimension_tags[w.dimension]!;
        expect(tags.en[tags["zh-CN"].indexOf(w.text)]).toBe(en[i]!.text);
      });
      expect(plainEn).toHaveLength(plainZh.length);
      expect(zh).toHaveLength(filledZh.length);
    }
    const answers = { Q0: "A", Q1: "B", Q2: "C", Q3: "A", Q4: "A", Q5: "C" };
    const result = inferFromFlow(context, answers);
    let fixed = createSession(context, "zh-CN", [], 0, "fixed");
    for (let guard = 0; fixed.stage === "questions" && guard < 8; guard += 1) {
      const step = nextStep(fixed);
      if (step.kind !== "ask") break;
      fixed = answer(
        fixed,
        step.card.slot,
        answers[step.card.slot as keyof typeof answers],
      );
    }
    const described = firstDescription(fixed);
    expect(described.description!.all).toEqual(
      describe(described.result!, "zh-CN").all,
    );
    expect(result.vTarget).toHaveLength(12);
  }, 120_000);
});

suite("the card follows the reader's signals (R3-D49)", () => {
  const presentationFamilies = (
    productVectorBundle.presentation as unknown as {
      dimension_tag_families: Record<string, string[]>;
    }
  ).dimension_tag_families;
  const familyOf = (dimension: string, word: string) =>
    presentationFamilies[dimension]![
      presentation.dimension_tags[dimension]!["zh-CN"].indexOf(word)
    ];

  it("a kind of fruit the reader saw and did not choose is not handed back by the rotation; citrus fills the fruit slots", () => {
    const dark = { c0_preparation: "espresso", c1_roast: "dark" };
    let checked = 0;
    let citrusInFruitSlots = 0;
    for (const session of walks(dark, 1)) {
      if (session.answers.Q0 !== "A1") continue; // the reader said citrus; stone, tropical and dried fruit were on offer
      const described = firstDescription(session);
      const hints = wordHints(session.answers, session.context);
      expect(hints.fruity?.passed?.length ?? 0).toBeGreaterThan(0);
      for (const w of described.description!.all) {
        if (w.dimension === "fruity")
          expect(hints.fruity!.passed, w.text).not.toContain(
            familyOf("fruity", w.text),
          );
        if (w.slot === "fruity") {
          expect(w.dimension).toBe("acidity");
          citrusInFruitSlots += 1;
        }
      }
      checked += 1;
    }
    expect(checked).toBeGreaterThan(0);
    expect(citrusInFruitSlots).toBeGreaterThan(0);
  }, 120_000);

  it("a citrus word in a fruit slot affirms both dimensions when picked, and an answer the reader could not give passes nothing over", () => {
    const v = picksToVector([
      { text: "甜橙", dimension: "acidity", slot: "fruity" },
    ]);
    const dims = productVectorBundle.dimensions as string[];
    expect(v[dims.indexOf("acidity")]).toBeGreaterThan(0);
    expect(v[dims.indexOf("fruity")]).toBeGreaterThan(0);
    const context = CONTEXTS[0]!;
    const unanswered = shownQuestion("A", context, "zh-CN").unanswered!.id;
    expect(
      wordHints({ Q0: unanswered }, context).fruity?.passed,
    ).toBeUndefined();
  });
});

suite("what the reader confirms reaches the card (owner, 2026-09-20)", () => {
  const dims = productVectorBundle.dimensions as string[];
  const roles = presentation.dimension_roles;

  it("a word ticked in the confirmation step is on the card as that very word, in both languages", () => {
    let evaluationChoices = 0;
    let candidateChoices = 0;
    for (const context of [CONTEXTS[0]!, CONTEXTS[3]!])
      for (const walked of walks(context, 17)) {
        const described = firstDescription(walked);
        const all = described.description!.all;
        const own = [...all]
          .sort(
            (x, y) =>
              (described.result!.vUser[dims.indexOf(y.dimension)] ?? 0) -
              (described.result!.vUser[dims.indexOf(x.dimension)] ?? 0),
          )
          .slice(0, 5);
        const gated = submitPicks(described, own);
        if (gated.stage !== "q6") continue;
        for (const option of gated.q6!.options) {
          const done = answerQ6(gated, [option.dimension]);
          const english = relocalize(done, "en");
          // the card keeps what the reader picked: after the confirmation step every word on it is one of their
          // picks or the word they just ticked — nothing they did not choose; and it switches language whole
          const mine = new Set(own.map((w) => w.text));
          // (a confirmed dimension is led by the reader's own second-level word when they gave one)
          const theirWord = wordHints(gated.answers, gated.context)[
            option.dimension
          ]?.lead;
          for (const text of done.card!.picked)
            expect(
              mine.has(text) || text === option.text || text === theirWord,
              text,
            ).toBe(true);
          expect(english.card!.picked).toHaveLength(done.card!.picked.length);
          expect(english.card!.picked.join("")).not.toMatch(/[一-鿿]/);
          // "I chose cinnamon and it is not on the card": whatever its dimension, the ticked word is one of the
          // card's words, as shown — and it does not repeat as an evaluation row
          if (roles[option.dimension] === "evaluation") evaluationChoices += 1;
          else candidateChoices += 1;
          expect(done.card!.picked, option.text).toContain(option.text);
          expect(english.card!.picked).toContain(
            q6Word(option.dimension, "en"),
          );
          expect(done.card!.evaluation.map((r) => r.text)).not.toContain(
            option.text,
          );
        }
      }
    expect(evaluationChoices).toBeGreaterThan(0);
    expect(candidateChoices).toBeGreaterThan(0);
  }, 240_000);

  it("of the flavors ticked in the confirmation step, every one — so at least two — is on the final card", () => {
    let checked = 0;
    for (const context of [CONTEXTS[0]!, CONTEXTS[3]!])
      for (const walked of walks(context, 23)) {
        const described = firstDescription(walked);
        const own = [...described.description!.all]
          .sort(
            (x, y) =>
              (described.result!.vUser[dims.indexOf(y.dimension)] ?? 0) -
              (described.result!.vUser[dims.indexOf(x.dimension)] ?? 0),
          )
          .slice(0, 5);
        const gated = submitPicks(described, own);
        if (gated.stage !== "q6") continue;
        const options = gated.q6!.options;
        // two, three, and every option ticked at once — five card words and four rows are the caps
        for (const ticked of [
          options.slice(0, 2),
          options.slice(2, 5),
          options,
        ]) {
          const done = answerQ6(
            gated,
            ticked.map((o) => o.dimension),
          );
          const onCard = new Set([
            ...done.card!.picked,
            ...done.card!.evaluation.map((r) => r.text),
          ]);
          const shown = ticked.filter((o) => onCard.has(o.text));
          // up to five ticked words are all among the card's words; beyond that the rest may only show as rows
          const words = ticked.filter((o) =>
            done.card!.picked.includes(o.text),
          );
          expect(words.length, ticked.map((o) => o.text).join(" ")).toBe(
            Math.min(ticked.length, 5),
          );
          expect(shown.length).toBeGreaterThanOrEqual(2);
          checked += 1;
        }
      }
    expect(checked).toBeGreaterThan(0);
  }, 240_000);

  it("three words are enough to confirm a card; five is the suggestion", () => {
    const flow = productVectorBundle.question_flow.first_description as {
      pick_count: number;
      pick_min: number;
    };
    expect(flow.pick_min).toBe(3);
    expect(flow.pick_count).toBe(5);
    const described = firstDescription([...walks(CONTEXTS[0]!, 40)][0]!);
    expect(described.description!.prompt).toMatch(/3–5/);
    for (const count of [3, 4, 5]) {
      let done = submitPicks(
        described,
        described.description!.all.slice(0, count),
      );
      if (done.stage === "q6")
        done = answerQ6(done, [done.q6!.options[0]!.dimension]);
      expect(done.stage).toBe("final");
      expect(done.card!.picked.length).toBeGreaterThanOrEqual(3);
    }
  });
});

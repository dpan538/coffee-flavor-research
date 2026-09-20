/**
 * Question flow for product-vector-v1: the owner's coherence decision tree (2026-09-12).
 *
 *   base pair Q0-Q1  →  check Q2-Q3 against it  →  Path 1 (coherent: light confirm Q4, deliver)
 *                                                  Path 2 (mild conflict: correct Q4, confirm Q5)
 *                                                  Path 3 (severe conflict: correct Q4-Q5)
 *                                                  Path 4 (late mutation: 0-2 agree, 3-4 contradict)
 *   → first description (3 + 5 words) → the user picks 5 → escalation gate → final card, or Q6 → second description.
 *
 * Coherence is a cosine, but not between raw answer sub-vectors: each answer moves one or two of
 * the 12 dimensions, so two consistent answers about different dimensions have cosine 0. Each answer
 * group is first mapped to its profile signature (cosine to every profile centroid); the coherence
 * of two groups is the cosine of their signatures — "do these answers point at the same profiles?".
 * Thresholds are the owner's (bundle.question_flow.thresholds).
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };
import {
  DIMENSIONS,
  add,
  buildVPred,
  defectNote,
  cosine,
  infer,
  normalize,
  rankBeans,
  rankProfiles,
  statementsFor,
  vTarget,
  zero,
  type BeanVector,
  type ContextAnswers,
  type InferenceResult,
  type Locale,
  type PerceptionAnswers,
  type ScienceLine,
  type Vector,
} from "./engine";

import { neighbourWordScores } from "./neighbours";
import {
  answeredRows,
  dynamicOptionVector,
  followUpKeys,
  isDynamicOption,
} from "./dynamicBank";
import {
  cardNote,
  descriptionNote,
  noteSeed,
  referenceNote,
  structureNote,
  supportNotes,
} from "./notes";

const flow = bundle.question_flow;
const presentation = bundle.presentation;

export type Slot = "Q0" | "Q1" | "Q2" | "Q3" | "Q4" | "Q5";
export const SLOTS = flow.slots.map((s) => s.slot as Slot);
/** Answers by question key: the six slots, and in the dynamic bank also "E1", "E2" and "S:<first-level option>". */
export type FlowAnswers = Partial<Record<string, string>>;
export type FlowOptions = {
  /** the dynamic question bank's flow: four core questions, then two follow-ups at most (R3-D40) */
  dynamic?: boolean;
  /** rotates the second follow-up between visits; fixed for a session */
  nonce?: number;
};
export type CoherenceLevel = "coherent" | "mild" | "severe";
export type CoherenceCheck = {
  between: [string, string];
  similarity: number;
  level: CoherenceLevel;
  paradox?: boolean;
};
export type FlowPath = 1 | 2 | 3 | 4;
export type FlowStep = {
  ask: string[];
  deliver: boolean;
  path: FlowPath | null;
  checks: CoherenceCheck[];
  escalationEligible: boolean;
  reason: string;
  /** dynamic bank: how many questions this cup is asked in all, once the four core answers decide the follow-ups */
  planned?: number;
  /** dynamic bank, once the four core answers are in: every question this cup is asked, in order — six at most. An
   *  answer kept from an earlier path for a question that is not among them will never be asked for again. */
  plannedKeys?: string[];
  /** dynamic bank: the follow-up is a strong correction — the four core answers are in severe conflict; such a
   *  question may show five options instead of four (owner, 2026-09-20) */
  strong?: boolean;
};
/** A word and the dimension it belongs to. `slot` is set when the word fills ANOTHER dimension's slot: the reader said
 *  "citrus", so the fruit weight of that answer is shown as citrus words (R3-D49); picking such a word affirms both. */
export type Word = { text: string; dimension: string; slot?: string };
export type Description = {
  main: Word[];
  secondary: Word[];
  all: Word[];
  prompt: string;
};
export type GateDecision = {
  escalate: boolean;
  reason: string;
  similarityPicksUser: number;
  similarityPicksPred: number;
  severeHistory: boolean;
  biasConfirmed: boolean;
};
export type Q6Option = { dimension: string; text: string; delta: number };
export type EvaluationRow = { dimension: string; label: string; text: string };
export type FinalCard = {
  picked: string[];
  /** the card's evaluation line: the strongest evaluation dimensions of V_target, one word each (owner, 2026-09-17) */
  evaluation: EvaluationRow[];
  science: ScienceLine[];
  /** the exported card's sentence: what stands out in this cup, not addressed to the reader (owner, 2026-09-19) */
  cardNote: string;
  closing: string;
  profileTitle: string | null;
  profileId: string | null;
};

const N = DIMENSIONS.length;

function questionOf(slot: Slot): keyof typeof bundle.matrix_q {
  const entry = flow.slots.find((s) => s.slot === slot);
  if (!entry) throw new Error(`unknown slot ${slot}`);
  return entry.question as keyof typeof bundle.matrix_q;
}

/** Unnormalised increment vector of one answer: a dynamic-bank option by its own weights, else a Matrix_Q letter. */
export function slotVector(slot: string, answer: string): Vector {
  const dynamic = dynamicOptionVector(answer);
  if (dynamic) return dynamic;
  if (!SLOTS.includes(slot as Slot)) return zero();
  const spec =
    (
      bundle.matrix_q[questionOf(slot as Slot)] as Record<
        string,
        Record<string, number>
      >
    )[answer] ?? {};
  const v = zero();
  for (const [dim, inc] of Object.entries(spec)) {
    const i = DIMENSIONS.indexOf(dim);
    if (i >= 0) v[i] = inc;
  }
  return v;
}

/** Unit vector of a group of answered slots (zero vector if none answered). */
export function groupVector(answers: FlowAnswers, slots: string[]): Vector {
  let sum = zero();
  for (const slot of slots) {
    const answer = answers[slot];
    if (answer) sum = add(sum, slotVector(slot, answer));
  }
  return normalize(sum);
}

/** Cosine of a vector to every profile centroid, negatives clipped, as a unit vector. */
export function profileSignature(v: Vector): Vector {
  return normalize(
    bundle.profiles.map((p) => Math.max(cosine(v, p.centroid), 0)),
  );
}

/** Roast-polarity of a vector: bright-light (+) vs dark-heavy (−), per bundle.question_flow.polarity. */
export function polarity(v: Vector): number {
  const weights = flow.polarity.weights as Record<string, number>;
  return DIMENSIONS.reduce(
    (acc, d, i) => acc + (v[i] ?? 0) * (weights[d] ?? 0),
    0,
  );
}

function polarityFlips(a: Vector, b: Vector, minMagnitude: number): boolean {
  const pa = polarity(a);
  const pb = polarity(b);
  return (
    (pa >= minMagnitude && pb <= -minMagnitude) ||
    (pb >= minMagnitude && pa <= -minMagnitude)
  );
}

function levelOf(similarity: number): CoherenceLevel {
  const { coherent, mild } = flow.thresholds;
  return similarity >= coherent
    ? "coherent"
    : similarity >= mild
      ? "mild"
      : "severe";
}

/**
 * Coherence of two answer groups: cosine of their profile signatures, with the roast-polarity paradox
 * guard — groups whose polarities flip strongly (light-roast acidity then heavy bitterness) are a
 * sensory paradox and read as severe whatever their signature overlap says.
 */
export function coherence(
  a: Vector,
  b: Vector,
  between: [string, string] = ["a", "b"],
): CoherenceCheck {
  let similarity = cosine(profileSignature(a), profileSignature(b));
  let paradox = false;
  if (polarityFlips(a, b, flow.polarity.min_magnitude)) {
    similarity = Math.min(similarity, flow.thresholds.mild - 0.01);
    paradox = true;
  }
  return { between, similarity, level: levelOf(similarity), paradox };
}

/**
 * Context conflict: the context's theoretical vector against the base pair. A polarity flip (dark
 * espresso, bright peach acidity) caps the first check at mild — a correction path, never severe on
 * its own, because V_pred is a soft prior.
 */
export function contextCheck(
  context: ContextAnswers | undefined,
  base: Vector,
): CoherenceCheck | null {
  if (!context) return null;
  const { vPred } = buildVPred(context);
  if (!vPred.some((x) => x !== 0)) return null;
  const similarity = cosine(profileSignature(vPred), profileSignature(base));
  const flips = polarityFlips(vPred, base, flow.polarity.context_min_magnitude);
  const capped = flips
    ? Math.min(similarity, flow.thresholds.coherent - 0.01)
    : similarity;
  return {
    between: ["context", "Q0-Q1"],
    similarity: capped,
    level: flips
      ? levelOf(capped) === "severe"
        ? "mild"
        : levelOf(capped)
      : levelOf(capped),
    paradox: flips,
  };
}

/** An answer whose increment is empty ("not noticeable") carries no direction. */
export function absentAnswer(answers: FlowAnswers, slot: string): boolean {
  const a = answers[slot];
  return (
    a !== undefined && a !== "" && !slotVector(slot, a).some((x) => x !== 0)
  );
}

/** Slot answers → Matrix_Q answers, so infer() runs unchanged. */
export function perceptionAnswers(answers: FlowAnswers): PerceptionAnswers {
  const out: PerceptionAnswers = {};
  for (const slot of SLOTS) {
    const answer = answers[slot];
    if (answer && !isDynamicOption(answer)) out[questionOf(slot)] = answer;
  }
  return out;
}

/** Which slots to ask next, or deliver the first description; a pure function of the answers so far.
 *  The owner's tree: base pair Q0-Q1 → check Q2-Q3 together against it → Path 1 (Q4 confirm),
 *  Path 2 (Q4 correct, Q5 confirm), Path 3 (Q4-Q5 correct), Path 4 (late mutation after Q4). */
export function flowStep(
  answers: FlowAnswers,
  context?: ContextAnswers,
  options: FlowOptions = {},
): FlowStep {
  const has = (s: string) => answers[s] !== undefined && answers[s] !== "";
  const missing = (...slots: string[]) => slots.filter((s) => !has(s));
  const checks: CoherenceCheck[] = [];
  const ask = (slots: string[], reason: string): FlowStep => ({
    ask: slots,
    deliver: false,
    path: null,
    checks,
    escalationEligible: false,
    reason,
  });
  const deliver = (
    path: FlowPath,
    escalationEligible: boolean,
    reason: string,
  ): FlowStep => ({
    ask: [],
    deliver: true,
    path,
    checks,
    escalationEligible,
    reason,
  });
  const g = (slots: string[]) => groupVector(answers, slots);

  if (missing("Q0", "Q1").length)
    return ask(missing("Q0", "Q1"), "base perception pair");
  if (missing("Q2", "Q3").length)
    return ask(missing("Q2", "Q3"), "coherence check needs Q2-Q3");
  let c23 = coherence(g(["Q0", "Q1"]), g(["Q2", "Q3"]), ["Q0-Q1", "Q2-Q3"]);
  // owner copy review 2026-09-12: a "not noticeable" answer (empty increment) adds no direction — and Q3 on its own
  // is direction-degenerate (all three body answers point the same way) — so a group holding one cannot claim a
  // severe conflict: absence contradicts nothing. Capped at mild: one more question, never Path 3.
  const absence = ["Q0", "Q1", "Q2"].some((s) => absentAnswer(answers, s));
  if (absence && c23.level === "severe")
    c23 = {
      ...c23,
      similarity: Math.max(c23.similarity, flow.thresholds.mild),
      level: "mild",
      paradox: false,
    };
  checks.push(c23);
  const ctx = contextCheck(context, g(["Q0", "Q1"]));
  if (ctx) checks.push(ctx);
  // the first decision takes the worse of the answer check and the context check
  const order: Record<CoherenceLevel, number> = {
    coherent: 2,
    mild: 1,
    severe: 0,
  };
  const first: CoherenceLevel =
    ctx && order[ctx.level] < order[c23.level] ? ctx.level : c23.level;

  if (options.dynamic) {
    // The dynamic bank (R3-D40): bitterness and the overall impression are no longer asked of every cup. The tree's
    // checks are the same; what changes is which questions follow the four core ones — see followUpKeys.
    const follow = followUpKeys(context ?? {}, answers, first, options.nonce);
    const need = follow.filter((k) => !has(k));
    if (need.length)
      return {
        planned: 4 + follow.length,
        plannedKeys: ["Q0", "Q1", "Q2", "Q3", ...follow],
        strong: first === "severe",
        ...ask(
          [need[0]!],
          first === "severe"
            ? "Path 3: correction questions"
            : first === "mild"
              ? "Path 2: confirmation, then the most telling detail"
              : "Path 1: the most telling details",
        ),
      };
    if (first === "severe") {
      const withBase = coherence(g(["Q4", "Q5"]), g(["Q0", "Q1"]), [
        "Q4-Q5",
        "Q0-Q1",
      ]);
      const withCheck = coherence(g(["Q4", "Q5"]), g(["Q2", "Q3"]), [
        "Q4-Q5",
        "Q2-Q3",
      ]);
      checks.push(withBase, withCheck);
      return withBase.level === "coherent" || withCheck.level === "coherent"
        ? deliver(3, false, "Path 3: Q4-Q5 agree with one side")
        : deliver(
            3,
            true,
            "Path 3: Q4-Q5 agree with neither side — Q6 eligible after the picks",
          );
    }
    if (first === "mild") {
      const withBase = coherence(g(["Q5"]), g(["Q0", "Q1", "Q3", "Q4"]), [
        "Q5",
        "Q0-Q1+Q3-Q4",
      ]);
      const withCheck = coherence(g(["Q5"]), g(["Q2", "Q3", "Q4"]), [
        "Q5",
        "Q2+Q3-Q4",
      ]);
      checks.push(withBase, withCheck);
      return withBase.level === "coherent" || withCheck.level === "coherent"
        ? deliver(2, false, "Path 2: Q5 agrees with one side")
        : deliver(
            2,
            true,
            "Path 2: Q5 conflicts again — Q6 eligible after the picks",
          );
    }
    if (has("Q4")) {
      const late = coherence(g(["Q0", "Q1", "Q2"]), g(["Q3", "Q4"]), [
        "Q0-Q2",
        "Q3-Q4",
      ]);
      checks.push(late);
      if (late.level === "severe")
        return deliver(
          4,
          true,
          "Path 4: late mutation — Q6 eligible after the picks",
        );
    }
    return deliver(1, false, "Path 1: coherent throughout");
  }
  if (first === "severe") {
    // Path 3: correct with Q4-Q5; Q4-Q5 must agree with one side
    const need = missing("Q4", "Q5");
    if (need.length) return ask(need, "Path 3: correction questions");
    const withBase = coherence(g(["Q4", "Q5"]), g(["Q0", "Q1"]), [
      "Q4-Q5",
      "Q0-Q1",
    ]);
    const withCheck = coherence(g(["Q4", "Q5"]), g(["Q2", "Q3"]), [
      "Q4-Q5",
      "Q2-Q3",
    ]);
    checks.push(withBase, withCheck);
    if (withBase.level === "coherent" || withCheck.level === "coherent")
      return deliver(3, false, "Path 3: Q4-Q5 agree with one side");
    return deliver(
      3,
      true,
      "Path 3: Q4-Q5 agree with neither side — Q6 eligible after the picks",
    );
  }
  if (first === "mild") {
    // Path 2: correct with Q4 (Q3 already in hand), confirm with Q5
    if (!has("Q4")) return ask(["Q4"], "Path 2: correction question");
    if (!has("Q5")) return ask(["Q5"], "Path 2: light confirmation");
    const withBase = coherence(g(["Q5"]), g(["Q0", "Q1", "Q3", "Q4"]), [
      "Q5",
      "Q0-Q1+Q3-Q4",
    ]);
    const withCheck = coherence(g(["Q5"]), g(["Q2", "Q3", "Q4"]), [
      "Q5",
      "Q2+Q3-Q4",
    ]);
    checks.push(withBase, withCheck);
    if (withBase.level === "coherent" || withCheck.level === "coherent")
      return deliver(2, false, "Path 2: Q5 agrees with one side");
    return deliver(
      2,
      true,
      "Path 2: Q5 conflicts again — Q6 eligible after the picks",
    );
  }
  // Path 1: light confirmation with Q4, then the late-mutation check (Path 4)
  if (!has("Q4")) return ask(["Q4"], "Path 1: light confirmation");
  const late = coherence(g(["Q0", "Q1", "Q2"]), g(["Q3", "Q4"]), [
    "Q0-Q2",
    "Q3-Q4",
  ]);
  checks.push(late);
  if (late.level === "severe")
    return deliver(
      4,
      true,
      "Path 4: late mutation — Q6 eligible after the picks",
    );
  return deliver(1, false, "Path 1: coherent throughout");
}

/** Run the inference from slot answers (Q6 aside). */
export function inferFromFlow(
  context: ContextAnswers,
  answers: FlowAnswers,
  options: { alpha?: number; beans?: BeanVector[] } = {},
): InferenceResult {
  const vUser = dynamicUserVector(answers);
  return infer(context, perceptionAnswers(answers), {
    ...options,
    ...(vUser ? { vUser } : {}),
  });
}

/** The reader's vector when the answers come from the dynamic bank (its options carry their own weights); undefined
 *  for Matrix_Q letters, which keep the original arithmetic bit for bit. */
export function dynamicUserVector(answers: FlowAnswers): Vector | undefined {
  if (!Object.values(answers).some((a) => isDynamicOption(a))) return undefined;
  let sum = zero();
  for (const [key, answer] of Object.entries(answers))
    if (answer) sum = add(sum, slotVector(key, answer));
  return normalize(sum);
}

function wordLists(dimension: string, locale: Locale): string[] {
  const owned =
    (presentation.dimension_tags as Record<string, Record<Locale, string[]>>)[
      dimension
    ]?.[locale] ?? [];
  const consumer =
    (presentation.consumer_terms as Record<string, Record<Locale, string[]>>)[
      dimension
    ]?.[locale] ?? [];
  return [...owned, ...consumer];
}

/** The owner-approved words of a dimension, started at a cup-specific point; consumer terms follow unrotated, as before. */
/**
 * A dimension's words for one cup: the list rotated by the cup's seed, then spread by sub-family — a soft constraint,
 * not a cap (owner, 2026-09-19). Some coffees really are built around one kind of flavor, so nothing limits how many
 * words a dimension may supply; but near-identical words (two mandarins, three chocolates) should not crowd a card by
 * accident of list order. So the first word of every sub-family comes before any sub-family's second word, in rotation
 * order. When the reader's answers point to one sub-family (`focus`, from the second-level questions), that sub-family
 * leads and may repeat: the spread yields to what the reader says. Index-based, so both languages stay aligned.
 *
 * `scores` (owner, 2026-09-20, R3-D47) say which words are DISTINCTIVE of coffees like this one (neighbours.ts): a
 * word scores only when the records nearest to the cup mention it clearly more often than coffee in general does.
 * They apply only to a dimension the reader gave NO signal for; with a hint, the reader's answer decides. A distinctive
 * word no longer comes and goes with the rotation — it leads its dimension; every other word (score 0: the words that
 * are common everywhere, and the ones the corpus cannot score) keeps its rotation order, and the spread by sub-family
 * still holds. The aim is to steady what is evident for this cup, never to push what is strong on every cup.
 */
export type WordHints = Record<
  string,
  { family?: string; lead?: string; passed?: string[]; from?: string }
>;

function rotatedWordList(
  dimension: string,
  locale: Locale,
  seed: number,
  hint: { family?: string; lead?: string; passed?: string[] } = {},
  scores?: readonly number[],
): string[] {
  const focus = hint.family;
  const owned =
    (presentation.dimension_tags as Record<string, Record<Locale, string[]>>)[
      dimension
    ]?.[locale] ?? [];
  const families =
    (
      presentation as unknown as {
        dimension_tag_families?: Record<string, string[]>;
      }
    ).dimension_tag_families?.[dimension] ?? [];
  const consumer =
    (presentation.consumer_terms as Record<string, Record<Locale, string[]>>)[
      dimension
    ]?.[locale] ?? [];
  const familyOf = (index: number) => families[index] ?? `w${index}`;
  // the base order interleaves the sub-families: with runs of one sub-family in the list, the word that follows a run
  // would be drawn far more often than the others
  const byFamily = new Map<string, number[]>();
  owned.forEach((_, i) =>
    byFamily.set(familyOf(i), [...(byFamily.get(familyOf(i)) ?? []), i]),
  );
  const base: number[] = [];
  for (let round = 0; base.length < owned.length; round += 1)
    for (const members of byFamily.values())
      if (members[round] !== undefined) base.push(members[round]!);
  const offset = owned.length
    ? (seed + DIMENSIONS.indexOf(dimension)) % owned.length
    : 0;
  const rotated = base.map((_, i) => base[(offset + i) % base.length]!);
  // the very word the reader chose at the second level leads; then the sub-family pointed to; then the spread
  const zhWords =
    (presentation.dimension_tags as Record<string, Record<Locale, string[]>>)[
      dimension
    ]?.["zh-CN"] ?? [];
  const lead = hint.lead ? zhWords.indexOf(hint.lead) : -1;
  const focused = [
    ...(lead >= 0 ? [lead] : []),
    ...(focus
      ? rotated.filter((i) => familyOf(i) === focus && i !== lead)
      : []),
  ];
  const open = rotated.filter((i) => !focused.includes(i));
  const rest =
    scores && !hint.family && !hint.lead
      ? open
          .map((i, at) => ({ i, at }))
          .sort(
            (a, b) => (scores[b.i] ?? 0) - (scores[a.i] ?? 0) || a.at - b.at,
          )
          .map((x) => x.i)
      : open;
  // round by round: every sub-family's next word, in the order the rotation meets the sub-families
  const spreadOf = (indices: number[]): number[] => {
    const queues = new Map<string, number[]>();
    for (const i of indices)
      queues.set(familyOf(i), [...(queues.get(familyOf(i)) ?? []), i]);
    const out: number[] = [];
    while (out.length < indices.length)
      for (const queue of queues.values()) {
        const next = queue.shift();
        if (next !== undefined) out.push(next);
      }
    return out;
  };
  // sub-families the reader was shown and did not choose come last (R3-D49): the card follows the reader's signals
  const passed = new Set(hint.passed ?? []);
  const spread = [
    ...spreadOf(rest.filter((i) => !passed.has(familyOf(i)))),
    ...spreadOf(rest.filter((i) => passed.has(familyOf(i)))),
  ];
  return [...focused, ...spread].map((i) => owned[i]!).concat(consumer);
}

/** owner (2026-09-17): a dimension is either a candidate (its words go to the pick list) or an evaluation dimension
 *  (body, bitter & roasted, fermented & winey, spice, defect: its words go to the card's evaluation line, never to the
 *  pick list). The roles live in the bundle (presentation.dimension_roles, from CONCEPT_FLAVOR_TAGS.tsv). */
function dimensionRole(dimension: string): "candidate" | "evaluation" {
  const roles =
    (presentation as { dimension_roles?: Record<string, string> })
      .dimension_roles ?? {};
  return roles[dimension] === "evaluation" ? "evaluation" : "candidate";
}

/** A vector with the evaluation dimensions zeroed and renormalised: the space the reader's picks live in. */
function candidateSubspace(v: Vector): Vector {
  return normalize(
    v.map((x, i) =>
      dimensionRole(DIMENSIONS[i] as string) === "candidate" ? x : 0,
    ),
  );
}

/** A stable integer from V_target: cups with different targets start their word lists at different points. */
function wordSeed(result: InferenceResult): number {
  return Math.abs(
    Math.round(
      result.vTarget.reduce(
        (sum, v, i) => sum + Math.abs(v) * (i + 1) * 97,
        0,
      ) * 100,
    ),
  );
}

/**
 * First description: 3 main + 5 secondary words drawn from V_target's dimensions, each word attributable to a
 * dimension. The three main words come from the three strongest dimensions (one each); the remaining slots are
 * shared in proportion to dimension weight (largest remainder), so a cup led by fruit and sweetness shows several
 * fruit and sugar words instead of one word from every faint dimension (owner, 2026-09-17: the cards must not keep
 * repeating one small set). Each dimension's list is rotated by a cup-specific seed, so which words appear also
 * varies between cups, and spread by sub-family as a soft constraint (see rotatedWordList): there is no fixed cap on
 * one kind of flavor. Both languages stay aligned position by position. With `options.neighbours` (the dynamic flow),
 * a dimension the reader gave no signal for takes its word order from the records nearest to this cup (R3-D47).
 */
export function describe(
  result: InferenceResult,
  locale: Locale,
  hints: WordHints | Record<string, string> = {},
  options: { neighbours?: boolean } = {},
): Description {
  const hintOf = (d: string) => {
    const h = (hints as Record<string, unknown>)[d];
    return typeof h === "string"
      ? { family: h }
      : ((h as WordHints[string] | undefined) ?? {});
  };
  const { main, secondary } = flow.first_description;
  const total = main + secondary;
  // candidate dimensions only: the evaluation dimensions never supply pick words (owner, 2026-09-17)
  const everyRanked = DIMENSIONS.map((d, i) => ({
    d,
    w: result.vTarget[i] ?? 0,
    reader: (result.vUser[i] ?? 0) > 0,
  }))
    .filter((x) => x.w > 0 && dimensionRole(x.d) === "candidate")
    .sort((a, b) => b.w - a.w);
  // measured, not adopted (R3-D49, `prior_slots` in the bundle): "none" gives a word only to dimensions the reader's
  // own answers weigh on; dimensions that come from the context's prior alone fill in only when the card would
  // otherwise fall short
  const readerOnly =
    options.neighbours === true &&
    (flow.first_description as { prior_slots?: string }).prior_slots ===
      "none" &&
    everyRanked.some((x) => x.reader);
  const ranked = readerOnly ? everyRanked.filter((x) => x.reader) : everyRanked;
  const seed = wordSeed(result);
  // the dynamic flow only: where the reader gave no signal, the records nearest to this cup order the words
  const scores = options.neighbours
    ? neighbourWordScores(result.vTarget)
    : null;
  // a dimension's slots may be filled with another dimension's words (`from`: the reader said "citrus", so the fruit
  // weight of that answer stands for citrus words); the words keep the dimension they belong to
  const sourceOf = (d: string) => {
    const from = hintOf(d).from;
    return from && dimensionRole(from) === "candidate" ? from : d;
  };
  const listOf = (d: string) =>
    rotatedWordList(d, locale, seed, hintOf(d), scores?.[d]);
  const lists = new Map(
    everyRanked.map((x) => [x.d, listOf(sourceOf(x.d))] as const),
  );
  // slot quota per dimension: one for each of the top `main` dimensions, the rest by weight among dimensions that
  // reach 12% of the leading weight, never more than a list can supply
  const quota = new Map<string, number>();
  for (const x of ranked.slice(0, main)) quota.set(x.d, 1);
  const eligible = ranked.filter((x) => x.w >= 0.12 * (ranked[0]?.w ?? 0));
  const sumW = eligible.reduce((s, x) => s + x.w, 0) || 1;
  const spare = total - Math.min(main, ranked.length);
  const shares = eligible.map((x) => {
    const exact = (spare * x.w) / sumW;
    return { d: x.d, q: Math.floor(exact), rem: exact - Math.floor(exact) };
  });
  let assigned = shares.reduce((s, x) => s + x.q, 0);
  for (const x of [...shares].sort((a, b) => b.rem - a.rem)) {
    if (assigned >= spare) break;
    x.q += 1;
    assigned += 1;
  }
  // a dimension may hold at most 1 + floor((words - 1) / 4) slots (3 words → 1, 4–7 → 2, 8+ → 3), so short lists do
  // not cycle their few words on every card; the unfilled remainder falls to the round-robin below
  for (const x of shares) {
    // the list's length in ONE language for both: consumer terms differ in number between the languages, and a cap that
    // differed with them put the last words of a card in a different order (found 2026-09-20; picks map by position)
    const size = wordLists(x.d, "zh-CN").length;
    const cap = size ? 1 + Math.floor((size - 1) / 4) : 0;
    quota.set(x.d, Math.min(cap, (quota.get(x.d) ?? 0) + x.q));
  }
  const words: Word[] = [];
  const used = new Set<string>();
  const taken = new Map<string, number>();
  const take = (d: string): boolean => {
    const list = lists.get(d) ?? [];
    let i = taken.get(d) ?? 0;
    while (i < list.length && used.has(list[i]!)) i += 1;
    if (i >= list.length) return false;
    used.add(list[i]!);
    words.push(
      sourceOf(d) === d
        ? { text: list[i]!, dimension: d }
        : { text: list[i]!, dimension: sourceOf(d), slot: d },
    );
    taken.set(d, i + 1);
    return true;
  };
  // main words: the top dimensions, one word each
  for (const x of ranked.slice(0, main)) take(x.d);
  // the rest: round by round in rank order while a dimension still has quota, so the list reads by importance
  for (let round = 1; words.length < total && round < total; round += 1) {
    let progressed = false;
    for (const x of ranked) {
      if (words.length >= total) break;
      if ((taken.get(x.d) ?? 0) >= (quota.get(x.d) ?? 0)) continue;
      if (take(x.d)) progressed = true;
    }
    if (!progressed) break;
  }
  // fallback when the quotas could not be filled (short lists): plain round-robin over every ranked dimension
  for (let round = 0; words.length < total && round < total; round += 1) {
    let progressed = false;
    for (const x of ranked) {
      if (words.length >= total) break;
      if (take(x.d)) progressed = true;
    }
    if (!progressed) break;
  }
  if (readerOnly)
    for (let round = 0; words.length < total && round < total; round += 1) {
      let progressed = false;
      for (const x of everyRanked) {
        if (words.length >= total) break;
        if (take(x.d)) progressed = true;
      }
      if (!progressed) break;
    }
  // reading order: the first word of every dimension present (rank order) before any dimension's second word, so the
  // first `pick_count` positions span as many dimensions as the card holds; the set of words is unchanged
  const ordered: Word[] = [];
  const seen = new Set<string>();
  for (const w of words) {
    const slot = w.slot ?? w.dimension; // a word that fills another dimension's slot stands for that dimension here
    if (seen.has(slot)) continue;
    seen.add(slot);
    ordered.push(w);
  }
  for (const w of words) if (!ordered.includes(w)) ordered.push(w);
  // owner, 2026-09-20: five is a suggestion, not a condition — a reader who finds four words that fit gets a card
  const most = flow.first_description.pick_count;
  const least =
    (flow.first_description as { pick_min?: number }).pick_min ?? most;
  const prompt =
    locale === "zh-CN"
      ? least < most
        ? `选出最贴近你感受的 ${least}–${most} 个词，建议选 ${most} 个。`
        : `选出最贴近你感受的 ${most} 个词。`
      : least < most
        ? `Pick the ${least} to ${most} words closest to what you tasted — ${most} if you can.`
        : `Pick the ${most} words closest to what you tasted.`;
  return {
    main: ordered.slice(0, main),
    secondary: ordered.slice(main, total),
    all: ordered,
    prompt,
  };
}

/**
 * The card's evaluation line (owner, 2026-09-17): the evaluation dimensions are not pick words; the strongest of them
 * in V_target — at least 12% of the leading weight, defect only when it dominates (≥ 0.5) — at most three, each as its
 * dimension label plus one word from the same cup-rotated list the candidates use.
 */
export function evaluate(
  result: InferenceResult,
  locale: Locale,
): EvaluationRow[] {
  const labels = presentation.dimension_labels as Record<
    string,
    Record<Locale, string>
  >;
  const top = Math.max(0, ...result.vTarget.map((v) => v ?? 0));
  const defectDominates =
    (result.vTarget[DIMENSIONS.indexOf("defect")] ?? 0) >= 0.5;
  const seed = wordSeed(result);
  return DIMENSIONS.map((d, i) => ({ d, w: result.vTarget[i] ?? 0 }))
    .filter(
      (x) =>
        dimensionRole(x.d) === "evaluation" &&
        x.w > 0 &&
        x.w >= 0.12 * top &&
        (x.d !== "defect" || defectDominates),
    )
    .sort((a, b) => b.w - a.w)
    .slice(0, 3)
    .map((x) => ({
      dimension: x.d,
      label: labels[x.d]?.[locale] ?? x.d,
      text: rotatedWordList(x.d, locale, seed)[0] ?? "",
    }))
    .filter((r) => r.text !== "");
}

/**
 * The user's picks as a vector: the set of dimensions the reader affirmed, one unit each. Two words of the same
 * dimension count once, so the gate reads which dimensions were confirmed and does not swing with how many words a
 * dimension happened to offer (the candidate list allocates slots by weight since 2026-09-17).
 */
export function picksToVector(picks: Word[]): Vector {
  const v = zero();
  for (const w of picks)
    for (const d of [w.dimension, w.slot]) {
      const i = d ? DIMENSIONS.indexOf(d) : -1;
      if (i >= 0) v[i] = 1;
    }
  return normalize(v);
}

/** Escalation gate: Q6 only when the flow saw a severe conflict AND the picks side with the user's perception against the theory. */
export function escalationGate(
  step: FlowStep,
  result: InferenceResult,
  picks: Word[],
): GateDecision {
  const pv = picksToVector(picks);
  // the picks can only name candidate dimensions (owner, 2026-09-17), so the reader's answers and the reference are
  // compared with them inside that subspace: body, bitterness, fermentation, spice and defect mass, which no pick can
  // affirm or deny, is left out of both cosines
  const similarityPicksUser = cosine(pv, candidateSubspace(result.vUser));
  const similarityPicksPred = cosine(pv, candidateSubspace(result.vPred));
  const severeHistory =
    step.escalationEligible || step.checks.some((c) => c.level === "severe");
  // owner (2026-09-12): the second round is part of the model, not a rare exception. The flow's own verdict decides:
  // on the correction paths (2, 3, 4) picks that side with the reader's answers more than with the reference open it
  // (margin 0.08, and not already aligned with the reference); after a severe conflict, picks that leave the
  // reference (< mild) open it too. Path 1 (coherent throughout) never opens it — the consistent persona stays at five questions.
  const conflictPath = step.path !== null && step.path !== 1;
  const leansUser = similarityPicksUser >= similarityPicksPred + 0.08;
  const leavesReference = similarityPicksPred < flow.thresholds.mild;
  const biasConfirmed =
    (conflictPath &&
      leansUser &&
      similarityPicksPred < flow.thresholds.coherent) ||
    (severeHistory && (leansUser || leavesReference));
  const escalate = biasConfirmed;
  const reason = escalate
    ? "severe conflict in the flow and the picks confirm the perception bias — Q6"
    : !severeHistory
      ? "no severe conflict — final card"
      : "picks do not confirm a bias against the theory — final card";
  return {
    escalate,
    reason,
    similarityPicksUser,
    similarityPicksPred,
    severeHistory,
    biasConfirmed,
  };
}

/** The same word in another language: the owned lists are aligned position by position. */
export function localizeWord(word: Word, locale: Locale): Word {
  for (const from of ["zh-CN", "en"] as Locale[]) {
    const i = wordLists(word.dimension, from).indexOf(word.text);
    const text = i >= 0 ? wordLists(word.dimension, locale)[i] : undefined;
    if (text) return { ...word, text };
  }
  return word;
}

/** The word that stands for a dimension in the confirmation step; the card shows this very word when it is chosen. */
export function q6Word(dimension: string, locale: Locale): string {
  return wordLists(dimension, locale)[0] ?? "";
}

/** Q6: the strong-correction checkbox — one word per dimension, for the dimensions where user and theory disagree most. */
export function q6Options(result: InferenceResult, locale: Locale): Q6Option[] {
  return DIMENSIONS.map((d, i) => ({
    dimension: d,
    delta: result.deltaV[i] ?? 0,
  }))
    .filter((x) => x.dimension !== "defect")
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, flow.q6.option_count)
    .map((x) => ({
      dimension: x.dimension,
      text: q6Word(x.dimension, locale) || x.dimension,
      delta: x.delta,
    }));
}

/** Apply the Q6 selection as a strong correction (alpha_strong) and re-rank. */
export function applyQ6(
  result: InferenceResult,
  selectedDimensions: string[],
): InferenceResult {
  if (!selectedDimensions.length) return result;
  const vq6 = zero();
  for (const d of selectedDimensions) {
    const i = DIMENSIONS.indexOf(d);
    if (i >= 0) vq6[i] = 1;
  }
  const vUser = normalize(vq6);
  const delta = vUser.map((x, i) => x - (result.vPred[i] ?? 0));
  const target = vTarget(result.vPred, delta, flow.alpha_strong);
  const topDeltaDimensions = delta
    .map((d, i) => ({ dimension: DIMENSIONS[i] as string, delta: d }))
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, 2);
  return {
    ...result,
    vUser,
    deltaV: delta,
    vTarget: target,
    alpha: flow.alpha_strong,
    similarityUserPred: cosine(vUser, result.vPred),
    profiles: rankProfiles(target, result.profiles.length || 3),
    beans: rankBeans(
      target,
      result.beans.map((b) => b.bean),
      result.beans.length || 3,
    ),
    topDeltaDimensions,
  };
}

/** The confirmed profile: the reader's five words weigh as much as the whole answer path, so a card whose picks
 *  left the suggested group is titled by the group they actually confirmed (owner copy review 2, 2026-09-12). */
export function confirmedProfile(
  result: InferenceResult,
  picks: Word[],
): {
  profile: InferenceResult["profiles"][number]["profile"];
  similarity: number;
} | null {
  const pv = picksToVector(picks);
  const v = pv.some((x) => x !== 0)
    ? normalize(add(result.vTarget, pv))
    : result.vTarget;
  return rankProfiles(v, 1)[0] ?? null;
}

/** Final summary card: the user's own 5 words, the notes about the description, the closing line. */
export function finalCard(
  result: InferenceResult,
  picks: Word[],
  locale: Locale,
  options: {
    nonce?: number;
    secondLook?: string[];
    /** the session's answers: aroma, aftertaste and bitterness answered in the dynamic bank go to the evaluation rows */
    answers?: FlowAnswers;
  } = {},
): FinalCard {
  // owner, 2026-09-18: the notes interpret the data (notes.ts) — the reference read against all review records, the
  // one statistic that bears on the confirmed words, what the reader's answers moved. At most four notes (five with
  // the papery group's note). The seed holds nothing language-dependent, so both languages carry the same statistics; the
  // session's nonce lets the same cup draw a different supporting statistic on another visit.
  const seed = noteSeed(result, picks, options.nonce);
  // What the reader answered outranks what the vector implies: the chosen word for bitterness replaces the derived
  // one ("no noticeable bitterness" removes the row), aroma and aftertaste are rows of their own. Four rows at most.
  const answered = answeredRows(options.answers ?? {}, locale);
  const replaced = new Set(answered.rows.map((r) => r.dimension));
  const derived = evaluate(result, locale).filter(
    (r) =>
      !replaced.has(r.dimension) &&
      !(answered.noBitterness && r.dimension === "bitter_roasted"),
  );
  // What the reader ticked in the confirmation step is the last and most explicit thing they said (owner, 2026-09-20:
  // "I chose cinnamon and it is not on the card"): an evaluation dimension chosen there gets its row, with the very
  // word the option showed — not the cup's rotated word, and not removed by an earlier "no noticeable bitterness".
  const labels = presentation.dimension_labels as Record<
    string,
    Record<Locale, string>
  >;
  // (a ticked word that is already among the card's words does not repeat as a row)
  const among = new Set(picks.map((w) => w.text));
  const confirmedRows = (options.secondLook ?? [])
    .filter((d) => dimensionRole(d) === "evaluation" && d !== "defect")
    .filter((d) => !among.has(q6Word(d, locale)))
    .map((d) => ({
      dimension: d,
      label: labels[d]?.[locale] ?? d,
      text: q6Word(d, locale),
    }))
    .filter((r) => r.text);
  const confirmedDims = new Set(confirmedRows.map((r) => r.dimension));
  const evaluation = [
    ...confirmedRows,
    ...[
      ...derived.slice(0, Math.max(0, 4 - answered.rows.length)),
      ...answered.rows,
    ].filter((r) => !confirmedDims.has(r.dimension)),
  ]
    .filter((r) => !among.has(r.text)) // a word on the card does not repeat as a row
    .slice(0, 4);
  const confirmed = confirmedProfile(result, picks);
  // the papery / stale group (owner copy review 2026-09-12): the words are shown, a second sip is suggested, no quality verdict
  const papery =
    confirmed &&
    (confirmed.profile as { anchor_id?: string }).anchor_id === "anchor-16"
      ? defectNote(locale)
      : null;
  const literatureLines = statementsFor(result.context, locale).filter(
    (l) => l.evidenceState === "LITERATURE_CLAIM",
  );
  // a research reference joins two times in three when one applies; the data note is always a single one (owner,
  // 2026-09-19: two notes under the same label read as a bug)
  const literature =
    literatureLines.length > 0 && seed % 3 !== 0
      ? literatureLines[(seed >> 1) % literatureLines.length]!
      : null;
  // one data note: the statistic about the confirmed words, or — one visit in two, when the reader found the aroma or
  // the aftertaste clear and this kind of coffee is known for it — the comparison within the same roast
  const structure =
    seed % 2 === 0
      ? structureNote(result, options.answers ?? {}, locale, seed)
      : null;
  const data = structure
    ? [structure]
    : supportNotes(result, picks, locale, seed, 1);
  const science: ScienceLine[] = [
    referenceNote(result, locale, seed),
    ...data,
    ...(literature
      ? [
          literature.textAlt && (seed >> 2) % 2 === 1
            ? { ...literature, text: literature.textAlt }
            : literature,
        ]
      : []),
    descriptionNote(
      result,
      picks,
      evaluation,
      locale,
      seed,
      options.secondLook ?? [],
    ),
    ...(papery ? [papery] : []),
  ];
  return {
    picked: picks.map((w) => w.text),
    evaluation,
    science,
    cardNote: cardNote(result, picks, evaluation, locale),
    closing: flow.closing[locale],
    profileTitle: confirmed
      ? confirmed.profile.owner_name[locale] || confirmed.profile.owner_name.en
      : null,
    profileId: confirmed ? confirmed.profile.profile_id : null,
  };
}

export const questionFlow = flow;
export const dimensionCount = N;

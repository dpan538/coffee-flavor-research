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
  calibrationLine,
  corpusLine,
  defectNote,
  referenceBasisLine,
  textSeed,
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

const flow = bundle.question_flow;
const presentation = bundle.presentation;

export type Slot = "Q0" | "Q1" | "Q2" | "Q3" | "Q4" | "Q5";
export const SLOTS = flow.slots.map((s) => s.slot as Slot);
export type FlowAnswers = Partial<Record<Slot, string>>;
export type CoherenceLevel = "coherent" | "mild" | "severe";
export type CoherenceCheck = {
  between: [string, string];
  similarity: number;
  level: CoherenceLevel;
  paradox?: boolean;
};
export type FlowPath = 1 | 2 | 3 | 4;
export type FlowStep = {
  ask: Slot[];
  deliver: boolean;
  path: FlowPath | null;
  checks: CoherenceCheck[];
  escalationEligible: boolean;
  reason: string;
};
export type Word = { text: string; dimension: string };
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

/** Unnormalised increment vector of one answer. */
export function slotVector(slot: Slot, answer: string): Vector {
  const spec =
    (
      bundle.matrix_q[questionOf(slot)] as Record<
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
export function groupVector(answers: FlowAnswers, slots: Slot[]): Vector {
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
export function absentAnswer(answers: FlowAnswers, slot: Slot): boolean {
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
    if (answer) out[questionOf(slot)] = answer;
  }
  return out;
}

/** Which slots to ask next, or deliver the first description; a pure function of the answers so far.
 *  The owner's tree: base pair Q0-Q1 → check Q2-Q3 together against it → Path 1 (Q4 confirm),
 *  Path 2 (Q4 correct, Q5 confirm), Path 3 (Q4-Q5 correct), Path 4 (late mutation after Q4). */
export function flowStep(
  answers: FlowAnswers,
  context?: ContextAnswers,
): FlowStep {
  const has = (s: Slot) => answers[s] !== undefined && answers[s] !== "";
  const missing = (...slots: Slot[]) => slots.filter((s) => !has(s));
  const checks: CoherenceCheck[] = [];
  const ask = (slots: Slot[], reason: string): FlowStep => ({
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
  const g = (slots: Slot[]) => groupVector(answers, slots);

  if (missing("Q0", "Q1").length)
    return ask(missing("Q0", "Q1"), "base perception pair");
  if (missing("Q2", "Q3").length)
    return ask(missing("Q2", "Q3"), "coherence check needs Q2-Q3");
  let c23 = coherence(g(["Q0", "Q1"]), g(["Q2", "Q3"]), ["Q0-Q1", "Q2-Q3"]);
  // owner copy review 2026-09-12: a "not noticeable" answer (empty increment) adds no direction — and Q3 on its own
  // is direction-degenerate (all three body answers point the same way) — so a group holding one cannot claim a
  // severe conflict: absence contradicts nothing. Capped at mild: one more question, never Path 3.
  const absence = (["Q0", "Q1", "Q2"] as Slot[]).some((s) =>
    absentAnswer(answers, s),
  );
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
  return infer(context, perceptionAnswers(answers), options);
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
function rotatedWordList(
  dimension: string,
  locale: Locale,
  seed: number,
): string[] {
  const owned =
    (presentation.dimension_tags as Record<string, Record<Locale, string[]>>)[
      dimension
    ]?.[locale] ?? [];
  const consumer =
    (presentation.consumer_terms as Record<string, Record<Locale, string[]>>)[
      dimension
    ]?.[locale] ?? [];
  const offset = owned.length
    ? (seed + DIMENSIONS.indexOf(dimension)) % owned.length
    : 0;
  const rotated = owned.map((_, i) => owned[(offset + i) % owned.length]!);
  return [...rotated, ...consumer];
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
 * varies between cups; both languages stay aligned position by position.
 */
export function describe(result: InferenceResult, locale: Locale): Description {
  const { main, secondary } = flow.first_description;
  const total = main + secondary;
  // candidate dimensions only: the evaluation dimensions never supply pick words (owner, 2026-09-17)
  const ranked = DIMENSIONS.map((d, i) => ({ d, w: result.vTarget[i] ?? 0 }))
    .filter((x) => x.w > 0 && dimensionRole(x.d) === "candidate")
    .sort((a, b) => b.w - a.w);
  const seed = wordSeed(result);
  const lists = new Map(
    ranked.map((x) => [x.d, rotatedWordList(x.d, locale, seed)] as const),
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
    const size = lists.get(x.d)?.length ?? 0;
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
    words.push({ text: list[i]!, dimension: d });
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
  // reading order: the first word of every dimension present (rank order) before any dimension's second word, so the
  // first `pick_count` positions span as many dimensions as the card holds; the set of words is unchanged
  const ordered: Word[] = [];
  const seen = new Set<string>();
  for (const w of words) {
    if (seen.has(w.dimension)) continue;
    seen.add(w.dimension);
    ordered.push(w);
  }
  for (const w of words) if (!ordered.includes(w)) ordered.push(w);
  const prompt =
    locale === "zh-CN"
      ? `选出最贴近你感受的 ${flow.first_description.pick_count} 个词。`
      : `Pick the ${flow.first_description.pick_count} words closest to what you tasted.`;
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
  for (const w of picks) {
    const i = DIMENSIONS.indexOf(w.dimension);
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
      text: wordLists(x.dimension, locale)[0] ?? x.dimension,
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
): FinalCard {
  // owner copy review 2 (2026-09-12): the initial reference (computed, said once), the first sourced research
  // reference that applies, the difference line; the owner's causal sentences are project rules, not card copy
  const science: ScienceLine[] = [];
  const basis = referenceBasisLine(result, locale);
  if (basis) science.push(basis);
  // the second line varies with the cup, the answers and the confirmed words (owner: not the same text every time):
  // a research reference (one of those that apply, in one of its two phrasings) or a data-count line, alternating
  const seed = textSeed([
    ...picks.map((w) => w.text),
    JSON.stringify(result.context),
    ...result.vUser.map((x) => x.toFixed(2)),
  ]);
  const literatureLines = statementsFor(result.context, locale).filter(
    (l) => l.evidenceState === "LITERATURE_CLAIM",
  );
  const data = corpusLine(result.context, locale, seed >> 3);
  const pickLiterature =
    literatureLines.length > 0 && (!data || (seed >> 1) % 3 !== 0);
  if (pickLiterature) {
    const line = literatureLines[seed % literatureLines.length]!;
    science.push(
      line.textAlt && (seed >> 2) % 2 === 1
        ? { ...line, text: line.textAlt }
        : line,
    );
  } else if (data) {
    science.push(data);
  }
  const [top, second] = result.topDeltaDimensions;
  if (top && Math.abs(top.delta) >= 0.1)
    science.push(
      calibrationLine(
        top.dimension,
        top.delta,
        locale,
        seed,
        second && Math.abs(second.delta) >= 0.1 ? second : undefined,
      ),
    );
  const confirmed = confirmedProfile(result, picks);
  // the papery / stale group (owner copy review 2026-09-12): the words are shown, a second sip is suggested, no quality verdict
  if (
    confirmed &&
    (confirmed.profile as { anchor_id?: string }).anchor_id === "anchor-16"
  ) {
    const note = defectNote(locale);
    if (note) science.push(note);
  }
  return {
    picked: picks.map((w) => w.text),
    evaluation: evaluate(result, locale),
    science,
    closing: flow.closing[locale],
    profileTitle: confirmed
      ? confirmed.profile.owner_name[locale] || confirmed.profile.owner_name.en
      : null,
    profileId: confirmed ? confirmed.profile.profile_id : null,
  };
}

export const questionFlow = flow;
export const dimensionCount = N;

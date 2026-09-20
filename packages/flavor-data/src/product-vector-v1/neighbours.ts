/**
 * Words for the slots the reader gave no signal for (owner, 2026-09-20, R3-D47).
 *
 * When the reader's answers point to a kind of flavor, their answer chooses the words (R3-D42, dynamicBank.wordHints).
 * For every other dimension on the card the word comes from the cup's rotation — so a word that is evident for this
 * kind of coffee shows up on one card and not on the next. Here the sixty records nearest to V_target say which words
 * are DISTINCTIVE of coffees like this one: a concept counts only when at least `support` of the neighbourhood
 * mentions it AND that rate is at least `lift` times its rate over all records. Such a word leads its dimension
 * (flow.rotatedWordList); everything else keeps the rotation.
 *
 * Owner's rule: this steadies candidates that are evident but fluctuate; it must not reinforce candidates that are
 * strong everywhere (orange, cocoa, cedar are in a fifth of all records) — ranking by the plain share put orange on
 * 75% of enumerated cards and would skew every card the same way. Measured on 500 + 500 simulated cups
 * (docs/product/QUESTION_FLOW_SIMULATION.md); letting the neighbours choose EVERY word loses 17 points of precision,
 * the reader's own answers carry more information than what similar coffees are called.
 *
 * The index (db/scripts/build-neighbour-index.py) holds a quantised vector and concept indices per record and nothing
 * else: no id, name, source, text or score. A record is evidence for a word, never a coffee the app names.
 * A pure function of V_target: both languages, edits and replays get the same order.
 */
import index from "../../../../db/data/product-vector-v1/product-vector-v1-neighbours.json" with { type: "json" };

type WordConcept = { exact: number } | { family: number[] } | null;

const DIMENSION_COUNT = index.dimensions.length;
const RECORDS = index.records;
const decode = (text: string): Uint8Array =>
  Uint8Array.from(atob(text), (c) => c.charCodeAt(0));
const vectors = decode(index.vectors);
const mentions = decode(index.mentions);
const norms = new Float64Array(RECORDS);
const offsets = new Uint32Array(RECORDS + 1);
for (let r = 0, at = 0; r < RECORDS; r += 1) {
  let sum = 0;
  for (let d = 0; d < DIMENSION_COUNT; d += 1)
    sum += vectors[r * DIMENSION_COUNT + d]! ** 2;
  norms[r] = Math.sqrt(sum) || 1;
  offsets[r] = at;
  at += 1 + mentions[at]!;
  offsets[r + 1] = at;
}

let last: { key: string; scores: Record<string, number[]> | null } | null =
  null;

/** dimension → a score per word (by the word's index in the dimension's list), 0 for a word that is not distinctive
 *  of this cup's neighbourhood; null when there is nothing to go by. */
export function neighbourWordScores(
  target: readonly number[],
): Record<string, number[]> | null {
  const key = target.join(",");
  if (last?.key === key) return last.scores;
  const scores = compute(target);
  last = { key, scores };
  return scores;
}

function compute(target: readonly number[]): Record<string, number[]> | null {
  const length = Math.sqrt(target.reduce((s, x) => s + x * x, 0));
  if (!RECORDS || !length) return null;
  const similarity = new Float64Array(RECORDS);
  for (let r = 0; r < RECORDS; r += 1) {
    let dot = 0;
    for (let d = 0; d < DIMENSION_COUNT; d += 1)
      dot += vectors[r * DIMENSION_COUNT + d]! * (target[d] ?? 0);
    similarity[r] = dot / (norms[r]! * length);
  }
  const nearest = Array.from({ length: RECORDS }, (_, r) => r)
    .sort((a, b) => similarity[b]! - similarity[a]! || a - b)
    .slice(0, index.neighbours);
  // the share of the neighbourhood that mentions a concept, nearer records counting for more
  const share = new Float64Array(index.concepts.length);
  let total = 0;
  for (const r of nearest) {
    const weight = Math.max(0, similarity[r]!) ** index.power;
    total += weight;
    for (let i = offsets[r]! + 1; i < offsets[r + 1]!; i += 1)
      share[mentions[i]!]! += weight;
  }
  if (!total) return null;
  // distinctive: mentioned by enough of the neighbourhood, and clearly more often than over all records
  const distinct = Array.from(share, (weight, c) => {
    const here = weight / total;
    const everywhere = index.concept_share[c] ?? 0;
    const ratio = everywhere > 0 ? here / everywhere : 0;
    return here >= index.support && ratio >= index.lift ? ratio : 0;
  });
  const out: Record<string, number[]> = {};
  for (const [dimension, words] of Object.entries(
    index.word_concepts as Record<string, WordConcept[]>,
  ))
    out[dimension] = words.map((word) =>
      !word
        ? 0
        : "exact" in word
          ? distinct[word.exact]!
          : (index.family_weight *
              word.family.reduce((s, c) => s + distinct[c]!, 0)) /
            word.family.length,
    );
  return out;
}

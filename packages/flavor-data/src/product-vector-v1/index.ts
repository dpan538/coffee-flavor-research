/**
 * product-vector-v1 — the runtime engine of docs/product/FLAVOR_VECTOR_DESIGN_V1.md.
 *
 * One projection matrix, a set of vectors and a cosine. Pure functions over the
 * committed bundle db/data/product-vector-v1/product-vector-v1.json; no server,
 * no training, no model file. Every score is a cosine similarity: a shape
 * comparison in [-1, 1], never a probability.
 *
 *   V_pred   = normalize( K[C0] + K[C1] + K[C2_variety] + K[C2_process] )
 *   V_user   = normalize( Σ Q[question][answer] )
 *   ΔV       = V_user − V_pred
 *   V_target = normalize( V_pred + α · ΔV )
 *   output   = profiles ranked by Sim(V_target, centroid), then beans ranked by Sim(V_target, V_bean)
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };

export const DIMENSIONS = bundle.dimensions as readonly string[];
export type Dimension = (typeof DIMENSIONS)[number];
export type Vector = number[];

export type ContextAnswers = {
  c0_preparation?: string; // pour_over_v60 | french_press | espresso | cold_brew
  c1_roast?: string; // light | medium_light | medium | medium_dark | dark | very_dark
  c2_variety?: string; // gesha | bourbon | ... (Matrix_K rows with corpus support)
  c2_process?: string; // washed | natural | anaerobic | decaf
};
export type PerceptionAnswers = Partial<Record<keyof typeof bundle.matrix_q, string>>;

export type Profile = (typeof bundle.profiles)[number];
export type BeanVector = { id: string; label: string; vector: Vector; source: "benchmark" | "user" };

export type ContextBasis = { axis: string; option: string; basis: string; memberCount: number | null };

export type InferenceResult = {
  vPred: Vector;
  vUser: Vector;
  deltaV: Vector;
  vTarget: Vector;
  alpha: number;
  contextBasis: ContextBasis[];
  similarityUserPred: number;
  profiles: Array<{ profile: Profile; similarity: number }>;
  beans: Array<{ bean: BeanVector; similarity: number }>;
  topDeltaDimensions: Array<{ dimension: string; delta: number }>;
  scoreSemantics: string;
};

const N = DIMENSIONS.length;

export function zero(): Vector {
  return new Array(N).fill(0);
}

export function norm(v: Vector): number {
  return Math.sqrt(v.reduce((acc, x) => acc + x * x, 0));
}

export function normalize(v: Vector): Vector {
  const n = norm(v);
  return n === 0 ? zero() : v.map((x) => x / n);
}

export function add(a: Vector, b: Vector): Vector {
  return a.map((x, i) => x + (b[i] ?? 0));
}

export function cosine(a: Vector, b: Vector): number {
  const na = norm(a);
  const nb = norm(b);
  if (na === 0 || nb === 0) return 0;
  let dot = 0;
  for (let i = 0; i < N; i += 1) dot += (a[i] ?? 0) * (b[i] ?? 0);
  return dot / (na * nb);
}

function increments(spec: Record<string, number>): Vector {
  const v = zero();
  for (const [dim, inc] of Object.entries(spec)) {
    const i = DIMENSIONS.indexOf(dim);
    if (i >= 0) v[i] = inc;
  }
  return v;
}

type KRow = { vector: number[] | null; basis: string; member_count: number | null };

function kRow(axis: keyof typeof bundle.matrix_k, option: string | undefined): { row: KRow | null; basis: ContextBasis | null } {
  if (!option) return { row: null, basis: null };
  const table = bundle.matrix_k[axis] as Record<string, KRow>;
  const row = table[option];
  if (!row) return { row: null, basis: { axis, option, basis: "UNKNOWN_OPTION", memberCount: null } };
  return { row, basis: { axis, option, basis: row.basis, memberCount: row.member_count } };
}

/** Theoretical flavor vector for a context; options without a corpus row contribute nothing and are reported. */
export function buildVPred(context: ContextAnswers): { vPred: Vector; contextBasis: ContextBasis[] } {
  let sum = zero();
  const contextBasis: ContextBasis[] = [];
  const parts: Array<[keyof typeof bundle.matrix_k, string | undefined]> = [
    ["C0", context.c0_preparation],
    ["C1", context.c1_roast],
    ["C2_variety", context.c2_variety],
    ["C2_process", context.c2_process],
  ];
  for (const [axis, option] of parts) {
    const { row, basis } = kRow(axis, option);
    if (basis) contextBasis.push(basis);
    if (row?.vector) sum = add(sum, row.vector);
  }
  return { vPred: normalize(sum), contextBasis };
}

/** Perceived flavor vector from Q5–Q10; unanswered questions add nothing. */
export function buildVUser(answers: PerceptionAnswers): Vector {
  let sum = zero();
  for (const [question, options] of Object.entries(bundle.matrix_q)) {
    const answer = answers[question as keyof typeof bundle.matrix_q];
    if (!answer) continue;
    const spec = (options as Record<string, Record<string, number>>)[answer];
    if (spec) sum = add(sum, increments(spec));
  }
  return normalize(sum);
}

export function deltaV(vUser: Vector, vPred: Vector): Vector {
  return vUser.map((x, i) => x - (vPred[i] ?? 0));
}

export function vTarget(vPred: Vector, delta: Vector, alpha = bundle.alpha_default): Vector {
  return normalize(vPred.map((x, i) => x + alpha * (delta[i] ?? 0)));
}

export function rankProfiles(target: Vector, limit = 3): Array<{ profile: Profile; similarity: number }> {
  return bundle.profiles
    .map((profile) => ({ profile, similarity: cosine(target, profile.centroid) }))
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, limit);
}

export function rankBeans(target: Vector, beans: BeanVector[], limit = 3): Array<{ bean: BeanVector; similarity: number }> {
  return beans
    .map((bean) => ({ bean, similarity: cosine(target, bean.vector) }))
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, limit);
}

/** Project a list of canonical concept ids (a user-entered bean's tasting notes) into the space. */
export function projectConcepts(conceptIds: string[]): Vector {
  let sum = zero();
  const projection = bundle.concept_projection as Record<string, number[]>;
  for (const id of conceptIds) {
    const row = projection[id];
    if (row) sum = add(sum, row);
  }
  return normalize(sum);
}

export function infer(
  context: ContextAnswers,
  answers: PerceptionAnswers,
  options: { alpha?: number; beans?: BeanVector[]; profileLimit?: number; beanLimit?: number } = {},
): InferenceResult {
  const alpha = options.alpha ?? bundle.alpha_default;
  const { vPred, contextBasis } = buildVPred(context);
  const vUser = buildVUser(answers);
  const delta = deltaV(vUser, vPred);
  const target = vTarget(vPred, delta, alpha);
  const topDeltaDimensions = delta
    .map((d, i) => ({ dimension: DIMENSIONS[i] as string, delta: d }))
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, 2);
  return {
    vPred,
    vUser,
    deltaV: delta,
    vTarget: target,
    alpha,
    contextBasis,
    similarityUserPred: cosine(vUser, vPred),
    profiles: rankProfiles(target, options.profileLimit ?? 3),
    beans: rankBeans(target, options.beans ?? [], options.beanLimit ?? 3),
    topDeltaDimensions,
    scoreSemantics: bundle.score_semantics,
  };
}

export const productVectorBundle = bundle;

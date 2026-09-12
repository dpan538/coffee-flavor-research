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
 *
 * Presentation is a separate layer over the same vectors (owner, 2026-09-12): the
 * backend converges on vectors, the UI maps them to words. zh-CN renders the
 * minimalist tag array of the Chinese specialty scene (词 A | 词 B | 词 C | 词 D);
 * en renders the scientific wording. The science line sits behind a fold and
 * carries its evidence_state (OWNER_STATEMENT / CORPUS_MEASURED / LITERATURE_CLAIM).
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };

export const DIMENSIONS = bundle.dimensions as readonly string[];
export type Dimension = (typeof DIMENSIONS)[number];
export type Vector = number[];
export type Locale = "zh-CN" | "en";

export type ContextAnswers = {
  c0_preparation?: string; // pour_over_v60 | french_press | espresso | cold_brew
  c1_roast?: string; // light | medium_light | medium | medium_dark | dark | very_dark
  c2_variety?: string | string[]; // one variety, or a blend of up to 3 (normalised mean of their rows)
  c2_process?: string; // washed | natural | anaerobic | decaf
  c2_origin?: string; // optional macro-region chip (context_rules.origin_regions): a delta-0.1 bias, never required
};
export type PerceptionAnswers = Partial<Record<keyof typeof bundle.matrix_q, string>>;

export type Profile = (typeof bundle.profiles)[number];
export type BeanVector = { id: string; label: string; vector: Vector; source: "benchmark" | "user"; conceptIds?: string[] };

export type ContextBasis = { axis: string; option: string; basis: string; memberCount: number | null };

export type InferenceResult = {
  vPred: Vector;
  vUser: Vector;
  deltaV: Vector;
  vTarget: Vector;
  alpha: number;
  context: ContextAnswers;
  contextBasis: ContextBasis[];
  similarityUserPred: number;
  profiles: Array<{ profile: Profile; similarity: number }>;
  beans: Array<{ bean: BeanVector; similarity: number }>;
  topDeltaDimensions: Array<{ dimension: string; delta: number }>;
  scoreSemantics: string;
};

export type ScienceLine = {
  text: string;
  evidenceState: string;
  citationRef: string;
  about: string;
  sourceTitle: string;
  sourceLicence: string;
  /** consumer-facing label for the evidence state (never the raw enum) */
  label: string;
  /** "参考资料：Coffee Ad Astra (J. Gagné)" for literature; empty for owner statements and the difference line */
  citation: string;
};
export type Presentation = {
  locale: Locale;
  headline: { title: string; tags: string[]; similarity: number; ownerReviewed: boolean; profileId: string } | null;
  alternatives: Array<{ title: string; tags: string[]; similarity: number; profileId: string }>;
  beans: Array<{ label: string; tags: string[]; similarity: number; source: BeanVector["source"] }>;
  science: ScienceLine[];
  scoreSemantics: string;
};

const N = DIMENSIONS.length;
const presentation = bundle.presentation;
const rules = bundle.context_rules;
const AXIS_KEYS: Array<[string, keyof ContextAnswers]> = [
  ["C0", "c0_preparation"],
  ["C1", "c1_roast"],
  ["C2_variety", "c2_variety"],
  ["C2_process", "c2_process"],
];

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

export function dot(a: Vector, b: Vector): number {
  // vectors of any length (12-dimension flavor vectors, 16-entry profile signatures)
  let sum = 0;
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i += 1) sum += (a[i] ?? 0) * (b[i] ?? 0);
  return sum;
}

export function cosine(a: Vector, b: Vector): number {
  const na = norm(a);
  const nb = norm(b);
  if (na === 0 || nb === 0) return 0;
  return dot(a, b) / (na * nb);
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
  for (const [axis, key] of AXIS_KEYS) {
    if (key === "c2_variety") {
      // blend (owner R3-D13): V_blend = normalize(Σ V_variety_i), at most max_varieties
      const raw = context.c2_variety;
      const varieties = (Array.isArray(raw) ? raw : raw ? [raw] : []).slice(0, rules.blend.max_varieties);
      let blend = zero();
      let members = 0;
      for (const variety of varieties) {
        const { row, basis } = kRow("C2_variety", variety);
        if (basis) contextBasis.push({ ...basis, basis: varieties.length > 1 ? `${basis.basis};BLEND_MEMBER_${varieties.length}` : basis.basis });
        if (row?.vector) {
          blend = add(blend, row.vector);
          members += 1;
        }
      }
      if (members > 0) sum = add(sum, normalize(blend));
      continue;
    }
    const { row, basis } = kRow(axis as keyof typeof bundle.matrix_k, context[key as keyof ContextAnswers] as string | undefined);
    if (basis) contextBasis.push(basis);
    if (row?.vector) sum = add(sum, row.vector);
  }
  if (context.c2_origin) {
    const region = (rules.origin_regions as Record<string, { bias: string[] }>)[context.c2_origin];
    if (region) {
      const unit = normalize(sum.some((x) => x !== 0) ? sum : zero());
      const biased = unit.map((x, i) => x + (region.bias.includes(DIMENSIONS[i] as string) ? rules.origin_bias_delta : 0));
      sum = biased;
      contextBasis.push({ axis: "C2_origin", option: context.c2_origin, basis: `ORIGIN_BIAS_DELTA_${rules.origin_bias_delta}_ON_${region.bias.join("+")}`, memberCount: null });
    } else {
      contextBasis.push({ axis: "C2_origin", option: context.c2_origin, basis: "UNKNOWN_OPTION", memberCount: null });
    }
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
    context,
    contextBasis,
    similarityUserPred: cosine(vUser, vPred),
    profiles: rankProfiles(target, options.profileLimit ?? 3),
    beans: rankBeans(target, options.beans ?? [], options.beanLimit ?? 3),
    topDeltaDimensions,
    scoreSemantics: bundle.score_semantics,
  };
}

// ---------------------------------------------------------------- presentation layer

type Localized = { "zh-CN": string; en: string };
type LocalizedList = { "zh-CN": string[]; en: string[] };
const DIM_THRESHOLD = 0.15;
const DEFECT_DOMINANCE = 0.5;

/**
 * Minimalist tags for a vector (owner's displayTags rules, 2026-09-12).
 *  priority 1 — with concept ids (a bean with tasting notes): the concrete words, ranked by the
 *               concept's projection weight against the vector, top 3–4;
 *  priority 2 — with a bare vector (a profile centroid): dominant dimensions above the threshold,
 *               each mapped to the first unused word of its CN/EN tag list;
 *  defect guard — defect words appear only when defect dominates the vector.
 */
export function displayTags(vector: Vector, locale: Locale, count = presentation.tag_count, conceptIds?: string[]): string[] {
  const dimTags = presentation.dimension_tags as Record<string, LocalizedList>;
  const conceptTags = presentation.concept_tags as Record<string, Localized>;
  const projection = bundle.concept_projection as Record<string, number[]>;
  const defectIndex = DIMENSIONS.indexOf("defect");
  const defectDominates = (vector[defectIndex] ?? 0) >= DEFECT_DOMINANCE;
  const tags: string[] = [];
  const push = (tag: string | undefined) => {
    if (tag && !tags.includes(tag)) tags.push(tag);
  };
  if (conceptIds?.length) {
    const ranked = conceptIds
      .filter((id) => projection[id])
      .filter((id) => defectDominates || (projection[id]![defectIndex] ?? 0) < DEFECT_DOMINANCE)
      .map((id) => ({ id, w: dot(projection[id]!, vector) }))
      .filter((x) => x.w > 0)
      .sort((a, b) => b.w - a.w);
    for (const { id } of ranked) {
      if (tags.length >= count) break;
      push(conceptTags[id]?.[locale]);
    }
  }
  if (tags.length < count) {
    const dims = DIMENSIONS.map((d, i) => ({ d, w: vector[i] ?? 0 }))
      .filter((x) => x.w > DIM_THRESHOLD && (x.d !== "defect" || defectDominates))
      .sort((a, b) => b.w - a.w);
    for (const { d } of dims) {
      if (tags.length >= count) break;
      const list = dimTags[d]?.[locale] ?? [];
      push(list.find((t) => !tags.includes(t)));
    }
  }
  return tags;
}

type SourceRow = { source_id: string; title: string; locator: string; licence_note: string; terms_short?: string; use?: string; claims: number; state: string };
type PresentationExtras = {
  evidence_labels?: Record<string, Record<Locale, string>>;
  delta_templates?: Record<Locale, { pos: string; neg: string; pos_variants?: string[]; neg_variants?: string[]; pair_variants?: string[] }>;
  citation_prefix?: Record<Locale, string>;
  card_heading?: Record<Locale, string>;
  science_heading?: Record<Locale, string>;
  displayable_evidence_states?: string[];
  defect_note?: Record<Locale, string>;
  reference_basis_templates?: Record<Locale, { text: string; explain: string; join: string; context_join: string }>;
  context_labels?: Record<string, Record<Locale, string>>;
};

/** UI label of a context option (bundle presentation.context_labels; the raw key when unknown). */
export function contextLabel(option: string, locale: Locale): string {
  return (presentation as PresentationExtras).context_labels?.[option]?.[locale] ?? option;
}

/** The initial reference, said once (owner copy review 2, 2026-09-12): which inputs it came from and which
 *  features it leans toward — computed from V_pred, so it is a statement about the reference, not about the cup. */
export function referenceBasisLine(result: { vPred: Vector; context: ContextAnswers }, locale: Locale): ScienceLine | null {
  const t = (presentation as PresentationExtras).reference_basis_templates?.[locale];
  if (!t) return null;
  const parts: string[] = [];
  for (const [, key] of AXIS_KEYS) {
    const value = result.context[key];
    for (const v of Array.isArray(value) ? value : value ? [value] : []) parts.push(contextLabel(v, locale));
  }
  if (result.context.c2_origin) {
    const region = (rules.origin_regions as Record<string, { label: Record<Locale, string> }>)[result.context.c2_origin];
    if (region) parts.push(region.label[locale]);
  }
  const labels = presentation.dimension_labels as Record<string, Record<Locale, string>>;
  const dims = DIMENSIONS.map((d, i) => ({ d, w: result.vPred[i] ?? 0 })).filter((x) => x.w > 0.15).sort((a, b) => b.w - a.w).slice(0, 3).map((x) => labels[x.d]?.[locale] ?? x.d);
  if (!parts.length || !dims.length) return null;
  const text = `${t.text.replace("{context}", parts.join(t.context_join)).replace("{dims}", dims.join(t.join))} ${t.explain}`;
  return { text, evidenceState: "REFERENCE_BASIS", citationRef: "engine: V_pred = normalize(Σ K)", about: "reference_basis", sourceTitle: "engine", sourceLicence: "", label: evidenceLabel("REFERENCE_BASIS", locale), citation: "" };
}

/** Evidence states a user may see (owner copy review 2026-09-12): a claim pending a locator or re-verification is declared in the data but never shown. */
export function displayableEvidenceStates(): string[] {
  return (presentation as PresentationExtras).displayable_evidence_states ?? Object.keys((presentation as PresentationExtras).evidence_labels ?? {});
}

/** The note for the papery / stale group: show the words, ask for a second sip, judge nothing. */
export function defectNote(locale: Locale): ScienceLine | null {
  const text = (presentation as PresentationExtras).defect_note?.[locale];
  if (!text) return null;
  return { text, evidenceState: "PRODUCT_NOTE", citationRef: "owner copy review 2026-09-12", about: "defect_note", sourceTitle: "owner", sourceLicence: "", label: evidenceLabel("PRODUCT_NOTE", locale), citation: "" };
}

/** consumer-facing label for an evidence state ("研究参考"), never the raw enum */
export function evidenceLabel(state: string, locale: Locale): string {
  return (presentation as PresentationExtras).evidence_labels?.[state]?.[locale] ?? "";
}

/** "World Coffee Research — Sensory Lexicon / Varieties Catalog" → "World Coffee Research"; "Coffee Ad Astra (Jonathan Gagné) — …" → "Coffee Ad Astra (J. Gagné)" */
export function shortSource(title: string): string {
  const head = title.split(" — ")[0]!.trim();
  return head.replace("(Jonathan Gagné)", "(J. Gagné)");
}

/** A small deterministic seed so the wording varies from card to card (owner) without being random on re-render. */
export function textSeed(parts: string[]): number {
  let h = 7;
  for (const p of parts) for (const ch of p) h = (h * 31 + ch.charCodeAt(0)) % 100003;
  return h;
}

/** the difference line for a delta dimension; `seed` picks a wording, `second` (opposite sign) makes it a pair */
export function calibrationLine(dimension: string, delta: number, locale: Locale, seed = 0, second?: { dimension: string; delta: number }): ScienceLine {
  const labels = presentation.dimension_labels as Record<string, Record<Locale, string>>;
  const label = labels[dimension]?.[locale] ?? dimension;
  const templates = (presentation as PresentationExtras).delta_templates?.[locale];
  const words = presentation.delta_words[locale];
  let text: string;
  if (templates) {
    const pairs = templates.pair_variants ?? [];
    const single = (delta > 0 ? templates.pos_variants : templates.neg_variants) ?? [delta > 0 ? templates.pos : templates.neg];
    const usePair = !!second && delta > 0 && second.delta < 0 && pairs.length > 0 && seed % 3 === 2;
    text = usePair
      ? pairs[seed % pairs.length]!.replace("{label}", label).replace("{label2}", labels[second!.dimension]?.[locale] ?? second!.dimension)
      : single[seed % single.length]!.replace("{label}", label);
  } else {
    text = locale === "zh-CN" ? `你感受到的${label}${delta > 0 ? words.pos : words.neg}。` : `Your ${label} reads ${delta > 0 ? words.pos : words.neg}.`;
  }
  return { text, evidenceState: "COMPUTED_DELTA", citationRef: "engine: V_user − V_pred", about: `delta:${dimension}`, sourceTitle: "engine", sourceLicence: "", label: evidenceLabel("COMPUTED_DELTA", locale), citation: "" };
}

export function cardCopy(locale: Locale): { heading: string; science: string } {
  const extras = presentation as PresentationExtras;
  return { heading: extras.card_heading?.[locale] ?? "", science: extras.science_heading?.[locale] ?? "" };
}
/** Short licence label for a source id ("CC BY-SA 4.0"), from the bundle's source registry; empty for owner statements. */
export function sourceLicence(sourceId: string): string {
  const registry = ((presentation as { sources?: SourceRow[] }).sources ?? []) as SourceRow[];
  const row = registry.find((r) => r.source_id === sourceId);
  if (!row?.licence_note) return "";
  if (row.terms_short) return row.terms_short;
  const cc = row.licence_note.match(/\(CC [A-Z-]+ [0-9.]+\)/);
  return cc ? cc[0].slice(1, -1) : row.licence_note.split(" — ")[0]!.split(" (")[0]!;
}

/** Context statements whose parts are all answered, most specific (most parts) first. */
export function statementsFor(context: ContextAnswers, locale: Locale): ScienceLine[] {
  const answered = new Map<string, Set<string>>();
  for (const [axis, key] of AXIS_KEYS) {
    const value = context[key];
    const values = Array.isArray(value) ? value : value ? [value] : [];
    if (values.length) answered.set(axis, new Set(values));
  }
  const visible = new Set(displayableEvidenceStates());
  return presentation.context_statements
    .filter((s) => visible.has(s.evidence_state) && s.parts.length > 0 && s.parts.every((p) => answered.get(p.axis)?.has(p.option)))
    .sort((a, b) => b.parts.length - a.parts.length)
    .map((s) => {
      const title = (s as { source_title?: string }).source_title ?? s.source_id;
      const literature = s.evidence_state.startsWith("LITERATURE_CLAIM");
      return {
        text: s[locale],
        evidenceState: s.evidence_state,
        citationRef: s.citation_ref,
        about: s.context_id,
        sourceTitle: title,
        sourceLicence: sourceLicence(s.source_id),
        label: evidenceLabel(s.evidence_state, locale),
        citation: literature ? `${(presentation as PresentationExtras).citation_prefix?.[locale] ?? ""}${shortSource(title)}` : "",
      };
    });
}

/** Locale-aware rendering of an inference: headline profile + tags, alternatives, beans, and the science fold. */
export function present(result: InferenceResult, locale: Locale): Presentation {
  const labels = presentation.dimension_labels as Record<string, Localized>;
  const words = presentation.delta_words[locale];
  const toHeadline = (entry: { profile: Profile; similarity: number }) => {
    const name = entry.profile.owner_name[locale] || entry.profile.owner_name.en || entry.profile.profile_id;
    const owned = entry.profile.display_tags[locale];
    const tags = owned.length ? owned.slice(0, presentation.tag_count) : displayTags(entry.profile.centroid, locale);
    return { title: name, tags, similarity: entry.similarity, ownerReviewed: entry.profile.owner_reviewed, profileId: entry.profile.profile_id };
  };
  const [first, ...rest] = result.profiles;
  const basis = referenceBasisLine(result, locale);
  const science: ScienceLine[] = [...(basis ? [basis] : []), ...statementsFor(result.context, locale)];
  for (const { dimension, delta } of result.topDeltaDimensions) {
    if (Math.abs(delta) < 0.1) continue;
    science.push(calibrationLine(dimension, delta, locale));
  }
  return {
    locale,
    headline: first ? toHeadline(first) : null,
    alternatives: rest.map((entry) => {
      const h = toHeadline(entry);
      return { title: h.title, tags: h.tags, similarity: h.similarity, profileId: h.profileId };
    }),
    beans: result.beans.map(({ bean, similarity }) => ({
      label: bean.label,
      tags: displayTags(bean.vector, locale, presentation.tag_count, bean.conceptIds),
      similarity,
      source: bean.source,
    })),
    science,
    scoreSemantics: result.scoreSemantics,
  };
}

export const productVectorBundle = bundle;

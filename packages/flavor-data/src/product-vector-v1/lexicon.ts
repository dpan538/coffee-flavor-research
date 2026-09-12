/**
 * Hybrid utterance mapper (owner spec, 2026-09-12): consumer language → Q0–Q5 answers.
 *
 *   [utterance] → negation-prefix scan ("不酸" must not read as "酸")
 *               → direction-sensitive questions (Q0 acidity, Q1 aroma, Q2 sweetness, Q5 complexity):
 *                   cosine of the utterance vector, restricted to the question's dimensions, against each option
 *               → parallel / magnitude questions (Q3 body, Q4 bitterness): cue-word hits
 *               → hybrid score = alpha · cosine + beta · cueHits, per option; best option wins if it clears the floor
 *   Negation forcing: "不苦 / 毫无苦味" → Q4-B; "不酸 / 怕酸" → Q0-C, before any vector projection.
 *
 * The utterance vector is built from the same vocabulary the presentation layer speaks: consumer terms
 * (CN_CONSUMER_FLAVOR_LEXICON), concept tags (projection rows) and dimension tag lists.
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };
import {
  DIMENSIONS,
  add,
  cosine,
  normalize,
  zero,
  type Locale,
  type Vector,
} from "./engine";
import { slotVector, type FlowAnswers, type Slot } from "./flow";

const presentation = bundle.presentation;
const mapper = bundle.question_flow.utterance_mapper;
const bank = bundle.question_bank as Record<
  string,
  {
    question: string;
    options: Record<
      string,
      { label: Record<Locale, string>; cues: Record<Locale, string[]> }
    >;
  }
>;

export type MatchedTerm = {
  term: string;
  dimension?: string;
  concept?: string;
  negated: boolean;
};
export type OptionScore = {
  option: string;
  cosine: number;
  cueHits: number;
  score: number;
  forced: boolean;
};
export type UtteranceMapping = {
  vector: Vector;
  matched: MatchedTerm[];
  answers: FlowAnswers;
  scores: Partial<Record<Slot, OptionScore[]>>;
  forced: Partial<Record<Slot, string>>;
};

function isNegated(text: string, index: number, locale: Locale): boolean {
  const window = text.slice(Math.max(0, index - 6), index);
  return mapper.negation_prefixes[locale].some(
    (prefix) => window.endsWith(prefix) || window.endsWith(prefix.trim()),
  );
}

function occurrences(text: string, term: string): number[] {
  const hits: number[] = [];
  if (!term) return hits;
  let from = 0;
  const haystack = text.toLowerCase();
  const needle = term.toLowerCase();
  for (;;) {
    const i = haystack.indexOf(needle, from);
    if (i < 0) return hits;
    hits.push(i);
    from = i + needle.length;
  }
}

/** Vector of an utterance from the shared vocabulary; negated terms are recorded but add nothing. */
export function utteranceVector(
  text: string,
  locale: Locale,
): { vector: Vector; matched: MatchedTerm[] } {
  let sum = zero();
  const matched: MatchedTerm[] = [];
  const projection = bundle.concept_projection as Record<string, number[]>;
  const conceptTags = presentation.concept_tags as Record<
    string,
    Record<Locale, string>
  >;
  // the mapper hears every lexicon term (including structural words such as "thin" / "watery");
  // the card only prints the display-eligible ones (presentation.consumer_terms)
  const consumer = ((presentation as { mapper_terms?: unknown }).mapper_terms ??
    presentation.consumer_terms) as Record<string, Record<Locale, string[]>>;
  const dimTags = presentation.dimension_tags as Record<
    string,
    Record<Locale, string[]>
  >;
  const unit = (dimension: string) => {
    const v = zero();
    const i = DIMENSIONS.indexOf(dimension);
    if (i >= 0) v[i] = 1;
    return v;
  };
  const consider = (
    term: string,
    vec: Vector,
    meta: Omit<MatchedTerm, "term" | "negated">,
  ) => {
    for (const index of occurrences(text, term)) {
      const negated = isNegated(text, index, locale);
      matched.push({ term, negated, ...meta });
      if (!negated) sum = add(sum, vec);
    }
  };
  const mapperSurface = new Set(
    Object.values(consumer).flatMap((terms) =>
      (terms[locale] ?? []).map((t) => t.toLowerCase()),
    ),
  );
  // a lexicon term overrides a concept tag with the same surface text (owner: "vinegar" is a negative filter, not a fermented note)
  for (const [concept, tags] of Object.entries(conceptTags)) {
    if (mapperSurface.has(tags[locale].toLowerCase())) continue;
    consider(tags[locale], projection[concept] ?? zero(), { concept });
  }
  for (const [dimension, terms] of Object.entries(consumer))
    for (const term of terms[locale] ?? [])
      consider(term, unit(dimension), { dimension });
  for (const [dimension, terms] of Object.entries(dimTags))
    for (const term of terms[locale] ?? [])
      consider(term, unit(dimension), { dimension });
  return { vector: normalize(sum), matched };
}

function questionDimensions(slot: Slot): number[] {
  const dims = new Set<number>();
  for (const option of Object.keys(bank[slot]!.options)) {
    slotVector(slot, option).forEach((x, i) => {
      if (x > 0) dims.add(i);
    });
  }
  return [...dims];
}

function restrict(vector: Vector, indices: number[]): Vector {
  const v = zero();
  for (const i of indices) v[i] = vector[i] ?? 0;
  return v;
}

/** Map an utterance to Q0–Q5 answers with the hybrid score; questions without evidence stay unanswered. */
export function mapUtterance(text: string, locale: Locale): UtteranceMapping {
  const { vector, matched } = utteranceVector(text, locale);
  const answers: FlowAnswers = {};
  const scores: Partial<Record<Slot, OptionScore[]>> = {};
  const forced: Partial<Record<Slot, string>> = {};
  // negation forcing first
  const forcing = mapper.forced_by_negation[locale] as unknown as Record<
    string,
    [string, string]
  >;
  for (const [word, [slot, option]] of Object.entries(forcing)) {
    const negatedAt = occurrences(text, word).filter((index) =>
      isNegated(text, index, locale),
    );
    if (negatedAt.length) {
      forced[slot as Slot] = option;
      answers[slot as Slot] = option;
      matched.push({
        term: word,
        negated: true,
        dimension:
          (
            { Q4: "bitter_roasted", Q0: "acidity", Q2: "sweetness" } as Record<
              string,
              string
            >
          )[slot] ?? "acidity",
      });
    }
  }
  for (const slot of Object.keys(bank) as Slot[]) {
    const options = bank[slot]!.options;
    const dims = questionDimensions(slot);
    const projected = restrict(vector, dims);
    const projectionMass = Math.sqrt(
      projected.reduce((acc, x) => acc + x * x, 0),
    );
    const direction = mapper.direction_questions.includes(slot);
    const rows: OptionScore[] = Object.entries(options).map(
      ([option, spec]) => {
        const optionVector = slotVector(slot, option);
        const cos =
          direction &&
          projectionMass >= mapper.min_projection &&
          optionVector.some((x) => x > 0)
            ? cosine(projected, optionVector)
            : 0;
        let cueHits = 0;
        for (const cue of spec.cues[locale] ?? []) {
          for (const index of occurrences(text, cue)) {
            // a cue that itself encodes the negation ("不苦") counts as is; otherwise a negated cue is ignored
            const encodesNegation = mapper.negation_prefixes[locale].some((p) =>
              cue.startsWith(p.trim()),
            );
            if (encodesNegation || !isNegated(text, index, locale)) {
              cueHits += 1;
              matched.push({ term: cue, negated: false });
            }
          }
        }
        const isForced = forced[slot] === option;
        // a negation-forced option outranks every scored option (the guard decides before the vector does)
        return {
          option,
          cosine: cos,
          cueHits,
          score:
            mapper.alpha * cos + mapper.beta * cueHits + (isForced ? 10 : 0),
          forced: isForced,
        };
      },
    );
    rows.sort((a, b) => b.score - a.score);
    scores[slot] = rows;
    if (forced[slot]) continue;
    const best = rows[0]!;
    const evidence =
      best.cueHits > 0 ||
      (direction && projectionMass >= mapper.min_projection && best.cosine > 0);
    if (evidence && best.score > 0) answers[slot] = best.option;
  }
  return { vector, matched, answers, scores, forced };
}

export const utteranceMapper = mapper;

/**
 * The card's notes, "关于这段描述" (owner, 2026-09-18). Three kinds of statement, each with its evidence label:
 *
 *   initial reference  — what the reader's choices mean in the review data: how often a kind of coffee is described
 *                        with a flavor dimension, next to the same frequency across all coffees. It interprets the
 *                        choices instead of repeating them, and says which choices the data cannot speak for.
 *   from the data      — one statistic that bears on the words the reader confirmed: the measured choice (or pair of
 *                        choices) that best supports a confirmed dimension — or, honestly, does not. One note, with
 *                        the conclusion in plain words first and the numbers as "about 5 in 10 … about 3 in 10 across
 *                        all coffees": two notes under the same label read as a bug, and "50% … 27% overall" is not
 *                        something a reader can follow (owner, 2026-09-19).
 *   your description   — what the reader's answers moved against the reference, and which confirmed words come from that.
 *
 * Both languages say the same thing: the statistic, the scope and the phrasing variant are chosen by a seed that
 * contains nothing language-dependent, and every template list has the same length and order in both languages. The
 * seed includes the session's nonce, so the same cup made again may draw a different supporting statistic.
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };
import { structureComparison } from "./dynamicBank";
import {
  DIMENSIONS,
  evidenceLabel,
  shortContextLabel,
  textSeed,
  type ContextAnswers,
  type InferenceResult,
  type Locale,
  type ScienceLine,
} from "./engine";

type Picked = { text: string; dimension: string };
type Stat = { n: number; presence: number[] };
type Templates = Record<string, string | string[]>;

const stats = bundle.corpus_stats as unknown as {
  all: Stat;
  options: Record<string, Record<string, Stat>>;
  pairs: Array<{ a: [string, string]; b: [string, string] } & Stat>;
};
const K = bundle.matrix_k as Record<
  string,
  Record<string, { vector: number[] | null }>
>;
const templatesFor = (locale: Locale): Templates =>
  (bundle.presentation as unknown as { card_notes: Record<Locale, Templates> })
    .card_notes[locale];
const dimensionLabels = bundle.presentation.dimension_labels as Record<
  string,
  Record<Locale, string>
>;

/** dimensions a note may talk about: body is mentioned by nearly every record, and a card never judges quality */
const SILENT = new Set(["body", "defect"]);
const NOTABLE = 0.06; // a choice is worth interpreting when a share differs from the whole by six points
// A statistic supports (or contradicts) a confirmed word from ten points on. The note gives no figures (owner,
// 2026-09-20: "of the 738 coffees about 4 in 10 … against 3" reads as heavy averaging and invites the suspicion of
// over-fitting), so the plain words "more often" must stand on a clear gap: five points were too thin for them.
const LEAN = 0.1;
const COMMONPLACE = 0.9; // a dimension nearly every record mentions cannot support anything
const MOVED = 0.1; // the reader's answers moved a dimension (same bar as the old difference line)
const AXES: Array<[string, keyof ContextAnswers]> = [
  ["C0", "c0_preparation"],
  ["C1", "c1_roast"],
  ["C2_variety", "c2_variety"],
  ["C2_process", "c2_process"],
];

type Choice = { axis: string; option: string };
function choices(context: ContextAnswers): Choice[] {
  const out: Choice[] = [];
  for (const [axis, key] of AXES) {
    const value = context[key];
    for (const option of Array.isArray(value) ? value : value ? [value] : [])
      out.push({ axis, option });
  }
  return out;
}

const dimLabel = (dimension: string, locale: Locale) =>
  dimensionLabels[dimension]?.[locale] ?? dimension;
/** the dimension said so a reader recognises it: the label plus familiar things it covers (presentation.dimension_gloss) */
const dimGloss = (dimension: string, locale: Locale) =>
  (
    bundle.presentation as unknown as {
      dimension_gloss?: Record<Locale, Record<string, string>>;
    }
  ).dimension_gloss?.[locale]?.[dimension] ?? dimLabel(dimension, locale);
/** the dimension as a noun inside a sentence: the gloss without its examples ("花香", "floral notes") */
const dimNoun = (dimension: string, locale: Locale) =>
  dimGloss(dimension, locale).split(/\s*[（(]/)[0]!;
/** an option's name inside a sentence: English lower-cases everything but variety names */
function optionLabel(choice: Choice, locale: Locale): string {
  const label = shortContextLabel(choice.option, locale);
  if (locale !== "en" || choice.axis === "C2_variety") return label;
  const lower = label.charAt(0).toLowerCase() + label.slice(1);
  // "light-roast coffees", not "light coffees"
  return choice.axis === "C1" ? `${lower}-roast` : lower;
}
const variant = (t: Templates, key: string, seed: number): string => {
  const list = t[key] as string[];
  return list[seed % list.length]!;
};
/** "A", "A and B", "A, B and C" — the last joiner differs in English */
const listed = (items: string[], t: Templates): string =>
  items.length < 2
    ? (items[0] ?? "")
    : `${items.slice(0, -1).join(t.join as string)}${t.last_join as string}${items[items.length - 1]!}`;
/** English sentences start with a capital even when they open with a label — also the second sentence of a note */
const sentence = (text: string, locale: Locale): string =>
  locale === "en"
    ? text.replace(
        /(^|[.!?]\s+)([a-z])/g,
        (_, lead: string, letter: string) => lead + letter.toUpperCase(),
      )
    : text;
const fill = (template: string, values: Record<string, string>) =>
  template.replace(
    /\{(\w+)\}/g,
    (whole, name: string) => values[name] ?? whole,
  );

/**
 * A share said as a natural frequency — "about 5 in 10" — and compared with "all coffees": a percentage next to an
 * undefined "overall" is not something a reader can follow (owner, 2026-09-19). Tenths by default; hundredths when the
 * sentence claims a difference that tenths would round away.
 */
function frequency(
  share: number,
  base: number,
  t: Templates,
  again = false,
): string {
  const k = Math.round(share * base);
  const key = `frequency${again ? "_again" : ""}${k < 1 ? "_under" : ""}`;
  return fill(t[key] as string, { k: String(k), base: String(base) });
}
function frequencyPair(
  share: number,
  whole: number,
  differ: boolean,
  t: Templates,
): [string, string] {
  const base =
    differ && Math.round(share * 10) === Math.round(whole * 10) ? 100 : 10;
  return [frequency(share, base, t), frequency(whole, base, t, true)];
}

function line(
  text: string,
  evidenceState: "REFERENCE_BASIS" | "CORPUS_MEASURED" | "COMPUTED_DELTA",
  about: string,
  citationRef: string,
  locale: Locale,
): ScienceLine {
  return {
    text,
    evidenceState,
    citationRef,
    about,
    sourceTitle: evidenceState === "CORPUS_MEASURED" ? "corpus" : "engine",
    sourceLicence: "",
    label: evidenceLabel(evidenceState, locale),
    citation: "",
  };
}

/** nothing in the seed depends on the language: the context, the answers' vector, the confirmed dimensions, the nonce */
export function noteSeed(
  result: InferenceResult,
  picks: Picked[],
  nonce = 0,
): number {
  return textSeed([
    JSON.stringify(result.context),
    ...result.vUser.map((x) => x.toFixed(2)),
    ...picks.map((w) => w.dimension),
    String(nonce),
  ]);
}

/** The initial reference, interpreted: what the measured choices shift against all review records. */
export function referenceNote(
  result: InferenceResult,
  locale: Locale,
  seed: number,
): ScienceLine {
  const t = templatesFor(locale);
  const all = stats.all;
  const chosen = choices(result.context);
  const measured = chosen.filter((c) => stats.options[c.axis]?.[c.option]);
  const leftOut = chosen.filter((c) => K[c.axis]?.[c.option]?.vector === null);

  const readings = measured
    .map((choice) => {
      const stat = stats.options[choice.axis]![choice.option]!;
      const shifts = DIMENSIONS.map((d, i) => ({
        d: d as string,
        i,
        shift: (stat.presence[i] ?? 0) - (all.presence[i] ?? 0),
      })).filter((x) => !SILENT.has(x.d));
      const up = [...shifts].sort((a, b) => b.shift - a.shift)[0]!;
      const down = [...shifts].sort((a, b) => a.shift - b.shift)[0]!;
      return {
        choice,
        stat,
        up: up.shift >= NOTABLE ? up : null,
        down: down.shift <= -NOTABLE ? down : null,
        weight: Math.max(up.shift, -down.shift),
      };
    })
    .filter((r) => r.up || r.down)
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 2);

  // One sentence in plain words, no numbers: the single data note carries the numbers. Choices that lean the same way
  // share a clause ("Gesha and light-roast coffees are described with floral notes more often…").
  const sentences: string[] = [];
  const grouped = new Map<string, typeof readings>();
  for (const r of readings) {
    const key = `${r.up?.d ?? ""}|${r.down?.d ?? ""}`;
    grouped.set(key, [...(grouped.get(key) ?? []), r]);
  }
  const clauses = [...grouped.values()].map((group) => {
    const r = group[0]!;
    const key =
      r.up && r.down
        ? "reference_clause_up_down"
        : r.up
          ? "reference_clause_up"
          : "reference_clause_down";
    return fill(t[key] as string, {
      option: listed(
        group.map((g) => optionLabel(g.choice, locale)),
        t,
      ),
      up: r.up ? dimNoun(r.up.d, locale) : "",
      down: r.down ? dimNoun(r.down.d, locale) : "",
    });
  });
  if (clauses.length)
    sentences.push(
      fill(variant(t, "reference_frame", seed), {
        clauses: clauses.join(t.clause_join as string),
        allN: all.n.toLocaleString(locale === "zh-CN" ? "zh-CN" : "en-US"),
      }),
    );

  if (!sentences.length) {
    if (!measured.length) sentences.push(variant(t, "reference_none", seed));
    else {
      const dims = DIMENSIONS.map((d, i) => ({
        d: d as string,
        w: result.vPred[i] ?? 0,
      }))
        .filter((x) => !SILENT.has(x.d) && x.w > 0.15)
        .sort((a, b) => b.w - a.w)
        .slice(0, 3)
        .map((x) => dimNoun(x.d, locale));
      sentences.push(
        fill(variant(t, "reference_typical", seed), {
          options: listed(
            measured.map((c) => optionLabel(c, locale)),
            t,
          ),
          dims: listed(dims, t),
        }),
      );
    }
  }
  if (leftOut.length && measured.length)
    sentences.push(
      fill(variant(t, "reference_left_out", seed), {
        options: listed(
          leftOut.map((c) => optionLabel(c, locale)),
          t,
        ),
      }),
    );

  return line(
    sentences
      .map((text) => sentence(text, locale))
      .join(locale === "zh-CN" ? "" : " "),
    "REFERENCE_BASIS",
    "reference_interpretation",
    "corpus_stats: presence by option against all records",
    locale,
  );
}

/** Statistics that bear on the confirmed words: for each confirmed dimension, the chosen scope that says most about it. */
export function supportNotes(
  result: InferenceResult,
  picks: Picked[],
  locale: Locale,
  seed: number,
  count: number,
): ScienceLine[] {
  if (count <= 0) return [];
  const t = templatesFor(locale);
  const all = stats.all;
  const chosen = choices(result.context);
  const has = (axis: string, option: string) =>
    chosen.some((c) => c.axis === axis && c.option === option);
  type Scope = { key: string; label: string; stat: Stat };
  const scopes: Scope[] = [
    ...chosen
      .filter((c) => stats.options[c.axis]?.[c.option])
      .map((c) => ({
        key: `${c.axis}:${c.option}`,
        label: optionLabel(c, locale),
        stat: stats.options[c.axis]![c.option]!,
      })),
    ...stats.pairs
      .filter((p) => has(p.a[0], p.a[1]) && has(p.b[0], p.b[1]))
      .map((p) => ({
        key: `${p.a.join(":")}+${p.b.join(":")}`,
        label: [
          optionLabel({ axis: p.a[0], option: p.a[1] }, locale),
          optionLabel({ axis: p.b[0], option: p.b[1] }, locale),
        ].join(t.pair_join as string),
        stat: { n: p.n, presence: p.presence },
      })),
  ];
  if (!scopes.length) return [];

  const byDimension = new Map<string, string[]>();
  for (const w of picks)
    if (!SILENT.has(w.dimension))
      byDimension.set(w.dimension, [
        ...(byDimension.get(w.dimension) ?? []),
        w.text,
      ]);

  const candidates = [...byDimension.entries()].map(([dimension, words]) => {
    const i = DIMENSIONS.indexOf(dimension as never);
    const best = [...scopes].sort(
      (a, b) =>
        (b.stat.presence[i] ?? 0) - (a.stat.presence[i] ?? 0) ||
        b.stat.n - a.stat.n,
    )[0]!;
    const lean = (best.stat.presence[i] ?? 0) - (all.presence[i] ?? 0);
    return { dimension, words, i, scope: best, lean };
  });
  const kind = (c: { lean: number; i: number }) =>
    c.lean >= LEAN && (all.presence[c.i] ?? 0) < COMMONPLACE
      ? "support"
      : c.lean <= -LEAN
        ? "contrast"
        : "neutral";
  const order = { support: 0, neutral: 1, contrast: 2 } as const;
  const supporting = candidates
    .filter((c) => kind(c) === "support")
    .sort((a, b) => b.lean - a.lean);
  // One note, so it has to be the most telling statistic. Another visit may draw a different one only among those
  // comparably strong (at least 60% of the strongest lean): a weak "7 in 10 against 6" never displaces "5 against 3".
  const strong = supporting.filter(
    (c) => c.lean >= 0.6 * (supporting[0]?.lean ?? 0),
  );
  const turn = strong.length ? seed % strong.length : 0;
  const ordered = [
    ...strong.slice(turn),
    ...strong.slice(0, turn),
    ...supporting.slice(strong.length),
    ...candidates
      .filter((c) => kind(c) !== "support")
      .sort((a, b) => order[kind(a)] - order[kind(b)] || b.lean - a.lean),
  ];

  return ordered.slice(0, count).map((c, index) => {
    const [f, fall] = frequencyPair(
      c.scope.stat.presence[c.i] ?? 0,
      all.presence[c.i] ?? 0,
      kind(c) !== "neutral",
      t,
    );
    return line(
      sentence(
        fill(variant(t, kind(c), seed + index), {
          words: listed(c.words, t),
          dim: dimNoun(c.dimension, locale),
          scope: c.scope.label,
          n: c.scope.stat.n.toLocaleString(
            locale === "zh-CN" ? "zh-CN" : "en-US",
          ),
          f,
          fall,
        }),
        locale,
      ),
      "CORPUS_MEASURED",
      `corpus_support:${c.scope.key}:${c.dimension}`,
      `corpus_stats:${c.scope.key}`,
      locale,
    );
  });
}

/**
 * Aroma or aftertaste read against coffees of the same roast (R3-D40) — only when the reader found it clear AND this
 * kind of coffee is scored high for it more often than its roast band: a statistic that agrees with the answer, in
 * the place of the single data note, never next to it.
 */
const FOUND_CLEAR: Record<string, "aroma" | "aftertaste"> = {
  E1a: "aroma",
  E1b: "aroma",
  E2c: "aftertaste",
  E2d: "aftertaste",
};
export function structureNote(
  result: InferenceResult,
  answers: Record<string, string | undefined>,
  locale: Locale,
  seed: number,
): ScienceLine | null {
  const t = templatesFor(locale);
  for (const id of [answers.E2, answers.E1]) {
    const which = FOUND_CLEAR[id ?? ""];
    if (!which) continue;
    const found = structureComparison(which, result.context);
    if (!found || found.share - found.bandShare < 0.08) continue;
    const scope = [
      found.facets.prep ? (t.structure_espresso as string) : "",
      found.facets.process
        ? optionLabel(
            { axis: "C2_process", option: found.facets.process },
            locale,
          )
        : "",
      found.facets.variety
        ? optionLabel(
            { axis: "C2_variety", option: found.facets.variety },
            locale,
          )
        : "",
    ].filter(Boolean);
    const [f, fall] = frequencyPair(found.share, found.bandShare, true, t);
    return line(
      sentence(
        fill(variant(t, "structure_high", seed), {
          what: t[`structure_${which}`] as string,
          scope: scope.join(t.pair_join as string),
          f,
          fall,
        }),
        locale,
      ),
      "CORPUS_MEASURED",
      `corpus_structure:${found.key}:${which}`,
      `dynamic_bank.groups:${found.key}`,
      locale,
    );
  }
  return null;
}

/** Which shown words come from what the answers raised, and which confirmed words the reference already had. */
function wordSources(
  result: InferenceResult,
  picks: Picked[],
  evaluation: Picked[],
): { own: string[]; shared: string[] } {
  const raised = new Set(
    DIMENSIONS.filter(
      (d, i) => d !== "defect" && (result.deltaV[i] ?? 0) >= MOVED,
    ) as string[],
  );
  const steady = (dimension: string) => {
    const i = DIMENSIONS.indexOf(dimension as never);
    return (
      Math.abs(result.deltaV[i] ?? 0) < MOVED && (result.vPred[i] ?? 0) >= 0.15
    );
  };
  return {
    own: [...picks, ...evaluation]
      .filter((w) => raised.has(w.dimension))
      .map((w) => w.text),
    shared: picks.filter((w) => steady(w.dimension)).map((w) => w.text),
  };
}

/**
 * The exported card's supplementary description: what stands out in this cup against the reference, said about the cup and not to
 * the reader — "your description" on a card that is meant to be shared weakens it (owner, 2026-09-19).
 */
export function cardNote(
  result: InferenceResult,
  picks: Picked[],
  evaluation: Picked[],
  locale: Locale,
): string {
  const t = templatesFor(locale);
  const moves = DIMENSIONS.map((d, i) => ({
    d: d as string,
    delta: result.deltaV[i] ?? 0,
  })).filter((x) => x.d !== "defect");
  // short labels in a plain list: the English nouns carry commas and "and" of their own ("roast and bitterness")
  const names = (list: Array<{ d: string }>) =>
    list
      .slice(0, 2)
      .map((x) => (locale === "en" ? dimLabel : dimNoun)(x.d, locale))
      .join(t.join as string);
  const raised = moves
    .filter((x) => x.delta >= MOVED)
    .sort((a, b) => b.delta - a.delta);
  const lowered = moves
    .filter((x) => x.delta <= -MOVED)
    .sort((a, b) => a.delta - b.delta);
  const key =
    raised.length && lowered.length
      ? "card_both"
      : raised.length
        ? "card_up"
        : lowered.length
          ? "card_down"
          : "card_none";
  const sentences = [
    fill(t[key] as string, {
      raised: names(raised),
      lowered: names(lowered),
    }),
  ];
  // a supplementary description, not a bare statement (owner, 2026-09-19): which words on the card come from that
  // lean and which the reference already had — the same reading as the description note, said about the cup
  const { own, shared } = wordSources(result, picks, evaluation);
  const wordsKey =
    own.length && shared.length
      ? "card_words_both"
      : own.length
        ? "card_words_own"
        : shared.length
          ? "card_words_shared"
          : null;
  if (wordsKey)
    sentences.push(
      fill(t[wordsKey] as string, {
        own: listed(own, t),
        shared: listed(shared, t),
      }),
    );
  return sentences
    .map((text) => sentence(text, locale))
    .join(locale === "zh-CN" ? "" : " ");
}

/** What the reader's answers moved against the reference, and which confirmed words come from that. */
export function descriptionNote(
  result: InferenceResult,
  picks: Picked[],
  evaluation: Picked[],
  locale: Locale,
  seed: number,
  secondLook: string[] = [],
): ScienceLine {
  const t = templatesFor(locale);
  const moves = DIMENSIONS.map((d, i) => ({
    d: d as string,
    delta: result.deltaV[i] ?? 0,
  })).filter((x) => x.d !== "defect");
  const raisedAll = moves
    .filter((x) => x.delta >= MOVED)
    .sort((a, b) => b.delta - a.delta);
  const loweredAll = moves
    .filter((x) => x.delta <= -MOVED)
    .sort((a, b) => a.delta - b.delta);
  // what stands out is said with its gloss, so "spice" is never a bare category; what recedes keeps the short label
  const names = (list: Array<{ d: string }>, gloss: boolean) =>
    listed(
      list
        .slice(0, 2)
        .map((x) => (gloss ? dimGloss(x.d, locale) : dimNoun(x.d, locale))),
      t,
    );

  const key =
    raisedAll.length && loweredAll.length
      ? "moved_both"
      : raisedAll.length
        ? "moved_up"
        : loweredAll.length
          ? "moved_down"
          : "moved_none";
  const sentences = [
    fill(variant(t, key, seed), {
      raised: names(raisedAll, true),
      lowered: names(loweredAll, false),
    }),
  ];

  const { own, shared } = wordSources(result, picks, evaluation);
  const wordsKey =
    own.length && shared.length
      ? "words_both"
      : own.length
        ? "words_own"
        : shared.length
          ? "words_shared"
          : null;
  if (wordsKey)
    sentences.push(
      fill(variant(t, wordsKey, seed + 1), {
        own: listed(own, t),
        shared: listed(shared, t),
      }),
    );
  if (secondLook.length)
    sentences.push(
      fill(variant(t, "second_look", seed + 2), {
        dims: listed(
          secondLook.map((d) => dimNoun(d, locale)),
          t,
        ),
      }),
    );

  return line(
    sentences
      .map((text) => sentence(text, locale))
      .join(locale === "zh-CN" ? "" : " "),
    "COMPUTED_DELTA",
    "description_moves",
    "engine: V_user − V_pred",
    locale,
  );
}

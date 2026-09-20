/**
 * The dynamic question bank (owner, 2026-09-19, R3-D40): what each question shows for this kind of coffee.
 *
 *   - An option pool holds six to ten options; a question shows FOUR of them (owner, 2026-09-20) — five only for the
 *     first two questions, where "I can't say" is the fifth option, and for bitterness asked as a strong correction,
 *     which shows its five levels. The corpus PRUNES the pool to the three
 *     options this kind of coffee is most often described with — it never sorts them: the survivors keep the pool's
 *     fixed order, so a position never nudges the reader toward "the usual answer".
 *   - The fifth option is never a bare "not noticeable": it says what it means ("酸不突出，整体圆润"). A reader who
 *     cannot answer has a line under the options ("这一项很难形容").
 *   - The same option has several wordings, drawn by a seed and aligned across languages; the examples inside a label
 *     are this kind of coffee's own most frequent words ("柑橘：柠檬、佛手柑、甜橙那种" for a Gesha).
 *   - Two levels: the family first, then "which one" among that family's words — which decides the words on the card
 *     (the soft constraint of R3-D42: what the reader points to leads, and may repeat).
 *
 * Everything here is a pure function of (context, answers, seed): an edited session replays to the same questions, and
 * both languages show the same option ids. The session and the interface are not wired to it yet.
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };
import {
  DIMENSIONS,
  textSeed,
  type ContextAnswers,
  type Locale,
} from "./engine";

export type DynamicQuestionId =
  | "A"
  | "B"
  | "C"
  | "D"
  | "E1"
  | "E2"
  | "E3"
  | "E4";

/** The session's question keys: the four core slots, bitterness and the overall impression keep their slot names (the
 *  coherence tree reads them), aroma and aftertaste are E1 / E2, and a second level is "S:<the first-level option>". */
export const QUESTION_OF_SLOT: Record<string, DynamicQuestionId> = {
  Q0: "A",
  Q1: "B",
  Q2: "C",
  Q3: "D",
  Q4: "E3",
  Q5: "E4",
  E1: "E1",
  E2: "E2",
};
const PREVIOUS_SLOT: Record<string, string> = { Q1: "Q0", Q2: "Q1", Q3: "Q2" };

/** Whether a key names a question of the session (a slot, aroma, aftertaste, or a second level). */
export const isQuestionKey = (key: string): boolean =>
  key in QUESTION_OF_SLOT || key.startsWith("S:");
type Role =
  | "data"
  | "always"
  | "default_light"
  | "fifth"
  | "unanswered"
  | "scale"
  | "word";
type BankOption = {
  id: string;
  parent: string;
  role: Role;
  label: Record<Locale, string[]>;
  deltas: Record<string, number>;
  focus: string;
  card_row: Record<Locale, string> | null;
  lead_in: Record<Locale, string> | null;
  short: Record<Locale, string> | null;
};
type Group = {
  n: number;
  keep: Record<string, string[]>;
  second: Record<string, string[]>;
  aroma_high: number | null;
  aftertaste_high: number | null;
  aftertaste_low: number | null;
};
type Bank = {
  max_options: number;
  /** how many things a question offers to tap: four, five for the first questions (owner, 2026-09-20) */
  tappable: Record<string, number>;
  /** which four levels of a five-level scale a cup is shown, by roast band */
  scale_windows: Record<string, Record<string, string[]>>;
  /** scales shown in full when the question is a strong correction (answers in severe conflict) */
  strong_correction_full_scale: string[];
  group_priority: string[][];
  roast_band: Record<string, string>;
  espresso_preparations: string[];
  mouthfeel_windows: Record<string, { preparations: string[]; keep: string[] }>;
  prompts: Record<
    string,
    { kind: string; tail: Record<Locale, string> | null } & Record<
      Locale,
      string
    >
  >;
  options: Record<string, BankOption[]>;
  groups: Record<string, Group>;
};
const bank = (bundle as unknown as { dynamic_bank: Bank }).dynamic_bank;

export type ShownOption = {
  id: string;
  label: string;
  role: Role;
};
export type ShownQuestion = {
  id: string;
  prompt: string;
  /** at most five, in the pool's order */
  options: ShownOption[];
  /** the line under the options for a reader who cannot answer; not one of the five */
  unanswered: ShownOption | null;
  /** the kind of coffee the pruning was read from, and how many records stand behind it */
  group: { key: string; n: number };
};

const single = (value: string | string[] | undefined): string =>
  Array.isArray(value) ? (value.length === 1 ? value[0]! : "") : (value ?? "");

/** The facets of a cup that the corpus can speak for: roast band, process, variety, espresso-based or not. */
function facets(context: ContextAnswers): Record<string, string> {
  const preparation = single(context.c0_preparation);
  return {
    band: bank.roast_band[single(context.c1_roast)] ?? "",
    process: single(context.c2_process),
    variety: single(context.c2_variety), // a blend of several varieties has no variety facet
    prep: bank.espresso_preparations.includes(preparation) ? "espresso" : "",
  };
}

/** The most specific kind of coffee with enough records behind it; the builder and the app walk the same list. */
export function contextGroup(context: ContextAnswers): {
  key: string;
  n: number;
} {
  const f = facets(context);
  for (const combo of bank.group_priority) {
    if (!combo.every((k) => f[k])) continue;
    const key = combo.map((k) => `${k}=${f[k]}`).join("|") || "all";
    const group = bank.groups[key];
    if (group) return { key, n: group.n };
  }
  return { key: "all", n: bank.groups.all!.n };
}

/** one wording of an option: the same index in both languages, fixed for a session (the seed) */
function wording(option: BankOption, locale: Locale, seed: number): string {
  const variants = option.label[locale];
  return variants[textSeed([String(seed), option.id]) % variants.length]!;
}

const joined = (words: string[], locale: Locale): string =>
  locale === "zh-CN"
    ? words.join("、")
    : words.length < 2
      ? (words[0] ?? "")
      : `${words.slice(0, -1).join(", ")} or ${words[words.length - 1]!}`;

function shown(
  option: BankOption,
  group: Group,
  locale: Locale,
  seed: number,
): ShownOption {
  let label = wording(option, locale, seed);
  if (label.includes("{examples}")) {
    // this kind of coffee's own most frequent words of the family, so the same option differs in detail between coffees
    const words = (group.second[option.id] ?? [])
      .slice(0, 3)
      .map((id) => bank.options.S!.find((o) => o.id === id)!)
      .map((o) =>
        locale === "en" ? o.label.en[0]!.toLowerCase() : o.label["zh-CN"][0]!,
      );
    label = label.replace("{examples}", joined(words, locale));
  }
  return { id: option.id, label, role: option.role };
}

/** What a question shows for this cup: the pruned options in the pool's order, the fifth option, the line below. */
export function shownQuestion(
  id: DynamicQuestionId,
  context: ContextAnswers,
  locale: Locale,
  seed = 0,
  /** the question is asked as a strong correction: the answers so far are in severe conflict */
  strong = false,
): ShownQuestion {
  const at = contextGroup(context);
  const group = bank.groups[at.key]!;
  const pool = bank.options[id]!;
  let kept: Set<string>;
  if (id === "D") {
    const preparation = single(context.c0_preparation);
    const window =
      Object.values(bank.mouthfeel_windows).find((w) =>
        w.preparations.includes(preparation),
      ) ?? bank.mouthfeel_windows.middle!;
    kept = new Set(window.keep);
  } else if (group.keep[id]) kept = new Set(group.keep[id]);
  else {
    const full = strong && bank.strong_correction_full_scale.includes(id);
    const window = full
      ? undefined
      : bank.scale_windows[id]?.[facets(context).band || "medium"];
    kept = new Set(
      window ?? pool.filter((o) => o.role === "scale").map((o) => o.id),
    );
  }
  const options = pool
    .filter((o) => kept.has(o.id) || o.role === "fifth")
    .map((o) => shown(o, group, locale, seed));
  // four options; five only for the first questions, where "I can't say" is the fifth — an option like the others
  const limit = bank.tappable[id] ?? bank.tappable.default ?? 4;
  const unanswered =
    options.length < limit
      ? pool.find((o) => o.role === "unanswered")
      : undefined;
  return {
    id,
    prompt: bank.prompts[id]![locale],
    options: options.slice(0, bank.max_options),
    unanswered: unanswered ? shown(unanswered, group, locale, seed) : null,
    group: at,
  };
}

/** The second level — "which one?" — for a first-level answer that names a family; null when there is none. */
export function secondLevelQuestion(
  parentOptionId: string,
  context: ContextAnswers,
  locale: Locale,
  seed = 0,
): ShownQuestion | null {
  const at = contextGroup(context);
  const group = bank.groups[at.key]!;
  const kept = new Set(group.second[parentOptionId] ?? []);
  if (!kept.size) return null;
  return {
    id: `S:${parentOptionId}`,
    prompt: bank.prompts.S![locale],
    options: bank.options
      .S!.filter((o) => kept.has(o.id))
      .map((o) => shown(o, group, locale, seed)),
    // three words and "I can't say": a reader may know it is a berry and not which one
    unanswered: (() => {
      const line = bank.options.S!.find((o) => o.role === "unanswered");
      return line ? shown(line, group, locale, seed) : null;
    })(),
    group: at,
  };
}

export type DynamicEffects = {
  /** what the answers add to the reader's vector, by dimension (the 12 dimensions' order) */
  deltas: number[];
  /** dimension → the sub-family the reader pointed to, for describe()'s soft constraint */
  focus: Record<string, string>;
  /** dimension → the very word the reader chose at the second level: it leads that dimension's words */
  leadWord: Record<string, string>;
  /** evaluation rows that come straight from the reader's answers (aroma, aftertaste) */
  cardRows: Array<Record<Locale, string>>;
  /** questions the reader could not answer: no effect on the vector, not counted for coherence */
  unanswered: string[];
};

const everyOption = Object.values(bank.options).flat();
const optionIndex = new Map(everyOption.map((o) => [o.id, o]));

/** Whether an answer is an option of the dynamic bank (its ids never collide with Matrix_Q's single letters). */
export const isDynamicOption = (id: string | undefined): boolean =>
  id !== undefined && optionIndex.has(id);

/** The weights of a dynamic option on the 12 dimensions, unnormalised; null for an id the bank does not know. */
export function dynamicOptionVector(id: string): number[] | null {
  const option = optionIndex.get(id);
  if (!option) return null;
  const v = DIMENSIONS.map(() => 0);
  for (const [dimension, weight] of Object.entries(option.deltas)) {
    const i = DIMENSIONS.indexOf(dimension);
    if (i >= 0) v[i] = weight;
  }
  return v;
}

export const isUnanswered = (id: string | undefined): boolean =>
  id !== undefined && optionIndex.get(id)?.role === "unanswered";

/** The question a session key shows: a core slot, bitterness, the overall impression, aroma, aftertaste or a second level. */
export function questionForKey(
  key: string,
  context: ContextAnswers,
  answers: Record<string, string | undefined>,
  locale: Locale,
  seed = 0,
  strong = false,
): ShownQuestion | null {
  if (key.startsWith("S:")) {
    const parent = key.slice(2);
    const question = secondLevelQuestion(parent, context, locale, seed);
    const short = optionIndex.get(parent)?.short?.[locale];
    const tail = bank.prompts.S!.tail?.[locale];
    return question && short && tail
      ? { ...question, prompt: tail.replace("{short}", short) }
      : question;
  }
  const id = QUESTION_OF_SLOT[key];
  if (!id) return null;
  const question = shownQuestion(id, context, locale, seed, strong);
  // the prompt follows the previous answer, as the six fixed questions did: "柑橘那种酸之后，闻起来、喝起来最像哪一类？"
  const previous = PREVIOUS_SLOT[key];
  const lead = previous
    ? optionIndex.get(answers[previous] ?? "")?.lead_in?.[locale]
    : undefined;
  const tail = bank.prompts[id]!.tail?.[locale];
  return lead && tail ? { ...question, prompt: lead + tail } : question;
}

/**
 * The follow-up questions after the four core ones — two at most, so a cup is asked six questions or fewer. A pure
 * function of the cup, the core answers, how well they agree, and the session's nonce (which only rotates the second
 * follow-up between visits).
 *   severe conflict   bitterness and the overall impression: the two correction questions of the coherence tree
 *   mild conflict     the overall impression (the tree's confirmation), then one of the three most telling details
 *   coherent          the two most telling details: a second level ("which one?") for the fruit answer and for the
 *                     aroma answer, aftertaste, aroma, bitterness — bitterness first for dark roasts and roasty answers
 */
export function followUpKeys(
  context: ContextAnswers,
  answers: Record<string, string | undefined>,
  level: "coherent" | "mild" | "severe",
  nonce = 0,
): string[] {
  // a reader who could not answer two of the core questions is not asked for more detail: one follow-up, not two
  const struggling =
    ["Q0", "Q1", "Q2", "Q3"].filter((k) => isUnanswered(answers[k])).length >=
    2;
  if (level === "severe") return struggling ? ["Q5"] : ["Q4", "Q5"];
  const group = bank.groups[contextGroup(context).key]!;
  const hasSecond = (id: string | undefined) =>
    id !== undefined && (group.second[id]?.length ?? 0) >= 2;
  const details = [answers.Q0, answers.Q1]
    .filter(hasSecond)
    .map((id) => `S:${id}`);
  const structure = (["E2", "E1"] as const).filter((id) =>
    structureQuestionWorthAsking(id, context),
  );
  const roasty =
    facets(context).band === "dark" ||
    ["B5", "B6", "B9"].includes(answers.Q1 ?? "") ||
    answers.Q2 === "C4";
  const pool = roasty
    ? ["Q4", ...details, ...structure]
    : [...details, ...structure, "Q4"];
  // the detail slot rotates between visits among the three most telling candidates, so that aroma and aftertaste are
  // reached on this path too (two cups in three take it); within a session the nonce is fixed
  if (level === "mild")
    return struggling
      ? ["Q5"]
      : ["Q5", pool[nonce % Math.min(3, pool.length)]!];
  const rest = pool.slice(1);
  return struggling || !rest.length
    ? [pool[0]!]
    : [pool[0]!, rest[nonce % rest.length]!];
}

/**
 * What the reader's answers say about the words, per dimension (the card follows the reader's signals):
 *   lead    the very word chosen at the second level
 *   family  the sub-family a first-level answer points to
 *   passed  kinds of fruit the reader was SHOWN in the fruit question and did not choose (owner, 2026-09-20, R3-D49): a
 *           reader who saw "stone fruit" and chose "citrus" must not be handed a peach by the rotation. They go to the
 *           back of their dimension — last, not removed: no cap, no exclusion. A reader who could not answer passed
 *           nothing over; a kind chosen in another question is not passed. Only the fruit question (PASSED_OVER_IN):
 *           it asks WHICH fruit, so the other kinds were weighed and left. The aroma and sweetness questions ask for
 *           the MAIN note among different things — choosing "wood" does not deny the chocolate — and treating their
 *           unchosen options as absent cost 4 points of precision and 6 of coverage on the 500-cup simulation.
 *   from    another dimension whose words fill this dimension's slots: an answer that points at a whole dimension
 *           ("citrus" → acidity:*) and also carries weight elsewhere (citrus is a fruit: fruity 1) says which words
 *           that weight stands for — citrus words, not whatever the fruit list's rotation holds. Only when the reader
 *           pointed at nothing else in that dimension.
 */
/** The questions whose unchosen options count as passed over (see WordHint.passed). */
const PASSED_OVER_IN: ReadonlySet<string> = new Set(["A"]);

export type WordHint = {
  family?: string;
  lead?: string;
  passed?: string[];
  from?: string;
};

export function wordHints(
  answers: Record<string, string | undefined>,
  context?: ContextAnswers,
): Record<string, WordHint> {
  const hints: Record<string, WordHint> = {};
  const chosen = new Set<string>();
  for (const id of Object.values(answers)) {
    const option = optionIndex.get(id ?? "");
    const [dimension, target] = (option?.focus ?? "").split(":");
    if (!option || !dimension || !target || target === "*") continue;
    const hint = (hints[dimension] ??= {});
    if (option.role === "word") hint.lead ??= target;
    else {
      hint.family ??= target; // the first answer that names a sub-family keeps it (the fruit question before the sweetness one)
      chosen.add(`${dimension}:${target}`);
    }
  }
  if (!context) return hints;
  for (const [key, id] of Object.entries(answers)) {
    const question = QUESTION_OF_SLOT[key];
    const answered = optionIndex.get(id ?? "");
    if (!question || !answered || answered.role === "unanswered") continue;
    // what this question showed for this cup, minus what the reader chose here or anywhere else
    for (const shownOption of shownQuestion(question, context, "zh-CN")
      .options) {
      const focus = optionIndex.get(shownOption.id)?.focus ?? "";
      const [dimension, target] = focus.split(":");
      if (shownOption.id === id || !dimension || !target || target === "*")
        continue;
      if (chosen.has(focus) || !PASSED_OVER_IN.has(question)) continue;
      const hint = (hints[dimension] ??= {});
      if (!(hint.passed ??= []).includes(target)) hint.passed.push(target);
    }
    // an answer about a whole dimension that also weighs on another one lends that dimension its words
    const [whole, target] = (answered.focus ?? "").split(":");
    if (whole && target === "*")
      for (const dimension of Object.keys(answered.deltas ?? {})) {
        if (dimension === whole) continue;
        const hint = (hints[dimension] ??= {});
        if (!hint.family && !hint.lead) hint.from ??= whole;
      }
  }
  for (const hint of Object.values(hints))
    if (hint.family || hint.lead) delete hint.from;
  return hints;
}

/** Evaluation rows that come straight from the reader's answers: aroma, aftertaste, and the word for bitterness. */
export function answeredRows(
  answers: Record<string, string | undefined>,
  locale: Locale,
): {
  rows: Array<{ dimension: string; label: string; text: string }>;
  noBitterness: boolean;
} {
  const rows: Array<{ dimension: string; label: string; text: string }> = [];
  for (const [key, id] of Object.entries(answers)) {
    const row = optionIndex.get(id ?? "")?.card_row?.[locale];
    if (!row) continue;
    const [label, text] = row.split(" · ");
    rows.push({
      dimension:
        key === "Q4" ? "bitter_roasted" : key === "E1" ? "aroma" : "aftertaste",
      label: label!,
      text: text ?? "",
    });
  }
  return { rows, noBitterness: answers.Q4 === "E3a" };
}

/** What a set of answers (question id → option id) means for the engine. */
export function dynamicEffects(
  answers: Record<string, string>,
): DynamicEffects {
  const deltas = DIMENSIONS.map(() => 0);
  const effects: DynamicEffects = {
    deltas,
    focus: {},
    leadWord: {},
    cardRows: [],
    unanswered: [],
  };
  const all = Object.values(bank.options).flat();
  for (const [question, optionId] of Object.entries(answers)) {
    const option = all.find((o) => o.id === optionId);
    if (!option) continue;
    if (option.role === "unanswered") {
      effects.unanswered.push(question);
      continue;
    }
    for (const [dimension, weight] of Object.entries(option.deltas)) {
      const i = DIMENSIONS.indexOf(dimension);
      if (i >= 0) deltas[i] = deltas[i]! + weight;
    }
    const [dimension, target] = option.focus.split(":");
    if (dimension && target && target !== "*") {
      if (option.role === "word") effects.leadWord[dimension] = target;
      else effects.focus[dimension] = target;
    }
    if (option.card_row) effects.cardRows.push(option.card_row);
  }
  return effects;
}

/**
 * Aroma or aftertaste for this kind of coffee against coffees of the SAME roast band — never across bands: the scores
 * follow the reviewers' preference for lighter roasts. Null when the group is the band itself (nothing to compare).
 */
export function structureComparison(
  which: "aroma" | "aftertaste",
  context: ContextAnswers,
): {
  key: string;
  n: number;
  share: number;
  bandShare: number;
  facets: { process: string; variety: string; prep: string };
} | null {
  const at = contextGroup(context);
  const f = facets(context);
  const band = bank.groups[`band=${f.band}`];
  const group = bank.groups[at.key]!;
  const pick = (g: Group) =>
    which === "aroma" ? g.aroma_high : g.aftertaste_high;
  if (!f.band || !band || !at.key.startsWith(`band=${f.band}|`)) return null;
  const share = pick(group);
  const bandShare = pick(band);
  if (share === null || bandShare === null) return null;
  return {
    key: at.key,
    n: at.n,
    share,
    bandShare,
    facets: {
      process: at.key.includes("process=") ? f.process! : "",
      variety: at.key.includes("variety=") ? f.variety! : "",
      prep: at.key.includes("prep=") ? "espresso" : "",
    },
  };
}

/** Whether the corpus is one-sided about aroma or aftertaste for this kind of coffee — then the question is not worth a slot. */
export function structureQuestionWorthAsking(
  id: "E1" | "E2",
  context: ContextAnswers,
): boolean {
  const group = bank.groups[contextGroup(context).key]!;
  const share = id === "E1" ? group.aroma_high : group.aftertaste_high;
  return share === null || (share > 0.15 && share < 0.85);
}

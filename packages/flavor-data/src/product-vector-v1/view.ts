/**
 * View models for the PWA (owner, 2026-09-12): framework-agnostic props for the four screens —
 * QuizCard (C0–C2 context cards, then Q0–Q5 question cards), FirstDescriptionCard (3 + 5 words with
 * the 8-choose-5 pick matrix), ResultCard (branch A / final), EscalationModal (Q6). No styling, no
 * framework: a React or Vue component binds these objects one-to-one.
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };
import { cardCopy, contextLabel, shortContextLabel, type ContextAnswers, type Locale } from "./engine";
import { type Word } from "./flow";
import { nextStep, type Session } from "./session";

const rules = bundle.context_rules;
const K = bundle.matrix_k as Record<string, Record<string, { vector: number[] | null; basis: string; member_count: number | null }>>;

export type Chip = { value: string; label: string; basis: string; memberCount: number | null; group?: string };
export type ContextCard =
  | { key: "c0_preparation"; title: string; chips: Chip[]; multi: false; optional: false }
  | { key: "c1_roast"; title: string; chips: Chip[]; multi: false; optional: false }
  | { key: "c2_variety"; title: string; chips: Chip[]; multi: true; max: number; toggle: { single: string; blend: string }; optional: false }
  | { key: "c2_process"; title: string; chips: Chip[]; multi: false; optional: false }
  | { key: "c2_origin"; title: string; chips: Chip[]; multi: false; optional: true; hint: string; groups: Array<{ key: string; label: string }> };

const LABELS: Record<string, Record<Locale, string>> = {
  pour_over_v60: { "zh-CN": "手冲 (V60)", en: "Pour-over (V60)" },
  french_press: { "zh-CN": "法压", en: "French press" },
  espresso: { "zh-CN": "意式浓缩", en: "Espresso" },
  cold_brew: { "zh-CN": "冷萃", en: "Cold brew" },
  very_light: { "zh-CN": "极浅烘", en: "Very light" },
  light: { "zh-CN": "浅烘", en: "Light" },
  medium_light: { "zh-CN": "中浅烘", en: "Medium-light" },
  medium: { "zh-CN": "中烘", en: "Medium" },
  medium_dark: { "zh-CN": "中深烘", en: "Medium-dark" },
  dark: { "zh-CN": "深烘", en: "Dark" },
  very_dark: { "zh-CN": "极深烘", en: "Very dark" },
  gesha: { "zh-CN": "瑰夏 Gesha", en: "Gesha" },
  bourbon: { "zh-CN": "波本 Bourbon", en: "Bourbon" },
  typica: { "zh-CN": "铁皮卡 Typica", en: "Typica" },
  caturra: { "zh-CN": "卡杜拉 Caturra", en: "Caturra" },
  catuai: { "zh-CN": "卡杜艾 Catuai", en: "Catuai" },
  sl28_sl34: { "zh-CN": "SL28 / SL34", en: "SL28 / SL34" },
  pacamara: { "zh-CN": "帕卡马拉 Pacamara", en: "Pacamara" },
  castillo: { "zh-CN": "卡斯蒂略 Castillo", en: "Castillo" },
  robusta: { "zh-CN": "罗布斯塔 Robusta", en: "Robusta" },
  ethiopian_landrace: { "zh-CN": "埃塞原生种 Heirloom", en: "Ethiopian landrace" },
  washed: { "zh-CN": "水洗", en: "Washed" },
  natural: { "zh-CN": "日晒", en: "Natural" },
  anaerobic: { "zh-CN": "厌氧发酵", en: "Anaerobic" },
  decaf: { "zh-CN": "低因", en: "Decaf" },
};
const TITLES: Record<string, Record<Locale, string>> = {
  c0_preparation: { "zh-CN": "怎么制作的？", en: "How was it made?" },
  c1_roast: { "zh-CN": "烘焙度", en: "Roast level" },
  c2_variety: { "zh-CN": "豆种", en: "Variety" },
  c2_process: { "zh-CN": "咖啡豆的处理法", en: "How the beans were processed" },
  c2_origin: { "zh-CN": "咖啡豆的产地（可选）", en: "Where the beans are from (optional)" },
};

function label(value: string, locale: Locale): string {
  const fromBundle = contextLabel(value, locale);
  return fromBundle !== value ? fromBundle : (LABELS[value]?.[locale] ?? value);
}

function chips(axis: string, locale: Locale): Chip[] {
  return Object.entries(K[axis] ?? {}).map(([value, row]) => ({ value, label: label(value, locale), basis: row.basis, memberCount: row.member_count }));
}

/** The C0–C2 context cards: preparation, roast, variety (single / blend toggle, max 3), processing, optional origin. */
export function contextCatalog(locale: Locale): ContextCard[] {
  const continents = ((rules as { origin_continents?: Record<string, Record<Locale, string>> }).origin_continents ?? {}) as Record<string, Record<Locale, string>>;
  const origins = Object.entries(rules.origin_regions as Record<string, { label: Record<Locale, string>; bias: string[]; continent?: string }>).map(([value, r]) => ({
    value,
    label: r.label[locale],
    basis: `ORIGIN_BIAS_DELTA_${rules.origin_bias_delta}_ON_${r.bias.join("+")}`,
    memberCount: null,
    ...(r.continent ? { group: r.continent } : {}),
  }));
  const groups = Object.entries(continents).map(([key, label]) => ({ key, label: label[locale] }));
  return [
    { key: "c0_preparation", title: TITLES.c0_preparation![locale], chips: chips("C0", locale), multi: false, optional: false },
    { key: "c1_roast", title: TITLES.c1_roast![locale], chips: chips("C1", locale), multi: false, optional: false },
    {
      key: "c2_variety",
      title: TITLES.c2_variety![locale],
      chips: chips("C2_variety", locale),
      multi: true,
      max: rules.blend.max_varieties,
      toggle: locale === "zh-CN" ? { single: "单品 SOE", blend: "拼配 Blend" } : { single: "Single origin", blend: "Blend" },
      optional: false,
    },
    { key: "c2_process", title: TITLES.c2_process![locale], chips: chips("C2_process", locale), multi: false, optional: false },
    {
      key: "c2_origin",
      title: TITLES.c2_origin![locale],
      chips: origins,
      multi: false,
      optional: true,
      hint: locale === "zh-CN" ? "不清楚产地也可以继续。" : "Not sure? You can skip this.",
      groups,
    },
  ];
}

/** Validate and normalise a context picked from the catalog (blend capped at max varieties). */
export function normalizeContext(input: ContextAnswers): ContextAnswers {
  const out: ContextAnswers = { ...input };
  if (Array.isArray(out.c2_variety)) {
    const unique = [...new Set(out.c2_variety.filter(Boolean))].slice(0, rules.blend.max_varieties);
    const first = unique[0];
    if (first === undefined) delete out.c2_variety;
    else out.c2_variety = unique.length === 1 ? first : unique;
  }
  return out;
}

export type QuizCardModel = { kind: "question"; slot: string; prompt: string; adapted: boolean; options: Array<{ option: string; label: string; fit: number }>; progress: { answered: number; expected: number } };
export type FirstDescriptionCardModel = {
  kind: "first_description";
  main: Word[];
  secondary: Word[];
  pickPrompt: string;
  pickCount: number;
  path: number | null;
  profileTitle: string | null;
  heading: string;
};
export type ResultCardModel = {
  kind: "result";
  title: string;
  /** the cup's own information, only what was entered: brew, roast, variety, process, origin */
  cupInfo: Array<{ key: string; label: string; value: string }>;
  picked: string[];
  pickedDimensions: string[];
  tags: string[];
  heading: string;
  scienceHeading: string;
  science: Array<{ text: string; evidenceState: string; citationRef: string; sourceTitle: string; sourceLicence: string; label: string; citation: string }>;
  closing: string;
  corrected: boolean; // true after Q6 (second, refined card)
  shareText: string;
};
export type EscalationModalModel = { kind: "escalation"; title: string; options: Array<{ dimension: string; text: string }>; submitLabel: string; reason: string };
export type ScreenModel = QuizCardModel | { kind: "describe_ready" } | FirstDescriptionCardModel | EscalationModalModel | ResultCardModel;

/** The screen to render for a session — the only function a UI needs after each user action. */
export function screenModel(session: Session): ScreenModel {
  const locale = session.locale;
  const step = nextStep(session);
  if (step.kind === "ask") return { kind: "question", ...step.card };
  if (step.kind === "describe") return { kind: "describe_ready" };
  if (step.kind === "picks" && session.description) {
    return {
      kind: "first_description",
      main: session.description.main,
      secondary: session.description.secondary,
      pickPrompt: session.description.prompt,
      pickCount: bundle.question_flow.first_description.pick_count,
      path: session.step.path,
      profileTitle: session.result?.profiles[0]?.profile.owner_name[locale] ?? null,
      heading: ((bundle.presentation as { preview_heading?: Record<Locale, string> }).preview_heading ?? { "zh-CN": "这杯咖啡的风味", en: "This cup's flavor" })[locale],
    };
  }
  if (step.kind === "q6" && session.q6) {
    return {
      kind: "escalation",
      title: q6Copy(locale).title,
      options: session.q6.options.map((o) => ({ dimension: o.dimension, text: o.text })),
      submitLabel: q6Copy(locale).submit,
      reason: session.gate?.reason ?? "",
    };
  }
  const card = session.card;
  const title = card?.profileTitle ?? "";
  const tags = card?.picked ?? [];
  return {
    kind: "result",
    title,
    cupInfo: cupInfo(session.context, locale),
    picked: tags,
    pickedDimensions: session.picks.map((w) => w.dimension),
    tags,
    heading: cardCopy(locale).heading,
    scienceHeading: cardCopy(locale).science,
    science: (card?.science ?? []).map((l) => ({ text: l.text, evidenceState: l.evidenceState, citationRef: l.citationRef, sourceTitle: l.sourceTitle, sourceLicence: l.sourceLicence, label: l.label, citation: l.citation })),
    closing: card?.closing ?? "",
    corrected: session.q6 !== null && session.q6.selected.length > 0,
    shareText: `${title}\n${tags.join(" | ")}`,
  };
}

/** The cup's information for the card's top layer: only fields the reader actually entered, in reading order. */
export function cupInfo(context: ContextAnswers, locale: Locale): Array<{ key: string; label: string; value: string }> {
  const zh = locale === "zh-CN";
  const names: Record<string, [string, string]> = { c0_preparation: ["冲煮", "Brew"], c1_roast: ["烘焙", "Roast"], c2_variety: ["豆种", "Variety"], c2_process: ["处理", "Process"], c2_origin: ["产地", "Origin"] };
  const out: Array<{ key: string; label: string; value: string }> = [];
  for (const key of ["c0_preparation", "c1_roast", "c2_variety", "c2_process", "c2_origin"] as const) {
    const value = context[key];
    const values = Array.isArray(value) ? value : value ? [value] : [];
    if (!values.length) continue;
    const text = key === "c2_origin"
      ? values.map((v) => (rules.origin_regions as Record<string, { label: Record<Locale, string> }>)[v]?.label[locale] ?? v).join(" + ")
      : values.map((v) => (contextLabel(v, locale) !== v ? shortContextLabel(v, locale) : label(v, locale))).join(" + ");
    out.push({ key, label: names[key]![zh ? 0 : 1], value: text });
  }
  return out;
}

/** Q6 copy: the second look is a question about the reader's own impression, never a correction of it. */
export function q6Copy(locale: Locale): { title: string; submit: string } {
  return locale === "zh-CN" ? { title: "哪些描述更贴近你的感受？", submit: "更新风味卡" } : { title: "Which of these are closer to what you tasted?", submit: "Update my card" };
}

/** App shell copy (owner, 2026-09-12): the slogan in English on both, the title and lead in each language, "Put this cup into words." as the action claim (the English title itself), two buttons. */
export function appShell(locale: Locale) {
  return locale === "zh-CN"
    ? {
        slogan: "Every taste has its own vocabulary.",
        title: "风味，自有表达。",
        subtitle: "像柑橘，像可可，或是某种熟悉却一时叫不出名字的味道。flavorwords 帮你找到贴近感受的词，组成这一杯的风味卡。",
        lead: "",
        claim: "Put this cup into words.",
        start: "开始",
        startLink: "从这一口开始",
        about: "关于",
        localeSwitch: "EN",
        offlineReady: "离线可用",
      }
    : {
        slogan: "Every taste has its own vocabulary.",
        title: "Put this cup into words.",
        subtitle: "Some coffees are easy to taste, but harder to describe. Find the words for what you taste, and bring them together in your own flavor card.",
        lead: "",
        claim: "",
        start: "Start",
        startLink: "Start with this sip",
        about: "About",
        localeSwitch: "中",
        offlineReady: "Works offline",
      };
}

export const contextRules = rules;

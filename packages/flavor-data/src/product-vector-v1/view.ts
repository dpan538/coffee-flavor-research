/**
 * View models for the PWA (owner, 2026-09-12): framework-agnostic props for the four screens —
 * QuizCard (C0–C2 context cards, then Q0–Q5 question cards), FirstDescriptionCard (3 + 5 words with
 * the 8-choose-5 pick matrix), ResultCard (branch A / final), EscalationModal (Q6). No styling, no
 * framework: a React or Vue component binds these objects one-to-one.
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };
import { cardCopy, type ContextAnswers, type Locale } from "./engine";
import { type Word } from "./flow";
import { nextStep, type Session } from "./session";

const rules = bundle.context_rules;
const K = bundle.matrix_k as Record<string, Record<string, { vector: number[] | null; basis: string; member_count: number | null }>>;

export type Chip = { value: string; label: string; basis: string; memberCount: number | null };
export type ContextCard =
  | { key: "c0_preparation"; title: string; chips: Chip[]; multi: false; optional: false }
  | { key: "c1_roast"; title: string; chips: Chip[]; multi: false; optional: false }
  | { key: "c2_variety"; title: string; chips: Chip[]; multi: true; max: number; toggle: { single: string; blend: string }; optional: false }
  | { key: "c2_process"; title: string; chips: Chip[]; multi: false; optional: false }
  | { key: "c2_origin"; title: string; chips: Chip[]; multi: false; optional: true; hint: string };

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
  c0_preparation: { "zh-CN": "怎么冲的？", en: "How was it brewed?" },
  c1_roast: { "zh-CN": "烘焙度", en: "Roast level" },
  c2_variety: { "zh-CN": "豆种", en: "Variety" },
  c2_process: { "zh-CN": "处理法", en: "Processing" },
  c2_origin: { "zh-CN": "产地（可选）", en: "Origin (optional)" },
};

function label(value: string, locale: Locale): string {
  return LABELS[value]?.[locale] ?? value;
}

function chips(axis: string, locale: Locale): Chip[] {
  return Object.entries(K[axis] ?? {}).map(([value, row]) => ({ value, label: label(value, locale), basis: row.basis, memberCount: row.member_count }));
}

/** The C0–C2 context cards: preparation, roast, variety (single / blend toggle, max 3), processing, optional origin. */
export function contextCatalog(locale: Locale): ContextCard[] {
  const origins = Object.entries(rules.origin_regions as Record<string, { label: Record<Locale, string>; bias: string[] }>).map(([value, r]) => ({
    value,
    label: r.label[locale],
    basis: `ORIGIN_BIAS_DELTA_${rules.origin_bias_delta}_ON_${r.bias.join("+")}`,
    memberCount: null,
  }));
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
      hint: locale === "zh-CN" ? "跳过也没关系：豆种和处理法已经决定了大部分预测" : "Skip if unsure: variety and processing already carry most of the prediction",
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

export type QuizCardModel = { kind: "question"; slot: string; prompt: string; options: Array<{ option: string; label: string }>; progress: { answered: number; expected: number } };
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
      heading: ((bundle.presentation as { preview_heading?: Record<Locale, string> }).preview_heading ?? { "zh-CN": "风味描述预览", en: "Flavor preview" })[locale],
    };
  }
  if (step.kind === "q6" && session.q6) {
    return {
      kind: "escalation",
      title: locale === "zh-CN" ? "再确认一次：勾选你确实尝到的" : "One more check: tick what you actually tasted",
      options: session.q6.options.map((o) => ({ dimension: o.dimension, text: o.text })),
      submitLabel: locale === "zh-CN" ? "生成精修风味卡" : "Refine my card",
      reason: session.gate?.reason ?? "",
    };
  }
  const card = session.card;
  const title = card?.profileTitle ?? "";
  const tags = card?.picked ?? [];
  return {
    kind: "result",
    title,
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

/** App shell copy: hero, start button, top bar — bilingual, no styling. */
export function appShell(locale: Locale) {
  return locale === "zh-CN"
    ? {
        title: "感官归因与风味诊断",
        subtitle: "感官物理学 × 12 维向量空间",
        lead: "描述直觉里的这一口，看它在物理上为什么这样。",
        start: "开始风味诊断",
        about: "关于",
        localeSwitch: "EN",
        offlineReady: "离线可用",
      }
    : {
        title: "Sensory attribution & flavor diagnosis",
        subtitle: "Sensory physics × a 12-dimension vector space",
        lead: "Describe the sip as you feel it; see why the cup tastes that way.",
        start: "Start the diagnosis",
        about: "About",
        localeSwitch: "中",
        offlineReady: "Works offline",
      };
}

export const contextRules = rules;

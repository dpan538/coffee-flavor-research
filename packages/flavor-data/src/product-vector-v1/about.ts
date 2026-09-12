/**
 * About — content only, bilingual, numbers from the bundle (owner copy review, 2026-09-12).
 * Reading order the owner asked for: what the product is for → a sample card → the author and the work →
 * the scope of the material → how a description is formed (technical notes folded) → sources.
 * No implementation vocabulary in the first screens; the formulas live under "technical notes".
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };
import { type Locale } from "./engine";

export type AboutBlock = { title: string; body: string };
export type AboutSection = { id: string; title: string; summary: string; blocks: AboutBlock[]; folded: boolean };
export type Citation = { id: string; title: string; role: string; locator: string; licence: string; evidenceState: string; claims: number; claimsLive: number; claimsPendingReview: number };
export type AboutStat = { key: string; value: number; label: string };
export type Approach = { eyebrow: string; title: string; intro: string[]; referenceTitle: string; reference: string[] };
export type ExampleCard = { eyebrow: string; title: string; words: string[]; note: string };
export type Contribution = { value: number; unit: string; label: string; use: string };
export type Author = { eyebrow: string; name: string; paragraphs: string[]; contributions: Contribution[] };
export type ScopeItem = { key: string; value: number; unit: string; label: string; note: string };
export type Scope = { title: string; items: ScopeItem[]; footnote: string };

const facts = bundle.corpus_facts;
const flow = bundle.question_flow;
type SourceRow = { source_id: string; title: string; locator: string; licence_note: string; claims: number; claims_live?: number; claims_pending_review?: number; state: string };
const P = bundle.presentation as unknown as { sources?: SourceRow[]; dimension_tags: Record<string, Record<Locale, string[]>> };
const registry = P.sources ?? [];
const live = (facts as { literature_claims_live?: number }).literature_claims_live ?? facts.literature_claims;
const pending = (facts as { literature_claims_pending_review?: number }).literature_claims_pending_review ?? 0;
const n = (v: number, locale: Locale) => v.toLocaleString(locale === "zh-CN" ? "zh-CN" : "en-US");

export function aboutTitle(locale: Locale): { title: string; subtitle: string } {
  return locale === "zh-CN" ? { title: "风味描述如何形成", subtitle: "How a flavor card is made" } : { title: "How a flavor card is made", subtitle: "风味描述如何形成" };
}

/** What flavorwords is for — the first thing About says. Owner's wording. */
export function aboutApproach(locale: Locale): Approach {
  if (locale === "zh-CN") {
    return {
      eyebrow: "关于 flavorwords",
      title: "说清这一杯的风味",
      intro: [
        "酸质像柑橘，还是青苹果？甜感接近蜂蜜，还是焦糖？一杯咖啡留下的感受，有时还需要几个合适的词才能说清楚。",
        "flavorwords 从你喝到的感受出发，围绕酸质、香气、甜感和口感，逐步缩小描述的范围。你选出贴近这一杯的词，组成自己的风味卡。",
      ],
      referenceTitle: "为日常品饮整理的参考",
      reference: [
        "产品中的风味词与参考风味，来自对咖啡评审、感官词汇和消费者表达资料的整理。它们帮助你比较不同描述，找到更接近当前感受的说法。",
        "相关的咖啡资料与研究说明，提供进一步理解这杯咖啡的参考。资料来源和使用方式列在方法说明中。",
      ],
    };
  }
  return {
    eyebrow: "About flavorwords",
    title: "Put this cup into words",
    intro: [
      "Is the acidity closer to citrus or green apple? Is the sweetness more like honey or caramel? What a coffee leaves behind sometimes takes a few well-chosen words to say.",
      "flavorwords starts from what you tasted and narrows the description step by step, through acidity, aroma, sweetness and mouthfeel. You pick the words that fit this cup, and they become your flavor card.",
    ],
    referenceTitle: "A reference for everyday drinking",
    reference: [
      "The flavor words and reference profiles come from organising public coffee reviews, sensory lexicons and consumer vocabulary. They help you compare descriptions and find the one closest to what you taste.",
      "Related coffee references and research notes offer a way to understand the cup a little further. Sources and how they are used are listed under the method notes.",
    ],
  };
}

/** A sample card, marked as a sample: the jasmine profile's words plus one acidity word from the dimension list. */
export function aboutExample(locale: Locale): ExampleCard {
  const profile = bundle.profiles.find((p) => (p as { anchor_id?: string }).anchor_id === "anchor-09") ?? bundle.profiles[0]!;
  const words = [...profile.display_tags[locale].slice(0, 4), P.dimension_tags.acidity?.[locale]?.[0] ?? ""].filter(Boolean).slice(0, 5);
  return locale === "zh-CN"
    ? { eyebrow: "示例风味卡", title: profile.owner_name[locale], words, note: "示例，不是真实结果：一次浅烘手冲的描述可能长这样。" }
    : { eyebrow: "Sample flavor card", title: profile.owner_name[locale], words, note: "A sample, not a real result: what a light-roast pour-over description might look like." };
}

/** Who did what: the owner's own boundary between their work and the sources' work; numbers tied to their use. */
export function aboutAuthor(locale: Locale): Author {
  if (locale === "zh-CN") {
    return {
      eyebrow: "研究、设计与开发",
      name: "潘岱 · Dai Pan",
      paragraphs: [
        "我整理公开咖啡评审与感官词汇资料，建立描述之间的对应关系，并设计了从品饮感受到风味卡的交互过程。flavorwords 的工作，集中在资料组织、词汇编排、提问方式和产品实现上。",
        "专业评审与研究结论来自各自的原始作者，具体来源列于资料说明中。",
      ],
      contributions: [
        { value: facts.dimensions, unit: "类", label: "风味特征", use: "每个风味词都归到其中一类；提问、出词和风味卡都按这些类取词。" },
        { value: facts.profiles, unit: "组", label: "参考风味", use: "从评审资料整理的分组，用来给出第一版描述；不是咖啡的全部分类。" },
        { value: facts.canonical_concepts, unit: "个", label: "风味词", use: "对照专业感官词汇整理的双语基础词表，加上中文消费端的补充说法。" },
      ],
    };
  }
  return {
    eyebrow: "Research, design and development",
    name: "Dai Pan · 潘岱",
    paragraphs: [
      "I organised public coffee reviews and sensory lexicons, built the correspondences between descriptions, and designed the path from what you taste to a flavor card. The work in flavorwords is in organising the material, arranging the vocabulary, the way questions are asked, and building the product.",
      "Professional reviews and research findings belong to their original authors; the sources are listed under the data notes.",
    ],
    contributions: [
      { value: facts.dimensions, unit: "", label: "flavor features", use: "every flavor word belongs to one of them; questions, suggested words and the card all draw from these." },
      { value: facts.profiles, unit: "", label: "reference profiles", use: "groups organised from the review material to give a first description; not a taxonomy of all coffee." },
      { value: facts.canonical_concepts, unit: "", label: "flavor words", use: "a bilingual base list aligned with professional lexicons, plus Chinese consumer expressions." },
    ],
  };
}

/** The scope of the material, with counting units, the subset relation and the checkpoint date. */
export function aboutScope(locale: Locale): Scope {
  const zh = locale === "zh-CN";
  const items: ScopeItem[] = [
    { key: "assertions", value: facts.source_assertions, unit: zh ? "条" : "", label: zh ? "风味描述记录" : "flavor-description records", note: zh ? "从公开评审文本中抽出的感官断言；83K 冻结检查点。" : "sensory assertions extracted from public review text; the frozen 83K checkpoint." },
    { key: "coffees", value: facts.coffees, unit: zh ? "条" : "", label: zh ? "咖啡评审记录" : "coffee review records", note: zh ? `去重后的记录数；其中 ${n(facts.usable_coffee_vectors, locale)} 条带至少一个风味词，进入参考风味分组。` : `deduplicated records; ${n(facts.usable_coffee_vectors, locale)} of them carry at least one flavor word and enter the reference-profile grouping.` },
    { key: "consumers", value: facts.consumer_respondents, unit: zh ? "位" : "", label: zh ? "消费者用词来源" : "consumers behind the vocabulary", note: zh ? "来自 GACTT 公开数据的聚合词频；不是 flavorwords 的使用者。" : "aggregate word frequencies from the public GACTT data; not users of flavorwords." },
    { key: "sources", value: facts.literature_sources, unit: zh ? "份" : "", label: zh ? "研究参考来源" : "research reference sources", note: zh ? `${live} 条说明上线，${pending} 条待复核后再展示。` : `${live} notes shown, ${pending} held back until re-verified.` },
  ];
  return { title: zh ? "资料范围" : "Scope of the material", items, footnote: zh ? `版本 ${bundle.version}，统计于 2026-09-12；去重口径与用途见方法说明。` : `Version ${bundle.version}, counted on 2026-09-12; deduplication and use are described under the method notes.` };
}

/** Flat counts, kept for consumers that want a single list (tests, exports). */
export function aboutStats(locale: Locale): AboutStat[] {
  const zh = locale === "zh-CN";
  return [
    { key: "assertions", value: facts.source_assertions, label: zh ? "条风味描述记录" : "flavor-description records" },
    { key: "coffees", value: facts.coffees, label: zh ? "条咖啡评审记录" : "coffee review records" },
    { key: "usable", value: facts.usable_coffee_vectors, label: zh ? "条进入分组的记录" : "records in the grouping" },
    { key: "consumers", value: facts.consumer_respondents, label: zh ? "位 GACTT 消费者" : "GACTT consumers" },
    { key: "concepts", value: facts.canonical_concepts, label: zh ? "个风味词" : "flavor words" },
    { key: "dimensions", value: facts.dimensions, label: zh ? "类风味特征" : "flavor features" },
    { key: "profiles", value: facts.profiles, label: zh ? "组参考风味" : "reference profiles" },
    { key: "sources", value: facts.literature_sources, label: zh ? "份研究参考来源" : "research reference sources" },
  ];
}

export function aboutCitations(locale: Locale): Citation[] {
  const zh = locale === "zh-CN";
  const roles: Record<string, [string, string]> = {
    wcr_sensory_lexicon: ["风味与香气属性的标准词汇与参照物；用于对齐 94 个风味词，以及浅、中、深烘的参考说明。", "Standard vocabulary and references for flavor and aroma attributes; used to align the 94 flavor words and for the light, medium and dark roast reference notes."],
    uc_davis_coffee_center: ["滴滤咖啡的萃取与感官研究；用于冷萃与法压的参考说明。两条关于萃取先后的说明待复核，暂不展示。", "Brewing and sensory research on drip coffee; used for the cold-brew and French-press reference notes. Two notes on extraction order are pending re-verification and are not shown."],
    coffee_ad_astra: ["滤泡咖啡萃取的物理模型；用于通道效应与萃取率的参考说明。", "A physical model of filter-coffee extraction; used for the notes on channeling and extraction yield."],
  };
  const names: Record<string, string> = {
    wcr_sensory_lexicon: "World Coffee Research (WCR) — Sensory Lexicon",
    uc_davis_coffee_center: "UC Davis Coffee Center — brewing and sensory research",
    coffee_ad_astra: "Coffee Ad Astra (Jonathan Gagné) — The Physics of Filter Coffee",
  };
  const licences: Record<string, [string, string]> = {
    wcr_sensory_lexicon: ["CC BY-SA 4.0（2026-09-12 核对）", "CC BY-SA 4.0 (checked 2026-09-12)"],
    uc_davis_coffee_center: ["学术引用 / 合理使用（2026-09-12 核对）", "Academic citation / fair use (checked 2026-09-12)"],
    coffee_ad_astra: ["个人研究引用，署名作者（2026-09-12 核对）", "Personal research citation with author attribution (checked 2026-09-12)"],
  };
  const out: Citation[] = [];
  for (const id of ["wcr_sensory_lexicon", "uc_davis_coffee_center", "coffee_ad_astra"]) {
    const row = registry.find((r) => r.source_id === id);
    out.push({
      id,
      title: names[id]!,
      role: roles[id]![zh ? 0 : 1],
      locator: row?.locator ?? "",
      licence: licences[id]![zh ? 0 : 1],
      evidenceState: row?.state ?? "PENDING_INGEST",
      claims: row?.claims ?? 0,
      claimsLive: row?.claims_live ?? row?.claims ?? 0,
      claimsPendingReview: row?.claims_pending_review ?? 0,
    });
  }
  out.push({
    id: "gactt",
    title: "Great American Coffee Taste Test (GACTT) — consumer vocabulary",
    role: zh ? `${n(facts.consumer_respondents, locale)} 位消费者盲测用词的聚合频次，不含原文；用于中文消费端词汇的对照。` : `Aggregate word frequencies from ${n(facts.consumer_respondents, locale)} consumers' blind-tasting notes, no original text; used to cross-check the Chinese consumer vocabulary.`,
    locator: "GACTT_CONSUMER_TERM_FREQUENCY.tsv",
    licence: zh ? "聚合计数，不含原文" : "aggregate counts, no text",
    evidenceState: "CORPUS_MEASURED",
    claims: 0,
    claimsLive: 0,
    claimsPendingReview: 0,
  });
  return out;
}

export type EvidenceLink = { id: string; title: string; gives: string; locator: string; licence: string; claims: number; claimsLive: number; claimsPendingReview: number; color: string };

/** The source list: what this project takes from each source, one line each. */
export function aboutEvidence(locale: Locale): EvidenceLink[] {
  const zh = locale === "zh-CN";
  const gives: Record<string, [string, string]> = {
    wcr_sensory_lexicon: ["风味属性的标准词汇与参照物", "standard vocabulary and references for flavor attributes"],
    uc_davis_coffee_center: ["滴滤萃取的分段研究与感官图谱", "fractionated drip-brew studies and sensory maps"],
    coffee_ad_astra: ["滤泡萃取的物理模型", "a physical model of filter extraction"],
    gactt: [`${n(facts.consumer_respondents, locale)} 位消费者的用词频次`, `word frequencies from ${n(facts.consumer_respondents, locale)} consumers`],
  };
  const colors: Record<string, string> = { wcr_sensory_lexicon: "#7268C9", uc_davis_coffee_center: "#2F7A4C", coffee_ad_astra: "#B97C4E", gactt: "#EE8F70" };
  return aboutCitations(locale).map((c) => ({ id: c.id, title: c.title.split(" — ")[0]!, gives: gives[c.id]![zh ? 0 : 1], locator: c.locator, licence: c.licence, claims: c.claims, claimsLive: c.claimsLive, claimsPendingReview: c.claimsPendingReview, color: colors[c.id] ?? "#999" }));
}

export function aboutSections(locale: Locale): AboutSection[] {
  const t = flow.thresholds;
  const fd = flow.first_description;
  if (locale === "zh-CN") {
    return [
      {
        id: "method",
        title: "风味描述如何形成",
        summary: "从几次选择开始，逐步缩小描述的范围，最后由你确认。",
        folded: true,
        blocks: [
          { title: "参考资料", body: `风味词与参考风味来自公开的咖啡评审文本、感官词汇表与消费者用词统计。每个词都对应到 ${facts.dimensions} 类风味特征中的一类，这样不同来源的描述才能放在一起比较。` },
          { title: "提问方式", body: "先问酸质和香气，再问甜感和口感，最后问苦感和整体印象。前两题给出一个基本方向；后面的回答如果与它不一致，就多问一题，或在出词后请你再看一眼；答案一致时少问。每个问题都有「不明显」一类的出口，不假设你一定喝到了什么。" },
          { title: "描述的选择与确认", body: `系统先给出 ${fd.main + fd.secondary} 个候选词，其中 ${fd.main} 个更可能，${fd.secondary} 个作为补充；你从中选出 ${fd.pick_count} 个，这 ${fd.pick_count} 个词就是风味卡。如果你选的词与前面的回答方向差得很远，会再请你确认一次，然后按你确认的结果更新。` },
          { title: "结果的适用范围", body: "风味卡记录的是你这次的描述，不是这杯咖啡的检测结果。参考说明来自公开资料与本项目的整理，用于帮助理解，不用于判断你喝得对不对。描述与参考的差异只作为提示，原因需要更多信息才能确定。" },
        ],
      },
      {
        id: "technical",
        title: "技术说明",
        summary: "一个投影矩阵、一组向量、余弦相似度；不训练模型。",
        folded: true,
        blocks: [
          { title: "向量与公式", body: `每类风味特征是向量的一个分量，共 ${facts.dimensions} 个分量。V_pred = normalize(Σ K)：冲煮、烘焙、豆种与处理法各自的参考向量相加；V_user = normalize(Σ Q)：每个回答的增量向量相加；ΔV = V_user − V_pred 是两者的差；V_target = normalize(V_pred + α·ΔV)，α = ${bundle.alpha_default}，再确认后 α = ${flow.alpha_strong}。` },
          { title: "相干性检查", body: `回答分组后投影到 ${facts.profiles} 组参考风味上，比较两组回答的相似度：≥ ${t.coherent} 视为一致，< ${t.mild} 视为明显不一致。另外检查烘焙方向：浅烘的酸与花香、深烘的苦与厚重同时很强时，直接进入再确认。` },
          { title: "相似度的用途", body: `余弦相似度只用于在 ${facts.profiles} 组参考风味与候选记录中找最接近的几项，再由你的选择决定；不给咖啡打分，也不输出概率。` },
          { title: "实现选择", body: "没有训练模型，没有概率拟合；全部计算在手机本地完成。这是实现方式的说明，不是质量保证。" },
        ],
      },
      {
        id: "literature",
        title: "资料来源",
        summary: `${facts.literature_sources} 份研究参考来源与一份消费者用词统计。链接与许可已列出；${pending} 条说明待复核，未上线。`,
        folded: true,
        blocks: aboutCitations("zh-CN").map((c) => ({ title: c.title, body: `${c.role}\n来源：${c.locator}\n许可：${c.licence}` })),
      },
    ];
  }
  return [
    {
      id: "method",
      title: "How a flavor card is made",
      summary: "A few choices narrow the description step by step; you confirm the result.",
      folded: true,
      blocks: [
        { title: "Reference material", body: `The flavor words and reference profiles come from public coffee review text, sensory lexicons and consumer word counts. Every word maps to one of ${facts.dimensions} flavor features, so descriptions from different sources can be compared side by side.` },
        { title: "How the questions work", body: "Acidity and aroma first, then sweetness and mouthfeel, then bitterness and the overall impression. The first two answers set a direction; if later answers disagree with it, one more question is asked, or you are asked to look again after the words appear; when answers agree, fewer questions are asked. Every question has a \"not noticeable\" way out, so nothing assumes what you must have tasted." },
        { title: "Choosing and confirming the words", body: `${fd.main + fd.secondary} candidate words are offered, ${fd.main} more likely and ${fd.secondary} as alternatives; you pick ${fd.pick_count}, and those ${fd.pick_count} are the card. If your picks point far from your earlier answers, you are asked once more, and the card is updated to what you confirm.` },
        { title: "What the result covers", body: "The card records your description of this cup, not a measurement of the coffee. The reference notes come from public sources and this project's own organisation; they are there to help you understand, not to judge whether you tasted correctly. A difference between your description and the reference is only a hint; its cause needs more information." },
      ],
    },
    {
      id: "technical",
      title: "Technical notes",
      summary: "One projection matrix, a set of vectors, cosine similarity; no model is trained.",
      folded: true,
      blocks: [
        { title: "Vectors and formulas", body: `Each flavor feature is one component of a ${facts.dimensions}-component vector. V_pred = normalize(Σ K): the reference vectors of brew, roast, variety and processing added; V_user = normalize(Σ Q): the answer increments added; ΔV = V_user − V_pred is the difference between them; V_target = normalize(V_pred + α·ΔV) with α = ${bundle.alpha_default}, and α = ${flow.alpha_strong} after a second confirmation.` },
        { title: "Coherence check", body: `Answers are grouped and projected onto the ${facts.profiles} reference profiles; the similarity of two groups is compared: ≥ ${t.coherent} counts as consistent, < ${t.mild} as clearly inconsistent. Roast direction is checked separately: strong light-roast acidity and florals together with strong dark-roast bitterness and weight go straight to a second confirmation.` },
        { title: "What similarity is used for", body: `Cosine similarity only finds the closest few among the ${facts.profiles} reference profiles and candidate records; your picks decide from there. It does not score coffees and outputs no probability.` },
        { title: "Implementation choices", body: "No model is trained and no probability is fitted; everything runs on the phone. This describes how it is built, not a guarantee of quality." },
      ],
    },
    {
      id: "literature",
      title: "Sources",
      summary: `${facts.literature_sources} research reference sources and one consumer word count. Links and licences are listed; ${pending} notes are held back until re-verified.`,
      folded: true,
      blocks: aboutCitations("en").map((c) => ({ title: c.title, body: `${c.role}\nSource: ${c.locator}\nLicence: ${c.licence}` })),
    },
  ];
}

export const aboutVersion = bundle.version;

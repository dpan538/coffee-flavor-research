/**
 * About — content only, bilingual, numbers from the bundle (owner copy review 2, 2026-09-12).
 * Default reading layer: what it is for → a sample card → the author and the work → three entries
 * (vocabulary & groups, how the questions work, data & method). Scale, charts, formulas and sources
 * stay in the expandable layers. Boundary statements live where a reader needs them, once.
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };
import { type Locale } from "./engine";

export type AboutBlock = { title: string; body: string };
export type AboutSection = { id: string; title: string; summary: string; blocks: AboutBlock[]; folded: boolean };
export type Citation = { id: string; title: string; role: string; locator: string; terms: string; use: string; evidenceState: string; claims: number; claimsLive: number; claimsPendingReview: number };
export type AboutStat = { key: string; value: number; label: string };
export type Approach = { eyebrow: string; title: string; intro: string[]; mission: string[] };
/** the sample card's three layers: the cup's info, the confirmed words, the reference entry + signature */
export type ExampleCard = { eyebrow: string; title: string; cup: Array<{ label: string; value: string }>; words: string[]; reference: string; brand: string; note: string };
export type Contribution = { value: number; unit: string; label: string; use: string };
export type Author = { eyebrow: string; title: string; name: string; paragraphs: string[]; credit: string; contributions: Contribution[] };
export type ScopeItem = { key: string; value: number; unit: string; label: string; note: string };
export type Scope = { title: string; items: ScopeItem[]; footnote: string };

const facts = bundle.corpus_facts;
const flow = bundle.question_flow;
type SourceRow = { source_id: string; title: string; locator: string; licence_note: string; terms_short?: string; use?: string; claims: number; claims_live?: number; claims_pending_review?: number; state: string };
const P = bundle.presentation as unknown as { sources?: SourceRow[]; dimension_tags: Record<string, Record<Locale, string[]>>; dimension_labels: Record<string, Record<Locale, string>> };
const registry = P.sources ?? [];
const live = (facts as { literature_claims_live?: number }).literature_claims_live ?? facts.literature_claims;
const pending = (facts as { literature_claims_pending_review?: number }).literature_claims_pending_review ?? 0;
const n = (v: number, locale: Locale) => v.toLocaleString(locale === "zh-CN" ? "zh-CN" : "en-US");

export function aboutTitle(locale: Locale): { title: string; subtitle: string } {
  return locale === "zh-CN" ? { title: "从品味，到表达", subtitle: "From tasting to words" } : { title: "From tasting to words", subtitle: "从品味，到表达" };
}

/** What flavorwords is for — the first thing About says. Owner's wording. */
export function aboutApproach(locale: Locale): Approach {
  if (locale === "zh-CN") {
    return {
      eyebrow: "关于 FLAVORWORDS",
      title: "从品味，到表达",
      intro: [
        "有时是一点花香，有时是像水果一样的酸，或是喝完之后留下的甜。你留意到的细节，构成了对这一杯咖啡的印象，却未必能立刻找到合适的词。",
        "flavorwords 将专业咖啡评审、感官词汇与日常品饮用语放在一起整理，帮助你从熟悉的味道联想，找到更具体的描述。",
        "从酸质、香气到甜感与口感，通过几次提问和选择，把这一杯的感受组成自己的风味卡。专业资料提供参照，最后由你确认。",
      ],
      mission: [],
    };
  }
  return {
    eyebrow: "About FLAVORWORDS",
    title: "From tasting to words",
    intro: [
      "Sometimes it is a touch of florals, an acidity like fruit, or the sweetness a cup leaves behind. The details you notice make up your impression of the coffee, yet the right word does not always come at once.",
      "flavorwords brings professional coffee reviews, sensory lexicons and everyday tasting language together, so you can move from familiar tastes to a more specific description.",
      "From acidity and aroma to sweetness and mouthfeel, a few questions and choices turn what you tasted into your own flavor card. Professional material provides the reference; you confirm the result.",
    ],
    mission: [],
  };
}

/** A sample card, marked as a sample: the jasmine profile's words plus one acidity word from the dimension list. */
export function aboutExample(locale: Locale): ExampleCard {
  const profile = bundle.profiles.find((p) => (p as { anchor_id?: string }).anchor_id === "anchor-09") ?? bundle.profiles[0]!;
  const words = [...profile.display_tags[locale].slice(0, 4), P.dimension_tags.acidity?.[locale]?.[0] ?? ""].filter(Boolean).slice(0, 5);
  return locale === "zh-CN"
    ? { eyebrow: "风味卡示例", title: profile.owner_name[locale], cup: [{ label: "冲煮", value: "手冲 (V60)" }, { label: "烘焙", value: "浅烘" }], words, reference: `参考风味 · ${profile.owner_name[locale]}`, brand: "flavorwords", note: "" }
    : { eyebrow: "Sample flavor card", title: profile.owner_name[locale], cup: [{ label: "Brew", value: "Pour-over (V60)" }, { label: "Roast", value: "Light" }], words, reference: `Reference · ${profile.owner_name[locale]}`, brand: "flavorwords", note: "" };
}

/** Who did what: the owner's own boundary between their work and the sources' work; numbers tied to their use. */
export function aboutAuthor(locale: Locale): Author {
  if (locale === "zh-CN") {
    return {
      eyebrow: "设计思路",
      title: "为品味而设计",
      name: "潘岱 · Dai Pan",
      paragraphs: [
        "flavorwords 将双语词汇、风味分组与匹配逻辑，整合进逐步展开的提问与选词过程。你不必翻查一整张风味词表，可以随着问题和候选描述，逐步辨认这一杯的特点。",
      ],
      credit: "研究、设计与开发：潘岱 · Dai Pan",
      contributions: [
        { value: facts.canonical_concepts, unit: "个", label: "双语风味词", use: "对照专业感官词汇整理，并补充中文品饮表达。" },
        { value: facts.dimensions, unit: "类", label: "风味特征", use: "每个风味词都归到其中一类；提问、出词和风味卡都按这些类取词。" },
        { value: facts.profiles, unit: "组", label: "参考风味", use: "本项目从评审资料整理的分组，用来给出第一版描述。" },
      ],
    };
  }
  return {
    eyebrow: "Design notes",
    title: "Designed for taste",
    name: "Dai Pan · 潘岱",
    paragraphs: [
      "flavorwords folds a bilingual vocabulary, flavor groups and matching logic into a step-by-step path of questions and word choices. Instead of reading through a whole flavor wheel, you recognise this cup's character as the questions and candidate words unfold.",
    ],
    credit: "Research, design and development: Dai Pan · 潘岱",
    contributions: [
      { value: facts.canonical_concepts, unit: "", label: "bilingual flavor words", use: "aligned with professional lexicons, with Chinese tasting expressions added." },
      { value: facts.dimensions, unit: "", label: "flavor features", use: "every flavor word belongs to one; questions, suggested words and the card all draw from them." },
      { value: facts.profiles, unit: "", label: "reference profiles", use: "groups this project organised from the review material to give a first description." },
    ],
  };
}

/** The scope of the material, with counting units and the subset relation. */
export function aboutScope(locale: Locale): Scope {
  const zh = locale === "zh-CN";
  const items: ScopeItem[] = [
    { key: "assertions", value: facts.source_assertions, unit: zh ? "条" : "", label: zh ? "风味描述记录" : "flavor-description records", note: zh ? "从公开评审文本中抽出的感官描述。" : "sensory descriptions extracted from public review text." },
    { key: "coffees", value: facts.coffees, unit: zh ? "条" : "", label: zh ? "咖啡评审记录" : "coffee review records", note: zh ? `去重后的记录数；其中 ${n(facts.usable_coffee_vectors, locale)} 条带至少一个风味词，进入参考风味分组。` : `deduplicated records; ${n(facts.usable_coffee_vectors, locale)} of them carry at least one flavor word and enter the reference-profile grouping.` },
    { key: "consumers", value: facts.consumer_respondents, unit: zh ? "位" : "", label: zh ? "GACTT 消费者研究参与者" : "GACTT consumer-study participants", note: zh ? "盲测用词的聚合频次，用于中文消费端词汇的对照；口径为研究参与者。" : "aggregate word frequencies from their blind-tasting notes, used to cross-check the Chinese consumer vocabulary; counted as study participants." },
    { key: "sources", value: registry.filter((r) => (r.claims_live ?? r.claims) > 0).length, unit: zh ? "份" : "", label: zh ? "已采用的研究参考" : "research references in use", note: zh ? `${live} 条研究说明来自这些来源；来源条款与本项目的使用方式列在下方。` : `${live} research notes come from these sources; each source's terms and this project's use are listed below.` },
  ];
  return { title: zh ? "资料范围" : "Scope of the material", items, footnote: zh ? `版本 ${bundle.version}，统计于 2026-09-12。` : `Version ${bundle.version}, counted on 2026-09-12.` };
}

/** Flat counts, kept for consumers that want a single list (tests, exports). */
export function aboutStats(locale: Locale): AboutStat[] {
  const zh = locale === "zh-CN";
  return [
    { key: "assertions", value: facts.source_assertions, label: zh ? "条风味描述记录" : "flavor-description records" },
    { key: "coffees", value: facts.coffees, label: zh ? "条咖啡评审记录" : "coffee review records" },
    { key: "usable", value: facts.usable_coffee_vectors, label: zh ? "条进入分组的记录" : "records in the grouping" },
    { key: "consumers", value: facts.consumer_respondents, label: zh ? "位 GACTT 研究参与者" : "GACTT study participants" },
    { key: "concepts", value: facts.canonical_concepts, label: zh ? "个风味词" : "flavor words" },
    { key: "dimensions", value: facts.dimensions, label: zh ? "类风味特征" : "flavor features" },
    { key: "profiles", value: facts.profiles, label: zh ? "组参考风味" : "reference profiles" },
    { key: "sources", value: facts.literature_sources, label: zh ? "份研究参考来源" : "research reference sources" },
    { key: "pending", value: pending, label: zh ? "条待复核的研究说明（内部记录）" : "research notes pending re-verification (internal record)" },
  ];
}

/** Sources in use: only those with at least one live note, plus the consumer word count. Terms and use are separate fields. */
export function aboutCitations(locale: Locale): Citation[] {
  const zh = locale === "zh-CN";
  const roles: Record<string, [string, string]> = {
    wcr_sensory_lexicon: ["风味与香气属性的标准词汇与参照物；用于对齐 94 个风味词，以及浅、中、深烘的研究说明。", "Standard vocabulary and references for flavor and aroma attributes; used to align the 94 flavor words and for the light, medium and dark roast research notes."],
    coffee_ad_astra: ["滤泡咖啡萃取的物理模型；用于通道效应与萃取率的研究说明。", "A physical model of filter-coffee extraction; used for the research notes on channeling and extraction yield."],
    uc_davis_coffee_center: ["滴滤咖啡的萃取与感官研究；相关说明待来源重新核对后再采用。", "Brewing and sensory research on drip coffee; its notes return once the source is re-established."],
  };
  const names: Record<string, string> = {
    wcr_sensory_lexicon: "World Coffee Research (WCR) — Sensory Lexicon",
    coffee_ad_astra: "Coffee Ad Astra (Jonathan Gagné) — The Physics of Filter Coffee",
    uc_davis_coffee_center: "UC Davis Coffee Center — brewing and sensory research",
  };
  const terms: Record<string, [string, string]> = {
    wcr_sensory_lexicon: ["官方页面：可免费下载、打印供个人使用；正式许可条款待核对（2026-09-12 查看）", "Official page: free download and printing for personal use; formal licence terms to be confirmed (checked 2026-09-12)"],
    coffee_ad_astra: ["作者公开博客与自出版书籍；署名引用，不转载原文", "Author's public blog and self-published book; cited with attribution, no text reproduced"],
    uc_davis_coffee_center: ["学术引用；来源待重新核对", "Academic citation; source pending re-verification"],
  };
  const uses: Record<string, [string, string]> = {
    wcr_sensory_lexicon: ["查阅属性名称与参照物定义，用于词表对齐；不转载词汇表原文", "Attribute names and reference definitions consulted for word-list alignment; no lexicon text reproduced"],
    coffee_ad_astra: ["转述萃取物理的解释，用于通道效应与萃取率两类说明", "Extraction-physics explanations paraphrased for the notes on channeling and extraction yield"],
    uc_davis_coffee_center: ["暂不采用", "Not in use"],
  };
  const out: Citation[] = [];
  for (const row of registry) {
    const id = row.source_id;
    const claimsLive = row.claims_live ?? row.claims;
    if (claimsLive <= 0) continue; // a source with nothing in use belongs to the internal record, not the reader's list
    out.push({ id, title: names[id] ?? row.title, role: roles[id]?.[zh ? 0 : 1] ?? "", locator: row.locator, terms: terms[id]?.[zh ? 0 : 1] ?? row.terms_short ?? "", use: uses[id]?.[zh ? 0 : 1] ?? row.use ?? "", evidenceState: row.state, claims: row.claims, claimsLive, claimsPendingReview: row.claims_pending_review ?? 0 });
  }
  out.sort((a, b) => ["wcr_sensory_lexicon", "coffee_ad_astra", "uc_davis_coffee_center"].indexOf(a.id) - ["wcr_sensory_lexicon", "coffee_ad_astra", "uc_davis_coffee_center"].indexOf(b.id));
  out.push({
    id: "gactt",
    title: "Great American Coffee Taste Test (GACTT) — consumer study",
    role: zh ? `${n(facts.consumer_respondents, locale)} 位参与者盲测用词的聚合频次，不含原文；用于中文消费端词汇的对照。` : `Aggregate word frequencies from ${n(facts.consumer_respondents, locale)} participants' blind-tasting notes, no original text; used to cross-check the Chinese consumer vocabulary.`,
    locator: "GACTT_CONSUMER_TERM_FREQUENCY.tsv",
    terms: zh ? "公开数据集" : "Public dataset",
    use: zh ? "只使用聚合计数，不保存原文" : "Aggregate counts only; no original text kept",
    evidenceState: "CORPUS_MEASURED",
    claims: 0,
    claimsLive: 0,
    claimsPendingReview: 0,
  });
  return out;
}

export type EvidenceLink = { id: string; title: string; gives: string; locator: string; terms: string; use: string; claims: number; claimsLive: number; color: string };

/** The source list: what this project takes from each source, one line each. */
export function aboutEvidence(locale: Locale): EvidenceLink[] {
  const zh = locale === "zh-CN";
  const gives: Record<string, [string, string]> = {
    wcr_sensory_lexicon: ["风味属性的标准词汇与参照物", "standard vocabulary and references for flavor attributes"],
    coffee_ad_astra: ["滤泡萃取的物理模型", "a physical model of filter extraction"],
    gactt: [`${n(facts.consumer_respondents, locale)} 位参与者的用词频次`, `word frequencies from ${n(facts.consumer_respondents, locale)} participants`],
  };
  const colors: Record<string, string> = { wcr_sensory_lexicon: "#7268C9", uc_davis_coffee_center: "#2F7A4C", coffee_ad_astra: "#B97C4E", gactt: "#EE8F70" };
  return aboutCitations(locale).map((c) => ({ id: c.id, title: c.title.split(" — ")[0]!, gives: gives[c.id]?.[zh ? 0 : 1] ?? c.role, locator: c.locator, terms: c.terms, use: c.use, claims: c.claims, claimsLive: c.claimsLive, color: colors[c.id] ?? "#999" }));
}

export function aboutSections(locale: Locale): AboutSection[] {
  const t = flow.thresholds;
  const fd = flow.first_description;
  const scope = aboutScope(locale);
  const scopeText = scope.items.map((s) => `${n(s.value, locale)} ${s.unit}${s.label}：${s.note}`).join("\n");
  const scopeTextEn = scope.items.map((s) => `${n(s.value, locale)} ${s.label}: ${s.note}`).join("\n");
  if (locale === "zh-CN") {
    return [
      {
        id: "vocabulary",
        title: "词汇与风味分组",
        summary: "将不同来源的风味描述进行双语对照与特征分组，把专业词汇和熟悉的品饮表达整理成可供比较的候选词，帮助你找到更贴近感受的说法。",
        folded: true,
        blocks: [
          { title: "词表", body: `风味词对照公开的感官词汇表整理，中英并列；中文一侧补充了大陆品饮时常用的说法（如酒酿、桂花、冰糖雪梨）。资料中出现过但意思不够明确的词，只用于识别输入，不作为默认推荐词。` },
          { title: "风味特征", body: `每个风味词归到 ${facts.dimensions} 类风味特征中的一类：酸质、甜感、醇厚度、花香、果香、坚果巧克力、发酵与酒香、烘烤苦感、香料、草本绿茶、木质泥土、瑕疵。不同来源的描述由此可以放在一起比较；提问、出词和风味卡都按这些类取词。` },
          { title: "参考风味", body: `${facts.profiles} 组参考风味是本项目从评审资料中整理的分组，每组以两个主要感官参照命名，用来给出第一版描述。它们是整理的结果，不是咖啡的全部分类。` },
        ],
      },
      {
        id: "questions",
        title: "随回答调整的提问",
        summary: "先从酸质与香气建立方向，再结合后续回答继续区分；需要进一步辨认时，补充一次提问或确认，让描述逐步形成。",
        folded: true,
        blocks: [
          { title: "提问顺序", body: "前两题（酸质、香气）给出一个基本方向；后面的回答如果与它不一致，就多问一题，或在出词后请你再看一眼；答案一致时少问。酸、香、甜、苦四题都有「不明显」的出口，不假设你一定喝到了什么。" },
          { title: "描述的选择与确认", body: `系统先给出 ${fd.main + fd.secondary} 个候选词：${fd.main} 个主要建议，${fd.secondary} 个备选；你从中选出 ${fd.pick_count} 个，这 ${fd.pick_count} 个词就是风味卡，卡片的分组名也按你选出的词确定。如果你选的词与前面的回答方向差得很远，会再请你看一眼，然后按你确认的结果更新。` },
        ],
      },
      {
        id: "data",
        title: "资料与方法",
        summary: "查看词汇来源、风味分组与匹配方式，了解参考描述如何形成，以及结果的适用范围。",
        folded: true,
        blocks: [
          { title: "资料范围", body: `${scopeText}\n${scope.footnote}` },
          { title: "初始参考如何形成", body: "冲煮方式、烘焙度、豆种与处理法各有一个从评审资料统计得到的参考向量，相加后就是这杯咖啡的初始参考。评审记录不足的选项（如蜜处理、湿刨法、乳酸发酵、酒桶发酵、冷萃）目前没有参考向量，选择它们不会改变初始参考。产地可选，只在花香、果香等少数特征上加一点偏置。初始参考只是起点，你的回答与选词决定最后的风味卡。" },
          { title: "结果的适用范围", body: "风味卡呈现你本次选择的描述。冲煮与豆子信息用于提供初始参考，相关研究用于补充说明；这些内容不构成对杯中成分或风味成因的测定。" },
          { title: "技术说明", body: `每类风味特征是向量的一个分量，共 ${facts.dimensions} 个分量。V_pred = normalize(Σ K)：语境的参考向量相加；V_user = normalize(Σ Q)：每个回答的增量向量相加；ΔV = V_user − V_pred；V_target = normalize(V_pred + α·ΔV)，α = ${bundle.alpha_default}，再确认后 α = ${flow.alpha_strong}。回答分组后投影到 ${facts.profiles} 组参考风味上比较相似度：≥ ${t.coherent} 视为一致，< ${t.mild} 视为明显不一致；烘焙方向单独检查。余弦相似度只用来找最接近的几组，再由你的选择决定；不给咖啡打分，也不输出概率。全部计算在手机本地完成，没有训练模型。` },
          { title: "来源", body: aboutCitations("zh-CN").map((c) => `${c.title}\n${c.role}\n来源：${c.locator}\n条款：${c.terms}\n本项目的使用：${c.use}`).join("\n\n") },
        ],
      },
    ];
  }
  return [
    {
      id: "vocabulary",
      title: "Vocabulary and flavor groups",
      summary: "Flavor descriptions from different sources are aligned in two languages and grouped by feature, so professional terms and familiar tasting expressions become candidate words you can compare and choose from.",
      folded: true,
      blocks: [
        { title: "Word list", body: "The flavor words are aligned with public sensory lexicons and given side by side in Chinese and English; the Chinese side adds expressions common in mainland tasting talk. Words that appear in the material but stay vague are used only to recognise input, never as default suggestions." },
        { title: "Flavor features", body: `Every flavor word belongs to one of ${facts.dimensions} features: acidity, sweetness, body, floral, fruity, nutty & chocolate, fermented & winey, roast & bitter, spice, herbal & green, woody & earthy, defect. Descriptions from different sources can then be compared side by side; questions, suggested words and the card all draw from these.` },
        { title: "Reference profiles", body: `The ${facts.profiles} reference profiles are groups this project organised from the review material, each named by two sensory references, used to give a first description. They are a result of that organisation, not a taxonomy of all coffee.` },
      ],
    },
    {
      id: "questions",
      title: "Questions that adapt to your answers",
      summary: "Acidity and aroma set the direction first; later answers refine it, and when something still needs telling apart, one more question or confirmation lets the description take shape.",
      folded: true,
      blocks: [
        { title: "Order", body: "The first two answers (acidity, aroma) set a direction; if later answers disagree with it, one more question is asked, or you are asked to look again after the words appear; when answers agree, fewer questions are asked. Acidity, aroma, sweetness and bitterness each have a \"not noticeable\" way out, so nothing assumes what you must have tasted." },
        { title: "Choosing and confirming the words", body: `${fd.main + fd.secondary} candidate words are offered: ${fd.main} main suggestions and ${fd.secondary} alternatives; you pick ${fd.pick_count}, those ${fd.pick_count} are the card, and the card's group name follows the words you picked. If your picks point far from your earlier answers, you are asked to look once more, and the card is updated to what you confirm.` },
      ],
    },
    {
      id: "data",
      title: "Data and method",
      summary: "Where the vocabulary comes from, how the groups and the matching work, how the reference descriptions are formed, and what the result covers.",
      folded: true,
      blocks: [
        { title: "Scope of the material", body: `${scopeTextEn}\n${scope.footnote}` },
        { title: "How the initial reference is formed", body: "Brew method, roast level, variety and processing each have a reference vector counted from the review material; added together they form this cup's initial reference. Options with too few reviews (honey, wet-hulled, lactic, barrel-aged, cold brew) have no reference vector yet, so choosing them leaves the initial reference unchanged. Origin is optional and adds only a small bias on a few features. The initial reference is a starting point; your answers and picks decide the final card." },
        { title: "What the result covers", body: "The card presents the description you chose this time. Brew and bean information provides the initial reference, and related research adds notes; none of this measures the cup's composition or the causes of its flavor." },
        { title: "Technical notes", body: `Each flavor feature is one component of a ${facts.dimensions}-component vector. V_pred = normalize(Σ K): the context reference vectors added; V_user = normalize(Σ Q): the answer increments added; ΔV = V_user − V_pred; V_target = normalize(V_pred + α·ΔV) with α = ${bundle.alpha_default}, and α = ${flow.alpha_strong} after a second confirmation. Answer groups are projected onto the ${facts.profiles} reference profiles and compared: ≥ ${t.coherent} counts as consistent, < ${t.mild} as clearly inconsistent; roast direction is checked separately. Cosine similarity only finds the closest few groups; your picks decide from there. No scores, no probabilities; everything runs on the phone and no model is trained.` },
        { title: "Sources", body: aboutCitations("en").map((c) => `${c.title}\n${c.role}\nSource: ${c.locator}\nTerms: ${c.terms}\nUse in this project: ${c.use}`).join("\n\n") },
      ],
    },
  ];
}

export const aboutVersion = bundle.version;

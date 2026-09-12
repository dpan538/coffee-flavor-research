/**
 * About — Sensory Physics & Methodology (owner copy, 2026-09-12; geek-romantic register, no sales voice).
 * Bilingual data only: sections with a short summary and folded details, merged literature + licences (folded),
 * lexicon & local autonomy (folded), and the corpus facts for the data visual. Numbers come from the bundle.
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };
import { type Locale } from "./engine";

export type AboutBlock = { title: string; body: string };
export type AboutSection = { id: string; title: string; summary: string; blocks: AboutBlock[]; folded: boolean };
export type Citation = { id: string; title: string; role: string; locator: string; licence: string; evidenceState: string; claims: number };
export type AboutStat = { key: string; value: number; label: string };

const facts = bundle.corpus_facts;
const flow = bundle.question_flow;
type SourceRow = { source_id: string; title: string; locator: string; licence_note: string; claims: number; state: string };
const registry = ((bundle.presentation as { sources?: SourceRow[] }).sources ?? []) as SourceRow[];

export function aboutTitle(locale: Locale): { title: string; subtitle: string } {
  return locale === "zh-CN" ? { title: "感官物理学与几何归因", subtitle: "Sensory Physics & Methodology" } : { title: "Sensory Physics & Methodology", subtitle: "感官物理学与几何归因" };
}

/** the data visual: what the engine was built from */
export function aboutStats(locale: Locale): AboutStat[] {
  const zh = locale === "zh-CN";
  return [
    { key: "assertions", value: facts.source_assertions, label: zh ? "条专业感官断言" : "professional sensory assertions" },
    { key: "coffees", value: facts.coffees, label: zh ? "杯经专业评审的咖啡" : "professionally reviewed coffees" },
    { key: "edges", value: facts.semantic_relation_edges, label: zh ? "条语义关系边" : "semantic relation edges" },
    { key: "consumers", value: facts.consumer_respondents, label: zh ? "位消费者的盲测笔记" : "consumers' blind-tasting notes" },
    { key: "concepts", value: facts.canonical_concepts, label: zh ? "个规范风味概念" : "canonical flavor concepts" },
    { key: "dimensions", value: facts.dimensions, label: zh ? "维正交感官空间" : "orthogonal sensory dimensions" },
    { key: "profiles", value: facts.profiles, label: zh ? "个风味画像" : "flavor profiles" },
    { key: "sources", value: facts.literature_sources, label: zh ? "份文献背书" : "literature sources" },
  ];
}

function short(title: string): string {
  return title.split(" — ")[0]!.trim();
}

export function aboutCitations(locale: Locale): Citation[] {
  const zh = locale === "zh-CN";
  const roles: Record<string, [string, string]> = {
    wcr_sensory_lexicon: ["94 个规范概念与 12 维投影标尺的标准化定义；品种基因上限（如瑰夏单萜烯表达）与烘焙演化的化学基准。", "Standard definitions behind the 94 canonical concepts and the 12-dimension projection; variety ceilings (Gesha's monoterpene expression) and roast-evolution chemistry."],
    uc_davis_coffee_center: ["萃取动力学与感官表达图谱。提取研磨度、水温与 TDS 对前段极性小分子酸与后段大分子绿原酸内酯苦感的萃取动力学释放规律。", "Brewing kinetics and sensory maps: how grind, water temperature and TDS release polar acids early and chlorogenic-acid lactone bitterness late."],
    coffee_ad_astra: ["咖啡萃取物理学。利用流体力学与粉床迁移理论，归因通道效应（Channeling）、萃取率（EY%）对中段甜感呈现与尾段瑕疵风味的物理成因。", "Physics of filter coffee: fluid dynamics and fines migration explain how channeling and extraction yield shape mid-palate sweetness and late off-notes."],
  };
  const names: Record<string, [string, string]> = {
    wcr_sensory_lexicon: ["World Coffee Research (WCR) — Sensory Lexicon & Varieties Catalog", "World Coffee Research (WCR) — Sensory Lexicon & Varieties Catalog"],
    uc_davis_coffee_center: ["UC Davis Coffee Center — Brewing Kinetics & Sensory Maps", "UC Davis Coffee Center — Brewing Kinetics & Sensory Maps"],
    coffee_ad_astra: ["Coffee Ad Astra (Dr. Christopher H. Gagné) — Physics of Filter Coffee", "Coffee Ad Astra (Dr. Christopher H. Gagné) — Physics of Filter Coffee"],
  };
  const licences: Record<string, [string, string]> = {
    wcr_sensory_lexicon: ["CC BY-SA 4.0 (Owner verified 2026-09-12)", "CC BY-SA 4.0 (owner verified 2026-09-12)"],
    uc_davis_coffee_center: ["Academic Citation / Fair Use (Owner verified 2026-09-12)", "Academic citation / fair use (owner verified 2026-09-12)"],
    coffee_ad_astra: ["Personal Research & Author Attribution (Owner verified 2026-09-12)", "Personal research & author attribution (owner verified 2026-09-12)"],
  };
  const out: Citation[] = [];
  for (const id of ["wcr_sensory_lexicon", "uc_davis_coffee_center", "coffee_ad_astra"]) {
    const row = registry.find((r) => r.source_id === id);
    out.push({ id, title: names[id]![zh ? 0 : 1], role: roles[id]![zh ? 0 : 1], locator: row?.locator ?? "", licence: licences[id]![zh ? 0 : 1], evidenceState: row?.state ?? "PENDING_INGEST", claims: row?.claims ?? 0 });
  }
  out.push({
    id: "gactt",
    title: "Great American Coffee Taste Test (GACTT) — Consumer Corpus",
    role: zh ? `${facts.consumer_respondents.toLocaleString()} 位消费者盲测笔记的纯粹聚合频次（Aggregate Frequency Counts），用于构建消费端真实用词的映射基底。` : `Pure aggregate frequency counts from ${facts.consumer_respondents.toLocaleString()} consumers' blind-tasting notes, the mapping base for real consumer vocabulary.`,
    locator: "GACTT_CONSUMER_TERM_FREQUENCY.tsv (Owner verified)",
    licence: zh ? "聚合计数，不含原文" : "aggregate counts, no text",
    evidenceState: "LITERATURE_CLAIM",
    claims: 0,
  });
  return out;
}

export type Approach = { eyebrow: string; title: string; author: string; paragraphs: string[]; problem: string[] };

/** "Our approach": why the project exists, who made it, what it answers — the first thing About says. */
export function aboutApproach(locale: Locale): Approach {
  if (locale === "zh-CN") {
    return {
      eyebrow: "Our approach",
      title: "把一口咖啡，还原成它的物理成因",
      author: "潘岱 · Dai Pan",
      problem: ["包装上的风味词是营销写的，杯子里的味道是烘焙与萃取决定的，两者之间没有一座桥。", "喝到了什么、为什么是这样、下一杯该往哪走——爱好者手边一直没有一件像样的工具。"],
      paragraphs: [
        "flavorwords 是一间放在口袋里的感官实验室。它把一口咖啡的直觉描述投影成一个向量，拿它去对照烘焙与萃取的物理先验，再用精品咖啡圈真正在用的词把结果说回来。",
        `它不训练模型，不打分，不排名。它只做三件事：把 ${facts.source_assertions.toLocaleString()} 条专业感官记录压成一个 ${facts.dimensions} 维空间，用几何而不是问卷去问，以及把每一句成因都注明出处。`,
      ],
    };
  }
  return {
    eyebrow: "Our approach",
    title: "Trace a sip back to its physics",
    author: "Dai Pan · 潘岱",
    problem: ["The flavor words on a bag are written by marketing; the taste in the cup is decided by roast and extraction, and nothing bridges the two.", "What did I taste, why, and where should the next cup go — the enthusiast never had a proper instrument for that."],
    paragraphs: [
      "flavorwords is a sensory lab that fits in a pocket. It projects the intuitive description of a sip into a vector, holds it against the physical priors of the roast and the brew, and answers in the words the specialty scene actually uses.",
      `It trains no model, gives no score, ranks nothing. It does three things: compresses ${facts.source_assertions.toLocaleString()} professional sensory records into a ${facts.dimensions}-dimension space, asks with geometry instead of a questionnaire, and cites the source of every causal sentence.`,
    ],
  };
}

export type EvidenceLink = { id: string; title: string; gives: string; locator: string; licence: string; claims: number; color: string };

/** the evidence chain: what each source gives the engine, in one line each */
export function aboutEvidence(locale: Locale): EvidenceLink[] {
  const zh = locale === "zh-CN";
  const gives: Record<string, [string, string]> = {
    wcr_sensory_lexicon: ["规范概念的标准定义、品种的基因上限", "canonical definitions, the genetic ceiling of varieties"],
    uc_davis_coffee_center: ["研磨、水温、TDS 如何先释放酸、后释放苦", "how grind, temperature and TDS release acids first and bitterness last"],
    coffee_ad_astra: ["通道效应与萃取率如何决定中段甜与尾段涩", "how channeling and extraction yield decide mid-palate sweetness and late astringency"],
    gactt: [`${facts.consumer_respondents.toLocaleString()} 位消费者真实用词的频次`, `the real vocabulary of ${facts.consumer_respondents.toLocaleString()} consumers, by frequency`],
  };
  const colors: Record<string, string> = { wcr_sensory_lexicon: "#7268C9", uc_davis_coffee_center: "#2F7A4C", coffee_ad_astra: "#B97C4E", gactt: "#EE8F70" };
  return aboutCitations(locale).map((c) => ({ id: c.id, title: c.title.split(" — ")[0]!, gives: gives[c.id]![zh ? 0 : 1], locator: c.locator, licence: c.licence, claims: c.claims, color: colors[c.id] ?? "#999" }));
}

export function aboutSections(locale: Locale): AboutSection[] {
  const t = flow.thresholds;
  if (locale === "zh-CN") {
    return [
      {
        id: "methodology",
        title: "感官物理学与几何归因",
        summary: `把风味拆成 ${facts.dimensions} 个正交维度；用向量的语义搜索给决策树剪枝，而不是给咖啡打分排序。`,
        folded: true,
        blocks: [
          { title: "动态设计", body: `问答不是问卷。每一次回答都被投影进画像空间，系统据此剪掉不可能的分支：回答相干时少问，出现分歧时多问一道，遇到物理悖论时直接拦截。平均 ${facts.mean_questions} 道题收敛，最多六道。` },
          { title: "公式设计", body: "V_pred = normalize(Σ K)，由冲煮、烘焙、豆种与处理法的先验向量相加；V_user = normalize(Σ Q)，由回答的增量向量相加；ΔV = V_user − V_pred 是感知偏置；V_target = normalize(V_pred + α·ΔV)，α = 0.5。全链路只有一个投影矩阵、一组向量和余弦相似度。不训练模型，不做概率拟合，不做统计校准。" },
          { title: "语义搜索，不是排序", body: `余弦相似度只用来在 ${facts.profiles} 个画像与候选豆之间做语义检索与剪枝——找到最接近的那一小撮，再由你的勾选定夺。它从不给咖啡打分排名，也不输出概率。` },
          { title: "相干与极性", body: `Q0–Q1 锁定基底，Q2–Q3 在画像签名空间里做相干性投影（相干 ≥ ${t.coherent}，冲突 < ${t.mild}）。签名空间由 ${facts.usable_coffee_vectors.toLocaleString()} 笔专业感官记录聚成 ${facts.profiles} 个画像。极性守卫在签名之外单独校验烘焙极性：极浅烘高酸花香与深烘重苦厚重不能同时成立，悖论直接进入强修正；冲煮与烘焙先验只引导修正，不越权。` },
        ],
      },
      {
        id: "literature",
        title: "数据与文献",
        summary: "每一句成因都带出处。三份文献背书萃取与品种的物理化学机理，一份消费者语料校准用词。",
        folded: true,
        blocks: aboutCitations("zh-CN").map((c) => ({ title: c.title, body: `${c.role}\n出底：${c.locator}\n许可：${c.licence}` })),
      },
    ];
  }
  return [
    {
      id: "methodology",
      title: "Sensory physics & geometric attribution",
      summary: `Flavor is split into ${facts.dimensions} orthogonal dimensions; vector semantic search prunes the decision tree — it never ranks coffees.`,
      folded: true,
      blocks: [
        { title: "Dynamic design", body: `This is not a questionnaire. Every answer is projected into profile space and the system prunes what cannot be: fewer questions when answers cohere, one more when they diverge, a hard stop on physical paradoxes. Paths converge in ${facts.mean_questions} questions on average, six at most.` },
        { title: "Formula design", body: "V_pred = normalize(Σ K), the prior vectors of brew, roast, variety and processing added; V_user = normalize(Σ Q), the answer increments added; ΔV = V_user − V_pred is the perception bias; V_target = normalize(V_pred + α·ΔV) with α = 0.5. The whole chain is one projection matrix, a set of vectors and cosine similarity. No model is trained, no probability fitted, no statistical calibration." },
        { title: "Semantic search, not ranking", body: `Cosine similarity is used only to search and prune among the ${facts.profiles} profiles and candidate beans — to find the closest few, which your picks then settle. It never scores or ranks coffees and never outputs a probability.` },
        { title: "Coherence and polarity", body: `Q0–Q1 lock the base; Q2–Q3 are projected against it in profile-signature space (coherent ≥ ${t.coherent}, conflict < ${t.mild}). That space is ${facts.profiles} profiles clustered from ${facts.usable_coffee_vectors.toLocaleString()} professional sensory records. A polarity guard checks roast polarity outside the signature: very-light-roast florals and dark-roast heaviness cannot both hold, so the paradox goes straight to correction; brew and roast priors only steer, never override.` },
      ],
    },
    {
      id: "literature",
      title: "Data and literature",
      summary: "Every attribution carries its source. Three references back the physics and chemistry of extraction and variety; one consumer corpus calibrates the words.",
      folded: true,
      blocks: aboutCitations("en").map((c) => ({ title: c.title, body: `${c.role}\nSource: ${c.locator}\nLicence: ${c.licence}` })),
    },
  ];
}

export const aboutVersion = bundle.version;

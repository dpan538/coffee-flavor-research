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

export function aboutFooter(locale: Locale): string {
  return locale === "zh-CN" ? "无服务器，无账号，无追踪。每一次诊断、每一个向量和自建豆库都只在这台设备的本地存储里，随时可清空。" : "No server, no account, no tracking. Every diagnosis, vector and bean stays in this device's local storage and can be cleared any time.";
}

export function aboutSections(locale: Locale): AboutSection[] {
  const t = flow.thresholds;
  if (locale === "zh-CN") {
    return [
      {
        id: "methodology",
        title: "方法",
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
      title: "Method",
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

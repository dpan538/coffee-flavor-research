/**
 * About / methodology content for the PWA (owner plan, 2026-09-12). Bilingual, offline, data only —
 * the page renders these sections; the numbers are read from the bundle so they never go stale.
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };
import { type Locale } from "./engine";

export type AboutSection = { id: string; title: string; paragraphs: string[]; bullets?: string[] };
export type Citation = { id: string; title: string; role: string; evidenceState: "LITERATURE_CLAIM" | "PENDING_INGEST"; locator: string };

const flow = bundle.question_flow;
const dims = bundle.dimensions.length;
const profiles = bundle.profiles.length;
const concepts = Object.keys(bundle.concept_projection).length;
const ingested = bundle.presentation.context_statements.filter((s) => s.evidence_state === "LITERATURE_CLAIM").length;

export function aboutCitations(locale: Locale): Citation[] {
  const state = ingested > 0 ? "LITERATURE_CLAIM" : "PENDING_INGEST";
  return locale === "zh-CN"
    ? [
        { id: "wcr", title: "World Coffee Research — Sensory Lexicon / Varieties Catalog", role: "94 个规范风味概念与 12 维投影标尺的标准化定义；品种的感官潜能", evidenceState: state, locator: "db/data/external-literature/wcr_sensory_lexicon.claims.csv" },
        { id: "ucdavis", title: "UC Davis Coffee Center", role: "萃取动力学与感官图谱：研磨度、水温、TDS 对前段极性小分子酸与后段大分子苦感的释放规律", evidenceState: state, locator: "db/data/external-literature/uc_davis_coffee_center.claims.csv" },
        { id: "adastra", title: "Coffee Ad Astra (Jonathan Gagné)", role: "咖啡萃取物理学：通道效应、萃取率（EY%）对中段甜感与尾段缺陷风味的归因", evidenceState: state, locator: "db/data/external-literature/coffee_ad_astra.claims.csv" },
        { id: "gactt", title: "Great American Coffee Taste Test (GACTT)", role: "4,042 位消费者的盲测笔记：消费端风味用语的频次基底（只用聚合计数）", evidenceState: "LITERATURE_CLAIM", locator: "db/data/product-vector-v1/GACTT_CONSUMER_TERM_FREQUENCY.tsv" },
      ]
    : [
        { id: "wcr", title: "World Coffee Research — Sensory Lexicon / Varieties Catalog", role: "standard definitions behind the 94 canonical concepts and the 12-dimension projection; variety sensory potential", evidenceState: state, locator: "db/data/external-literature/wcr_sensory_lexicon.claims.csv" },
        { id: "ucdavis", title: "UC Davis Coffee Center", role: "brewing kinetics and sensory maps: how grind, temperature and TDS release polar acids early and large bitter molecules late", evidenceState: state, locator: "db/data/external-literature/uc_davis_coffee_center.claims.csv" },
        { id: "adastra", title: "Coffee Ad Astra (Jonathan Gagné)", role: "physics of extraction: channeling and extraction yield versus mid-palate sweetness and late off-notes", evidenceState: state, locator: "db/data/external-literature/coffee_ad_astra.claims.csv" },
        { id: "gactt", title: "Great American Coffee Taste Test (GACTT)", role: "blind-tasting notes from 4,042 consumers: the frequency base of consumer flavor language (aggregate counts only)", evidenceState: "LITERATURE_CLAIM", locator: "db/data/product-vector-v1/GACTT_CONSUMER_TERM_FREQUENCY.tsv" },
      ];
}

export function aboutSections(locale: Locale): AboutSection[] {
  const t = flow.thresholds;
  if (locale === "zh-CN") {
    return [
      {
        id: "methodology",
        title: "核心方法论",
        paragraphs: [
          `${dims} 维感官向量空间：系统放弃营销式的模糊形容词，把香气、酸质、甜感、体感、发酵感、烘烤、香料、草本、木质与瑕疵拆成 ${dims} 个几何维度。${concepts} 个规范风味概念各自投影到这个空间；一杯咖啡、一个画像、一次回答，都是同一空间里的向量。`,
          `相干性校验与动态纠错：回答不是逐题累加，而是分组比对。系统先用 Q0–Q1 建立感知基底，再用 Q2–Q3 做相干性评估（相干 ≥ ${t.coherent}，冲突 < ${t.mild}），在画像签名空间里问「这些回答指向同一批风味画像吗」；极性守卫拦截「极浅烘高酸花香 + 深烘重苦厚重」这类感官悖论，语境检查让冲煮与烘焙参数只引导修正、不越权。平均 5.70 题完成。`,
          `第一份风味描述给出 3 + 5 个词，你勾选 5 个最贴切的；这次勾选是隐式的强信号。只有当前文出现过严重冲突且你的勾选证实了感官偏置时，才会出现 Q6 强修正，得到第二份精修卡。`,
        ],
        bullets: [`${profiles} 个风味画像，由 8,142 杯专业评审记录聚类而来，命名采用中国精品咖啡圈的通用词汇`, "所有分数都是余弦相似度，不是概率，未做校准", "系统从不训练模型：一个投影矩阵、一组向量、一行余弦"],
      },
      {
        id: "literature",
        title: "学术文献与理论支持",
        paragraphs: ["归因文案的每一句都带证据级别：OWNER_STATEMENT（产品方陈述）、CORPUS_MEASURED（从 83,031 条专业评审断言实测）、LITERATURE_CLAIM（引自下列文献）。"],
        bullets: aboutCitations("zh-CN").map((c) => `${c.title} — ${c.role}`),
      },
      {
        id: "lexicon",
        title: "极简风味词典与数据血缘",
        paragraphs: [
          "卡片上的词（如 白花 | 水蜜桃 | 茉莉绿茶 | 杏桃）来自两层词典：94 个规范概念的中文极简词，以及从 GACTT 消费者盲测语料与国内消费端语料收敛的本土词（野果发酵、微醺酒香、冰糖雪梨、鸭屎香……）。专业端的长句描述只用于计算，从不直接展示。",
          "隐私：本应用没有后端服务器、没有账号。所有诊断交互、历史记录与你录入的豆子都只保存在你手机本地（IndexedDB），可以随时清空。",
        ],
      },
    ];
  }
  return [
    {
      id: "methodology",
      title: "Methodology",
      paragraphs: [
        `A ${dims}-dimension sensory vector space: instead of marketing adjectives, aroma, acidity, sweetness, body, fermentation, roast, spice, herbal, woody and defect become ${dims} geometric axes. ${concepts} canonical flavor concepts project into this space; a cup, a profile and an answer are all vectors in it.`,
        `Coherence checks with dynamic correction: answers are compared in groups, not summed. Q0–Q1 set the perceptual base; Q2–Q3 are checked against it (coherent ≥ ${t.coherent}, conflict < ${t.mild}) in profile-signature space — "do these answers point at the same profiles?". A polarity guard intercepts sensory paradoxes (light-roast florals and acidity followed by heavy dark bitterness); the context check lets brew and roast parameters guide a correction without overriding perception. 5.70 questions on average.`,
        "The first description offers 3 + 5 words and asks you to pick the 5 that fit; that pick is a strong implicit signal. Only when the flow saw a severe conflict and your picks confirm the bias does a Q6 correction appear, producing a refined second card.",
      ],
      bullets: [`${profiles} flavor profiles clustered from 8,142 professionally reviewed coffees, named in the vocabulary of the Chinese specialty scene`, "every score is a cosine similarity, never a probability, uncalibrated", "no model is ever trained: one projection matrix, a set of vectors, a cosine"],
    },
    {
      id: "literature",
      title: "Literature and theoretical basis",
      paragraphs: ["Every attribution sentence carries its evidence state: OWNER_STATEMENT, CORPUS_MEASURED (from 83,031 professional review assertions) or LITERATURE_CLAIM (from the sources below)."],
      bullets: aboutCitations("en").map((c) => `${c.title} — ${c.role}`),
    },
    {
      id: "lexicon",
      title: "Lexicon and provenance",
      paragraphs: [
        "Card words (白花 | 水蜜桃 | 茉莉绿茶 | 杏桃, or jasmine | peach | green tea | apricot) come from two layers: minimalist words for the 94 canonical concepts, and consumer terms converged from GACTT blind-tasting notes and Chinese consumer language. Long professional descriptions are used for computation only, never shown.",
        "Privacy: no server, no account. Every diagnosis, its history and the beans you enter stay on your device (IndexedDB) and can be cleared at any time.",
      ],
    },
  ];
}

export const aboutVersion = bundle.version;

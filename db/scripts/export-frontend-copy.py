#!/usr/bin/env python3
"""Export every user-facing string of the PWA into one Markdown document for the owner's review.

Sources: the runtime bundle (question bank, context labels, profile names and tags, evidence labels, calibration
templates, headings, context statements, dimension / concept / consumer words) plus the strings hard-coded in the
Vue components and view.ts (kept in COMPONENT_STRINGS below — update it when a component string changes).
Output: docs/product/FRONTEND_COPY_REVIEW.md
"""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = json.loads((ROOT / "db" / "data" / "product-vector-v1" / "product-vector-v1.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs" / "product" / "FRONTEND_COPY_REVIEW.md"
P = B["presentation"]

# strings that live in components / view.ts (not in the bundle)
COMPONENT_STRINGS = {
    "首页 Hero（view.ts appShell）": [
        ("标题", "感官归因与风味诊断", "Sensory attribution & flavor diagnosis"),
        ("副标题", "感官物理学 × 12 维向量空间", "Sensory physics × a 12-dimension vector space"),
        ("导言", "描述直觉里的这一口，看它在物理上为什么这样。", "Describe the sip as you feel it; see why the cup tastes that way."),
        ("开始按钮", "开始风味诊断", "Start the diagnosis"),
        ("About 按钮 aria", "关于", "About"),
        ("语言切换", "EN", "中"),
        ("离线标记 title", "离线可用", "Works offline"),
    ],
    "语境卡 ContextSetupCard": [
        ("小标签", "这杯咖啡", "This cup"),
        ("C0 标题", "怎么冲的？", "How was it brewed?"), ("C1 标题", "烘焙度", "Roast level"), ("C2 标题", "豆种", "Variety"), ("处理法标题", "处理法", "Processing"), ("产地标题", "产地（可选）", "Origin (optional)"),
        ("产地提示", "跳过也没关系：豆种和处理法已经决定了大部分预测", "Skip if unsure: variety and processing already carry most of the prediction"),
        ("单品 / 拼配切换", "单品 SOE ｜ 拼配 Blend ≤ 3", "Single origin ｜ Blend ≤ 3"),
        ("下一步 / 跳过", "下一步 ｜ 跳过", "Next ｜ Skip"),
        ("C0 选项", "手冲 (V60) ｜ 法压 ｜ 意式浓缩 ｜ 冷萃", "Pour-over (V60) ｜ French press ｜ Espresso ｜ Cold brew"),
        ("C1 选项", "极浅烘 ｜ 浅烘 ｜ 中浅烘 ｜ 中烘 ｜ 中深烘 ｜ 深烘 ｜ 极深烘", "Very light ｜ Light ｜ Medium-light ｜ Medium ｜ Medium-dark ｜ Dark ｜ Very dark"),
        ("C2 豆种选项", "波本 Bourbon ｜ 卡斯蒂略 Castillo ｜ 卡杜艾 Catuai ｜ 卡杜拉 Caturra ｜ 埃塞原生种 Heirloom ｜ 瑰夏 Gesha ｜ 帕卡马拉 Pacamara ｜ 罗布斯塔 Robusta ｜ SL28 / SL34 ｜ 铁皮卡 Typica", "Bourbon ｜ Castillo ｜ Catuai ｜ Caturra ｜ Ethiopian landrace ｜ Gesha ｜ Pacamara ｜ Robusta ｜ SL28 / SL34 ｜ Typica"),
        ("处理法选项", "水洗 ｜ 日晒 ｜ 厌氧发酵 ｜ 低因", "Washed ｜ Natural ｜ Anaerobic ｜ Decaf"),
    ],
    "题卡 QuizCard": [("小标签", "这一口", "This sip")],
    "第一次出卡 FirstDescriptionCard": [("提交按钮", "生成我的风味卡", "Make my card")],
    "Q6 EscalationModal": [("小标签", "再确认一次", "One more check"), ("标题", "再确认一次：勾选你确实尝到的", "One more check: tick what you actually tasted"), ("提交按钮", "生成精修风味卡", "Refine my card")],
    "终卡 FinalAttributionCard": [("精修标记", "精修", "refined"), ("底部 icon aria", "首页 ｜ 重新体验 ｜ 分享", "Home ｜ Start over ｜ Share")],
    "上方堆叠 CollectedStack": [("勾选卡标题", "你的 5 个词", "Your 5 words"), ("收集中 aria", "收集中", "collecting")],
    "About 抽屉 AboutDrawer": [
        ("关闭 aria", "关闭", "Close"), ("展开 / 收起", "展开 ｜ 收起", "Details ｜ Collapse"),
        ("数据流标题", "数据从哪来，变成了什么", "Where the data came from, what it became"),
        ("数据流注", "左：来源评审族与咖啡数；右：12 个维度；带宽是该来源在该维度上的质量", "left: source panels and their coffees; right: the 12 dimensions; ribbon width is that source's mass on that dimension"),
        ("光谱标题", "十六个风味画像", "Sixteen flavor profiles"),
        ("光谱注", "每一道射线是一个画像，长度按咖啡数的对数刻度，刻度色是它在各维度上的重心", "each ray is a profile, length on a log scale of its coffees, tick colours its weight across the dimensions"),
        ("证据链标题", "证据链", "Evidence chain"), ("证据链行前缀", "给引擎的是", "gives the engine"),
        ("来源族名", "CoffeeReview 编辑评审 ｜ Cup of Excellence 评审 ｜ Q-grader 储藏实验 ｜ Q-grader 数据集 ｜ 罗布斯塔 Q-grader 评审 ｜ 其他评审", "CoffeeReview editorial reviews ｜ Cup of Excellence juries ｜ Q-grader storage panel ｜ Q-grader dataset ｜ Robusta Q-grader panel ｜ other panels"),
    ],
}


def esc(s: str) -> str:
    return s.replace("|", "｜").replace("\n", "<br>")


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(esc(str(c)) for c in r) + " |")
    return "\n".join(out)


def main() -> int:
    md = ["# flavorwords 前端文案总表（审核稿）", "", f"自动导出自 `product-vector-v1.json`（{B['version']}）与组件内固定文案。每一行都是用户会在屏幕上看到的字。修改后请告诉我改哪一行，我改源头再重新导出。", ""]
    md += ["## 1. 界面固定文案（组件与 view.ts）", ""]
    for section, rows in COMPONENT_STRINGS.items():
        md += [f"### {section}", "", table(["位置", "中文", "English"], rows), ""]
    md += ["## 2. 卡片标题与折叠层标签（bundle.presentation）", ""]
    rows = [("第一次出卡标题", P["preview_heading"]["zh-CN"], P["preview_heading"]["en"]), ("终卡标题", P["card_heading"]["zh-CN"], P["card_heading"]["en"]), ("折叠层标题", P["science_heading"]["zh-CN"], P["science_heading"]["en"]), ("引用前缀", P["citation_prefix"]["zh-CN"], P["citation_prefix"]["en"])]
    for k, v in P["evidence_labels"].items():
        rows.append((f"证据级别标签 {k}", v["zh-CN"], v["en"]))
    for k in ("pos", "neg"):
        rows.append((f"偏置句模板 {k}", P["delta_templates"]["zh-CN"][k], P["delta_templates"]["en"][k]))
    rows.append(("勾选提示（describe）", f"请勾选出你觉得最符合你当前体验的 {B['question_flow']['first_description']['pick_count']} 个风味描述", f"Pick the {B['question_flow']['first_description']['pick_count']} words that best match what you tasted"))
    md += [table(["位置", "中文", "English"], rows), ""]
    md += ["## 3. 题库 Q0–Q5（bundle.question_bank）", ""]
    rows = []
    for slot, q in B["question_bank"].items():
        rows.append((slot, "提问", q["prompt"]["zh-CN"], q["prompt"]["en"]))
        for opt, spec in q["options"].items():
            rows.append((slot, f"选项 {opt}", spec["label"]["zh-CN"], spec["label"]["en"]))
    md += [table(["题", "位置", "中文", "English"], rows), ""]
    md += ["## 4. 十六个风味画像（终卡标题与标签）", ""]
    rows = [(p["owner_name"]["zh-CN"], p["owner_name"]["en"], " ｜ ".join(p["display_tags"]["zh-CN"]), " ｜ ".join(p["display_tags"]["en"]), p["benchmark_beans"], p["member_count"]) for p in B["profiles"]]
    md += [table(["中文名", "English", "标签 zh", "tags en", "标杆豆款", "咖啡数"], rows), ""]
    md += ["## 5. 维度词（描述与勾选时按维度取的词）", ""]
    rows = [(d, P["dimension_labels"][d]["zh-CN"], P["dimension_labels"][d]["en"], " ｜ ".join(P["dimension_tags"][d]["zh-CN"]), " ｜ ".join(P["dimension_tags"][d]["en"]), " ｜ ".join(P["consumer_terms"].get(d, {}).get("zh-CN", [])), " ｜ ".join(P["consumer_terms"].get(d, {}).get("en", []))) for d in B["dimensions"]]
    md += [table(["维度", "标签 zh", "label en", "维度词 zh", "words en", "消费端补充 zh", "consumer en"], rows), ""]
    md += ["## 6. 94 个规范概念的极简词（用户录入豆子时上卡）", ""]
    rows = [(k.removeprefix("sensory."), v["zh-CN"], v["en"]) for k, v in sorted(P["concept_tags"].items())]
    md += [table(["概念", "中文", "English"], rows), ""]
    md += ["## 7. 科学归因句（折叠层里的成因句）", ""]
    rows = [(s["context_id"], P["evidence_labels"].get(s["evidence_state"], {}).get("zh-CN", s["evidence_state"]), s["zh-CN"], s["en"], (s.get("source_title") or "").split(" — ")[0]) for s in P["context_statements"]]
    md += [table(["语境", "标签", "中文", "English", "出处"], rows), ""]
    md += ["## 8. About（about.ts）", "", "About 的正文（our approach、感官物理学与几何归因四段、证据链四条）见 `packages/flavor-data/src/product-vector-v1/about.ts`，中英并列；本表只列标题级文案：", ""]
    rows = [("Eyebrow", "Our approach", "Our approach"), ("标题", "把一口咖啡，还原成它的物理成因", "Trace a sip back to its physics"), ("作者", "潘岱 · Dai Pan", "Dai Pan · 潘岱"),
            ("问题 1", "包装上的风味词是营销写的，杯子里的味道是烘焙与萃取决定的，两者之间没有一座桥。", "The flavor words on a bag are written by marketing; the taste in the cup is decided by roast and extraction, and nothing bridges the two."),
            ("问题 2", "喝到了什么、为什么是这样、下一杯该往哪走——爱好者手边一直没有一件像样的工具。", "What did I taste, why, and where should the next cup go — the enthusiast never had a proper instrument for that."),
            ("段 1", "flavorwords 是一间放在口袋里的感官实验室。它把一口咖啡的直觉描述投影成一个向量，拿它去对照烘焙与萃取的物理先验，再用精品咖啡圈真正在用的词把结果说回来。", "flavorwords is a sensory lab that fits in a pocket. It projects the intuitive description of a sip into a vector, holds it against the physical priors of the roast and the brew, and answers in the words the specialty scene actually uses."),
            ("段 2", "它不训练模型，不打分，不排名。它只做三件事：把 83,031 条专业感官记录压成一个 12 维空间，用几何而不是问卷去问，以及把每一句成因都注明出处。", "It trains no model, gives no score, ranks nothing. It does three things: compresses 83,031 professional sensory records into a 12-dimension space, asks with geometry instead of a questionnaire, and cites the source of every causal sentence."),
            ("方法段标题", "感官物理学与几何归因", "Sensory physics & geometric attribution"),
            ("方法段摘要", "把风味拆成 12 个正交维度；用向量的语义搜索给决策树剪枝，而不是给咖啡打分排序。", "Flavor is split into 12 orthogonal dimensions; vector semantic search prunes the decision tree — it never ranks coffees."),
            ("方法四小节标题", "动态设计 ｜ 公式设计 ｜ 语义搜索，不是排序 ｜ 相干与极性", "Dynamic design ｜ Formula design ｜ Semantic search, not ranking ｜ Coherence and polarity"),
            ("数据标签", "条专业感官断言 ｜ 杯经专业评审的咖啡 ｜ 条语义关系边 ｜ 位消费者的盲测笔记", "professional sensory assertions ｜ professionally reviewed coffees ｜ semantic relation edges ｜ consumers' blind-tasting notes"),
            ("证据链四条", "World Coffee Research (WCR) ｜ UC Davis Coffee Center ｜ Coffee Ad Astra (Dr. Christopher H. Gagné) ｜ Great American Coffee Taste Test (GACTT)", "same"),
            ("证据链 gives", "规范概念的标准定义、品种的基因上限 ｜ 研磨、水温、TDS 如何先释放酸、后释放苦 ｜ 通道效应与萃取率如何决定中段甜与尾段涩 ｜ 4,042 位消费者真实用词的频次", "canonical definitions, the genetic ceiling of varieties ｜ how grind, temperature and TDS release acids first and bitterness last ｜ how channeling and extraction yield decide mid-palate sweetness and late astringency ｜ the real vocabulary of 4,042 consumers, by frequency")]
    md += [table(["位置", "中文", "English"], rows), ""]
    OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"written {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

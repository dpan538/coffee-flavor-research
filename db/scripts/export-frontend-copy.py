#!/usr/bin/env python3
"""Export every user-facing string of the PWA into one Markdown document for the owner's review.

Sources, in order of trust:
  1. the runtime bundle (question bank, context labels, profile names and tags, evidence labels, difference
     templates, headings, context statements, dimension / concept / consumer words);
  2. the TypeScript copy modules view.ts (hero, context titles, origin hint, Q6) and about.ts (the whole About page),
     executed through esbuild + node so the document cannot drift from the code;
  3. the few strings hard-coded in Vue components (COMPONENT_STRINGS below — update it when a component string changes).
Output: docs/product/FRONTEND_COPY_REVIEW.md
"""
from __future__ import annotations
import json, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = json.loads((ROOT / "db" / "data" / "product-vector-v1" / "product-vector-v1.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs" / "product" / "FRONTEND_COPY_REVIEW.md"
P = B["presentation"]
SRC = ROOT / "packages" / "flavor-data" / "src" / "product-vector-v1"

# strings that live in Vue components (not in the bundle, not in view.ts / about.ts)
COMPONENT_STRINGS = {
    "首页 App.vue": [("两个按钮", "开始 ｜ 关于", "Start ｜ About"), ("几何图形（三套组合共用一种语言）", "首页：四格邮票带（色底 + 奶白形）；About：六格拼布；风味卡：按所选词特征色的一排小格（四分圆 / 圆 / 半圆 / 三角 / 菱形），形状都在格内", "home: a four-tile stamp band (coloured ground + cream shape); About: a six-tile quilt; card: a row of small tiles in the words' colours (quarter / circle / half / triangle / diamond), every shape inside its box"), ("大标题", "Every taste has its own vocabulary.（taste 五个字母各一种高亮色）", "Every taste has its own vocabulary. (the five letters of taste, one bright colour each)")],
    "风味卡 FlavorCard（终卡）": [("三层", "上：冲煮 / 烘焙 / 豆种 / 处理 / 产地（只列已填的）；中：5 个词等大；下：参考风味 · 分组名 ｜ flavorwords", "top: Brew / Roast / Variety / Process / Origin (entered only); middle: the 5 words at equal weight; bottom: Reference · group ｜ flavorwords")],
    "语境卡 ContextSetupCard": [
        ("小标签", "这杯咖啡", "This cup"),
        ("单品 / 拼配切换后缀", "≤ 3", "≤ 3"),
        ("下一步 / 跳过 / 已选", "下一步 ｜ 跳过 ｜ 已选", "Next ｜ Skip ｜ chosen"),
        ("产地分组标题", "非洲 ｜ 亚洲 ｜ 美洲", "Africa ｜ Asia ｜ Americas"),
    ],
    "题卡 QuizCard": [("小标签", "这一口", "This sip")],
    "第一次出卡 FirstDescriptionCard": [("提交按钮", "确认风味卡", "Confirm my card")],
    "Q6 EscalationModal": [("小标签", "再看一眼", "One more look")],
    "终卡 FinalAttributionCard": [("再确认后的标记", "已确认", "confirmed"), ("参考行前缀", "参考风味", "Reference"), ("底部 icon aria", "首页 ｜ 重新体验 ｜ 分享（导出 1200×1200 PNG）", "Home ｜ Start over ｜ Share (exports a 1200×1200 PNG)"), ("操作区 aria", "操作", "Actions"), ("PNG 上的字", "风味卡 ｜ 参考风味 · … ｜ flavorwords", "FLAVOR CARD ｜ Reference · … ｜ flavorwords")],
    "上方堆叠 CollectedStack": [("勾选卡标题", "候选风味描述", "Candidate descriptions"), ("收集中 aria", "收集中", "collecting")],
    "About 抽屉 AboutDrawer（五页）": [
        ("关闭 aria / 滑动提示", "关闭 ｜ 向下滑动", "Close ｜ Scroll"), ("展开 / 收起", "展开 ｜ 收起", "Details ｜ Collapse"),
        ("第三页导语（无标题）", "十二类风味特征在全部评审记录里的累计权重（对数刻度）；深浅是来源评审族，字母下是各自占比。", "Twelve flavor features by cumulative weight across every review record (log scale); shades are the review panels, the share sits under each letter."),
        ("第三页主干", "8,142 条记录 → 整理为 16 组参考风味", "8,142 records → organised into 16 reference profiles"),
        ("第四页标题", "本项目整理的 16 组参考风味", "16 reference profiles organised by this project"),
        ("第四页导语", "大小按记录数，颜色是该组最强的风味特征；内圈是记录最多的 6 组。白线连到最接近的两组，C1–C6 是最接近的几对。", "Size by records, colour by the group's strongest feature; the inner ring holds the 6 largest. Curves join the two nearest groups, C1–C6 the closest pairs."),
        ("第四页环与注释", "记录最多的 6 组 ｜ 其余 10 组 ｜ 条记录", "the 6 largest ｜ the other 10 ｜ records"),
        ("来源页（独立一页，右下角 TOP）", "引用与来源 ｜ 本项目的使用 ｜ 链接与条款 ｜ 来源条款 ｜ ↑ TOP", "Citations and sources ｜ Use in this project ｜ Link and terms ｜ Source terms ｜ ↑ TOP"),
        ("来源族名", "CoffeeReview 编辑评审 ｜ Cup of Excellence 评审 ｜ Q-grader 数据集 ｜ 罗布斯塔 Q-grader 评审 ｜ Project Origin 评审 ｜ Cenicafé 受训杯测师 ｜ 印度咖啡局 Fine Cup ｜ 也门 Sheba 拍卖评审", "CoffeeReview editorial reviews ｜ Cup of Excellence juries ｜ Q-grader dataset ｜ Robusta Q-grader panel ｜ Project Origin panel ｜ Cenicafé trained cuppers ｜ Coffee Board of India Fine Cup ｜ Sheba Yemen auction panel"),
    ],
}

DUMP_ENTRY = """
import { appShell, contextCatalog, q6Copy } from "%(src)s/view.ts";
import * as about from "%(src)s/about.ts";
const out = {};
for (const locale of ["zh-CN", "en"]) {
  out[locale] = {
    shell: appShell(locale),
    context: contextCatalog(locale).map((c) => ({ key: c.key, title: c.title, chips: c.chips.map((x) => x.label), hint: c.hint ?? "", toggle: c.toggle ?? null })),
    q6: q6Copy(locale),
    approach: about.aboutApproach(locale), example: about.aboutExample(locale), author: about.aboutAuthor(locale), scope: about.aboutScope(locale),
    sections: about.aboutSections(locale), evidence: about.aboutEvidence(locale), title: about.aboutTitle(locale),
  };
}
process.stdout.write(JSON.stringify(out));
"""


def dump_ts_copy() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        entry = Path(tmp) / "entry.ts"
        entry.write_text(DUMP_ENTRY % {"src": SRC.as_posix()}, encoding="utf-8")
        bundle = Path(tmp) / "entry.mjs"
        subprocess.run(["npx", "esbuild", str(entry), "--bundle", "--format=esm", "--platform=node", f"--outfile={bundle}", "--log-level=warning"], cwd=ROOT, check=True)
        return json.loads(subprocess.run(["node", str(bundle)], cwd=ROOT, check=True, capture_output=True, text=True).stdout)


def esc(s: str) -> str:
    return str(s).replace("|", "｜").replace("\n", "<br>")


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(out)


def pair(zh, en, key):
    return (zh[key], en[key])


def main() -> int:
    ts = dump_ts_copy()
    zh, en = ts["zh-CN"], ts["en"]
    md = ["# flavorwords 前端文案总表（审核稿）", "", f"自动导出自 `product-vector-v1.json`（{B['version']}）、`view.ts` / `about.ts`（经 esbuild 执行）与组件内固定文案。每一行都是用户会在屏幕上看到的字。修改后请告诉我改哪一行，我改源头再重新导出。", ""]

    md += ["## 1. 首页与流程界面", "", "### 首页 Hero（view.ts appShell）", ""]
    rows = [("口号", *pair(zh["shell"], en["shell"], "slogan")), ("标题", *pair(zh["shell"], en["shell"], "title")), ("段落", *pair(zh["shell"], en["shell"], "subtitle")), ("行动主张", *pair(zh["shell"], en["shell"], "claim")), ("开始链接（与下方按钮同一动作）", *pair(zh["shell"], en["shell"], "startLink")), ("开始按钮", *pair(zh["shell"], en["shell"], "start")),
            ("About 按钮 aria", *pair(zh["shell"], en["shell"], "about")), ("语言切换", *pair(zh["shell"], en["shell"], "localeSwitch")), ("离线标记 title", *pair(zh["shell"], en["shell"], "offlineReady"))]
    md += [table(["位置", "中文", "English"], rows), ""]
    md += ["### 语境卡（view.ts contextCatalog）", ""]
    rows = []
    for cz, ce in zip(zh["context"], en["context"]):
        rows.append((f"{cz['key']} 标题", cz["title"], ce["title"]))
        if cz["hint"]:
            rows.append((f"{cz['key']} 提示", cz["hint"], ce["hint"]))
        if cz["toggle"]:
            rows.append((f"{cz['key']} 单品 / 拼配", " ｜ ".join(cz["toggle"].values()), " ｜ ".join(ce["toggle"].values())))
        rows.append((f"{cz['key']} 选项", " ｜ ".join(cz["chips"]), " ｜ ".join(ce["chips"])))
    md += [table(["位置", "中文", "English"], rows), ""]
    md += ["### 再确认 Q6（view.ts）", "", table(["位置", "中文", "English"], [("标题", zh["q6"]["title"], en["q6"]["title"]), ("提交按钮", zh["q6"]["submit"], en["q6"]["submit"])]), ""]
    md += ["### 组件内固定文案", ""]
    for section, rows in COMPONENT_STRINGS.items():
        md += [f"#### {section}", "", table(["位置", "中文", "English"], rows), ""]

    md += ["## 2. 卡片标题、说明标签与差异句（bundle.presentation）", ""]
    rows = [("第一次出卡标题", P["preview_heading"]["zh-CN"], P["preview_heading"]["en"]), ("终卡标题", P["card_heading"]["zh-CN"], P["card_heading"]["en"]), ("折叠层标题", P["science_heading"]["zh-CN"], P["science_heading"]["en"]), ("参考资料前缀", P["citation_prefix"]["zh-CN"], P["citation_prefix"]["en"])]
    for k, v in P["evidence_labels"].items():
        rows.append((f"说明标签 {k}", v["zh-CN"], v["en"]))
    for k in ("pos", "neg"):
        rows.append((f"差异句模板 {k}", P["delta_templates"]["zh-CN"][k], P["delta_templates"]["en"][k]))
    rows.append(("纸味 / 陈味组的提示", P["defect_note"]["zh-CN"], P["defect_note"]["en"]))
    rows.append(("勾选提示（describe）", f"选出最贴近你感受的 {B['question_flow']['first_description']['pick_count']} 个词。", f"Pick the {B['question_flow']['first_description']['pick_count']} words closest to what you tasted."))
    md += [table(["位置", "中文", "English"], rows), "", f"上屏的说明状态：{', '.join(P['displayable_evidence_states'])}；待补链接或待复核的文献句不上屏。", ""]

    md += ["## 3. 题库 Q0–Q5（bundle.question_bank）", ""]
    rows = []
    for slot, q in B["question_bank"].items():
        rows.append((slot, "提问", q["prompt"]["zh-CN"], q["prompt"]["en"]))
        for opt, spec in q["options"].items():
            rows.append((slot, f"选项 {opt}", spec["label"]["zh-CN"], spec["label"]["en"]))
    md += [table(["题", "位置", "中文", "English"], rows), ""]

    md += ["## 4. 十六组参考风味（终卡标题与标签）", "", "「参考实例」一列不上屏，只作内部对照；命名规则：两个主要感官参照，不加修饰词。", ""]
    rows = [(p["owner_name"]["zh-CN"], p["owner_name"]["en"], " ｜ ".join(p["display_tags"]["zh-CN"]), " ｜ ".join(p["display_tags"]["en"]), p["benchmark_beans"], p["member_count"]) for p in B["profiles"]]
    md += [table(["中文名", "English", "标签 zh", "tags en", "参考实例（未上屏）", "记录数"], rows), ""]

    md += ["## 5. 维度词（描述与勾选时按维度取的词）", ""]
    rows = [(d, P["dimension_labels"][d]["zh-CN"], P["dimension_labels"][d]["en"], " ｜ ".join(P["dimension_tags"][d]["zh-CN"]), " ｜ ".join(P["dimension_tags"][d]["en"]), " ｜ ".join(P["consumer_terms"].get(d, {}).get("zh-CN", [])), " ｜ ".join(P["consumer_terms"].get(d, {}).get("en", []))) for d in B["dimensions"]]
    md += [table(["维度", "标签 zh", "label en", "维度词 zh", "words en", "消费端补充 zh", "consumer en"], rows), ""]

    md += ["## 6. 94 个规范概念的极简词（用户录入豆子时上卡）", ""]
    rows = [(k.removeprefix("sensory."), v["zh-CN"], v["en"]) for k, v in sorted(P["concept_tags"].items())]
    md += [table(["概念", "中文", "English"], rows), ""]

    md += ["## 7. 关于这段描述（折叠层里的句子）", "", "标签为「（不上屏）」的行不出现在产品里：owner 自建的成因句是项目规则（在 About 的「初始参考如何形成」里解释），待复核的文献句撤下。", ""]
    rows = [("初始参考句模板", P["evidence_labels"]["REFERENCE_BASIS"]["zh-CN"], P["reference_basis_templates"]["zh-CN"]["text"] + " " + P["reference_basis_templates"]["zh-CN"]["explain"], P["reference_basis_templates"]["en"]["text"] + " " + P["reference_basis_templates"]["en"]["explain"], "engine")]
    rows += [(s["context_id"], P["evidence_labels"].get(s["evidence_state"], {}).get("zh-CN", "（不上屏：" + s["evidence_state"] + "）") if s["evidence_state"] in P["displayable_evidence_states"] else "（不上屏：" + s["evidence_state"] + "）", s["zh-CN"], s["en"], (s.get("source_title") or "").split(" — ")[0]) for s in P["context_statements"]]
    md += [table(["语境", "标签", "中文", "English", "出处"], rows), ""]

    md += ["## 8. About（about.ts，经执行导出）", ""]
    rows = [("页面小标题", zh["title"]["title"], en["title"]["title"]), ("Eyebrow", zh["approach"]["eyebrow"], en["approach"]["eyebrow"]), ("标题", zh["approach"]["title"], en["approach"]["title"])]
    for i, (a, b) in enumerate(zip(zh["approach"]["intro"], en["approach"]["intro"]), 1):
        rows.append((f"导言 {i}", a, b))
    rows += [("设计页 eyebrow", zh["author"]["eyebrow"], en["author"]["eyebrow"]), ("设计页标题", zh["author"]["title"], en["author"]["title"])]
    for i, (a, b) in enumerate(zip(zh["author"]["paragraphs"], en["author"]["paragraphs"]), 1):
        rows.append((f"设计页段 {i}", a, b))
    rows.append(("署名行", zh["author"]["credit"], en["author"]["credit"]))
    for a, b in zip(zh["author"]["contributions"], en["author"]["contributions"]):
        rows.append((f"贡献 {a['value']}", f"{a['value']} {a['unit']}{a['label']}：{a['use']}", f"{b['value']} {b['label']}: {b['use']}"))
    rows.append(("资料范围标题", zh["scope"]["title"], en["scope"]["title"]))
    for a, b in zip(zh["scope"]["items"], en["scope"]["items"]):
        rows.append((f"资料范围 {a['key']}", f"{a['value']:,} {a['unit']}{a['label']}：{a['note']}", f"{b['value']:,} {b['label']}: {b['note']}"))
    rows.append(("资料范围脚注", zh["scope"]["footnote"], en["scope"]["footnote"]))
    md += [table(["位置", "中文", "English"], rows), ""]
    for sz, se in zip(zh["sections"], en["sections"]):
        md += [f"### About · {sz['title']} / {se['title']}（默认折叠）", ""]
        rows = [("摘要", sz["summary"], se["summary"])]
        for bz, be in zip(sz["blocks"], se["blocks"]):
            rows.append((bz["title"] + " / " + be["title"], bz["body"], be["body"]))
        md += [table(["位置", "中文", "English"], rows), ""]
    md += ["### About · 资料来源列表（本项目如何使用这份资料）", ""]
    rows = [(a["title"], a["gives"], b["gives"], a["terms"], a["use"], a["claimsLive"]) for a, b in zip(zh["evidence"], en["evidence"])]
    md += [table(["来源", "中文", "English", "来源条款", "本项目的使用", "上线说明句"], rows), ""]

    OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"written {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

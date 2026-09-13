# 风味向量设计 V1 (Flavor Vector Design V1)

**Status:** ACTIVE — owner decisions R3-D5 (pivot), R3-D6 (dimension count, candidate-library path, structure axes) R3-D7 (confirmation: 0.6 : 1.0 structure weight, data sources, Steps 1–4) R3-D8 (profile names, α = 0.5, literature intake, bilingual presentation layer) R3-D9 (coherence decision tree, 8-pick-5 feedback, Q6 escalation gate, consumer lexicon) R3-D10 (thresholds 0.80 / 0.65, slot mapping approved, lexicon v1 locked) R3-D11 (94 concept tags approved, literature claim conventions, hybrid utterance mapper, paradox guard, three test suites) R3-D12 (Q0 wording localised, question bank approved, guard and context check confirmed, Step 5: GACTT lexicon expansion and the session API) R3-D13 (GACTT zh mapping, blends and optional origin, PWA topology, app interfaces before visual design) R3-D14 (Vue 3 + Tailwind isolated PWA, two-level claim declaration, three claims files ingested) R3-D15 (visual pass: tonality, 1 : 4 layout, card flow, consumer-facing copy layer, About data visual, mobile UX list) R3-D16 (owner's copy review: positioning, evidence labelling, claim re-verification, exit options, profile naming) R3-D17 (copy review 2 + mobile pass: UC Davis DOI withdrawn, project rules off the card, initial-reference line, confirmed-profile title, hero home page, 54 dp controls, four-page scroll-driven About) R3-D18 (copy review 3 + brand pass: the flavor card as the product object, home with two bright buttons, poster-style About visuals after the owner's references, origins by continent, serif proposals) R3-D19 (branding pass: slogan hero, brand glyphs instead of the card on home and About, Fraunces for the wordmark, the owner's About copy, reading time on the poster pages) R3-D20 (owner review 4: coloured headline, motif kit, four-option questions, drinker's-eye context titles, pinned About pages, MiSans subsets, PNG export) R3-D21 (owner review 5: concrete flavor words, nine brewing methods, reworded Q3/Q4/Q5, varying card notes, SVG wordmark, pins without stutter, Stack Sans) R3-D22 (varying notes with alternate phrasings and a data-count line, a reachable Q6 gate, English fit, Vercel + machine-readable layer) R3-D23 (Q6 trigger rate stated with a front-of-house test set, English About fit, Git LFS + Vercel form sheet for the push) and R3-D24 (tablet and desktop layout: one centred column, height-bound home tiles), 2026-09-13
(`db/data/backend-sequential-model-v2/revisions/round3/owner_decisions_round3.json`).
**Supersedes:** the adaptive-question / proposition-lattice / product-inference v0–v0.2 line. Those artefacts are archived, not deleted: `docs/archive/adaptive-question-policy-20260912/README.md`.
**Owner's words:** 「做向量然后进行相似度算法设计 … 做一个小而美的产品，后续产品中不再需要训练或者 transformer。停止无意义测试，数据的可用性比测试更重要。」

---

## 0. 这一轮决定了什么

| 保留                                                               | 替换                                                                                                             |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| 数据管线：acquire → clean → semantic → consolidation（83K 检查点） | 推理机制：有限状态机 + 命题格 + 问题轴策略 → **12 维向量 + 余弦相似度**                                          |
| 概念注册表（94 个规范概念）与 5,656 个聚类                         | 产品策略检查点 product-inference v0 / v0.2（120 用例、100 行审阅包）→ 归档                                       |
| 权利治理：按数据集逐一审批；分数不是概率；不训练                   | 「训练/不训练」的争论 → 设计上不需要训练；MLP 只是 V_pred 的可选实现，未计划                                     |
| 语境层 C0（冲煮）/ C1（烘焙）                                      | 语境扩展为 **C0–C2 三道题**：冲煮、烘焙、豆种 + 处理法                                                           |
| ——                                                                 | 产品定位：**科学感官诊断与风味探索工具**，不是咖啡导购。输出先给「目标风味画像」，再给标杆豆款与用户自建库的匹配 |

整个系统的底层可以精简为：**一个投影矩阵 + 一组向量 + 一行余弦公式**。全部运算是加权求和与余弦，在前端 JS 中完成，无服务器、无 GPU、无训练。

---

## 1. 向量空间

### 1.1 十二个维度（R3-D6，原 8 维方案扩展）

```
V = [ acidity, sweetness, body, floral, fruity, nutty_chocolate, fermented_winey, bitter_roasted,
      酸度      甜度       醇厚度  花香     果香    坚果/巧克力        发酵/酒香         苦感/烘烤
      spice, herbal_green, woody_earthy, defect ]
      香料    草本/青草       木质/泥土      瑕疵
```

前 8 维是 owner 的原始 SCA/WCR 空间；后 4 维是数据要求的：8 维草案里 94 个规范概念有 22 个无处安放、12 个勉强归属
（近 36% 的语义节点会被扭曲或丢失），12 维后 **94/94 全覆盖**。前端点积从 8 维到 12 维的开销是纳秒级。
`defect` 维天然是推荐里的**负向约束**：用户向量在该维恒为 0，候选的瑕疵质量会直接拉低余弦，无需额外惩罚项。

每个向量在比较前归一化为单位向量；余弦只比较分布形状，不比较强度。

### 1.2 投影矩阵（概念 → 维度）

`db/data/product-vector-v1/CONCEPT_DIMENSION_PROJECTION_DRAFT.tsv`：94 个规范概念各一行，12 列权重（0–1），
`coverage_state`（60 MAPPED + 34 MAPPED_12D），`coverage_state_8d`（保留 8 维时的诊断），`owner_reviewed=true`
（R3-D7 Step 1：owner 以草案整体批准登记，basis 注明 `OWNER_STEP1_APPROVAL`；权重由操作员按 SCA 风味轮家族起草，逐行修正随时可改，
改动只需编辑这一张表再重跑两个 build 脚本）。

### 1.3 聚类如何进入空间

5,656 个聚类中 83 + 8 + 3 个已经指向规范概念（EXISTING*CANONICAL*\*），直接继承投影行。
其余 4,396 个 GENUINE_ONTOLOGY_CANDIDATE 里，`assertion_support ≥ 20` 的只有 351 个 —— 这 351 个是「完成标准空间量化」
真正要人工映射的范围，其余是长尾，先不映射（它们对余弦几乎没有贡献）。

---

## 2. 前置语境 C0–C2 → V_pred

三道题，四个变量：

| 题  | 变量                      | 选项                                                              | 后台物理/化学逻辑（owner 表述，证据状态见 §6）                                                                                                                           |
| --- | ------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| C0  | 冲煮方式                  | 手冲(V60) / 意式浓缩 / 冷萃 / 法压                                | 萃取动力学与分子量截断：冷萃抑制低挥发酸；意式放大醇厚度与油脂                                                                                                           |
| C1  | 烘焙度                    | 浅 / 中 / 深（数据侧对应 CoffeeReview 的 Light … Very Dark 六档） | 绿原酸降解与美拉德产物占比：浅烘高酸/花果，深烘高醇厚/焦糖苦                                                                                                             |
| C2  | 豆种 + 处理法（一题两栏） | 瑰夏 / 波本 / 铁皮卡 / 罗布斯塔 … × 水洗 / 日晒 / 蜜处理 / 厌氧   | 品种定风味上限（基因型），处理法定前体物质积累：日晒→还原糖/游离氨基酸↑→果酱、热带水果、高甜；水洗→内源有机酸突出→干净、柑橘、花香、高酸；厌氧→乳酸与外源酯类→酸奶、酒香 |

`V_pred = normalize( K[C0] + K[C1] + K[C2_variety] + K[C2_process] )`，`Matrix_K` 每个选项一行 12 维。

**拼配与产地（R3-D13）**：C2 豆种卡有「单品 SOE / 拼配 Blend」切换，拼配最多勾 3 个豆种，
`V_blend_variety = normalize(Σ V_variety_i)`（等权均值），对应 Big Sur 那种「哥伦比亚瑰夏 + 埃塞原生种 + 印尼铁皮卡」的真实拼配结构。
产地不是必选项，是 C2 的可选大区 Chip：埃塞俄比亚/东非（floral + acidity）、哥伦比亚/中南美（fruity + sweetness）、
云南（fermented_winey + nutty_chocolate）、肯尼亚（acidity + fruity）；选了就在对应轴叠加 δ = 0.1 的偏置，跳过则完全靠豆种与处理法。
产地在向量层本质是「海拔 + 基因 + 处理法」的集合表达，所以只做轻微引导。

**Matrix_K 的来源分两层，状态不同：**

1. **可以现在从 83K 语料算出来的**：C0 × C1。CoffeeReview 每条评论带 Roast Level 与冲煮方式（cupping / espresso），
   按格子统计向量均值即得 K 行。格子密度（7,300 杯）：

   | 格子                   | 杯数  | 格子                    | 杯数 |
   | ---------------------- | ----- | ----------------------- | ---- |
   | CUPPING × Medium-Light | 3,110 | ESPRESSO × Medium-Light | 315  |
   | CUPPING × Light        | 1,215 | ESPRESSO × Medium       | 279  |
   | CUPPING × Medium       | 1,110 | ESPRESSO × Medium-Dark  | 131  |
   | CUPPING × Medium-Dark  | 448   | ESPRESSO × Dark         | 18   |
   | CUPPING × Very Dark    | 272   | ESPRESSO × Light        | 16   |
   | CUPPING × Dark         | 121   | ESPRESSO × Very Dark    | 13   |

   主干格子远超 owner 的 100+ 标准；意式 × 浅/极深两格只有十几杯，属于「插值」格子。冷萃、法压在语料里没有。

   **已算出（Step 2，`build-matrix-k-v1.py` → `MATRIX_K.tsv`, `MATRIX_K_C0_C1_CELLS.tsv`）**：C0 两行（cupping 作 V60 / 法压的
   滤泡代理，espresso 实测），C1 六行，12 个 C0×C1 联合格子（8 个 MAIN ≥100 杯，4 个 INTERPOLATION 10–99 杯）。冷萃无语料行，
   标 `NO_CORPUS_ROW_LITERATURE_CLAIM_PENDING`，等 UC Davis / Coffee Ad Astra 的萃取结论。

2. **C2（Step 3，`extract-coffeereview-c2-labels.py` → `COFFEEREVIEW_C2_LABELS.tsv`）**：用关键词词表在评论名称、产地与正文里
   抽取品种与处理法（只输出类别标签，不输出文本）。8,387 条评论：品种可解析 3,586（43%），处理法 4,304（51%），两者皆有 2,517。
   进入 Matrix_K 的行（单标签、成员 ≥ 50 / ≥ 30）：

   | 品种               | 杯  | 品种     | 杯  | 处理法    | 杯    |
   | ------------------ | --- | -------- | --- | --------- | ----- |
   | ethiopian_landrace | 565 | caturra  | 166 | washed    | 1,819 |
   | gesha              | 447 | bourbon  | 154 | natural   | 879   |
   | sl28_sl34          | 259 | catuai   | 90  | decaf     | 66    |
   | typica             | 88  | robusta  | 64  | anaerobic | 52    |
   | pacamara           | 55  | castillo | 51  |           |       |

   honey（145 条）因大多同时出现 washed/natural 字样被判多标签而未入行，需要词表细化。WCR Varieties Catalog（已批准）
   将补 K[C2_variety] 的 sensory potential 与标准品种词表；语料实测行与 WCR 行并列，各带 basis。

---

## 3. 感知题 Q5–Q10 → V_user

`V_user = normalize( Σ Q[question][answer] )`，增量按 owner 给定（只作用于前 8 维；spice / herbal_green / woody_earthy / defect
在 V_user 中为 0，等新的感知题再补）：

| 题         | 选项              | 增量                                |
| ---------- | ----------------- | ----------------------------------- |
| Q5 酸质    | A 鲜明柑橘/苹果酸 | acidity+2, fruity+1                 |
|            | B 柔和乳酸/发酵酸 | acidity+1, fermented_winey+2        |
|            | C 几乎无酸，平顺  | body+1                              |
| Q6 甜感    | A 花蜜/蔗糖       | floral+1, sweetness+2               |
|            | B 焦糖/黑巧       | nutty_chocolate+2, bitter_roasted+1 |
|            | C 熟果/果酱       | fruity+2, sweetness+2               |
| Q7 触感    | A 绿茶/果汁       | body+1                              |
|            | B 牛奶/丝绒       | body+2                              |
|            | C 黑巧/糖浆       | body+3, bitter_roasted+1            |
| Q8 香气    | A 花香草本        | floral+3                            |
|            | B 坚果烤面包      | nutty_chocolate+3                   |
|            | C 热带水果微醺    | fermented_winey+2, fruity+2         |
| Q9 苦感    | A 微苦回甘        | nutty_chocolate+1, bitter_roasted+1 |
|            | B 无苦            | （无增量）                          |
| Q10 复杂度 | A 层次分明干净    | floral+1, acidity+1                 |
|            | B 交融浓郁        | fermented_winey+1, body+1           |

3×3×3×3×2×2 = 324 种答案组合，即 324 个可能的 V_user；§7 的用户视野测试就是穷举这 324 个。

### 3.1 问答流：相干性决策树（R3-D9）

六道感知题不再固定顺序全问，而是按 owner 的决策树动态分支（`packages/flavor-data/src/product-vector-v1/flow.ts`，`flowStep()`）。
槽位 Q0–Q5 到 Matrix_Q 六题的映射（R3-D10 批准，`slot_mapping_owner_reviewed=true`）：
Q0 = 酸质、Q1 = 香气（基础对，两题在 12 维里贡献的特征最丰富、区分度最高）；Q2 = 甜感、Q3 = 触感（校验）；Q4 = 苦感、Q5 = 复杂度（确认/修正），
契合萃取与口感演进的顺序；Q6 = 8 词勾选强修正。

```
C0–C2 + Q0–Q1 → 问 Q2、Q3 → 相干度(Q0-Q1, Q2-Q3)
   ≥ 0.80 相干   → Path 1：问 Q4（轻微确认）→ 相干度(Q0-Q2, Q3-Q4) 严重? → Path 4（后置突变，Q6 候选）: 交付
   0.65–0.80 轻微 → Path 2：问 Q4（修正）→ 问 Q5（确认）→ Q5 与 (0-1+3-4) 或 (2+3-4) 相干 → 交付；否则 Q6 候选
   < 0.65 严重    → Path 3：问 Q4-Q5（修正）→ Q4-5 与 0-1 或 2-3 相干 → 交付；均不相干 → Q6 候选
```

第一次校验必须是 Q2–Q3 一起对基础对，而不是 Q2 单独：单题的画像签名比一对题噪声大得多，按 Q2 单独校验时 324 条答题序列有 44% 落入严重冲突；
按树图（Q2–Q3 一起）校验后回到 owner 设计的节奏。

**相干度不在原始答案子向量上算。** 每个答案只动 1–2 个维度，两个内容一致但涉及不同维度的答案余弦为 0
（实测 Q0-Q1 对 Q2-Q3 的 81 种组合里 76 种 < 0.65）。引擎先把每组答案映射成「画像签名」——对 16 个画像质心的余弦向量——再取两组签名的余弦：
问的是「这些答案指向同一批画像吗」。校准（81 种 Q0–Q3 组合）：最小 0.62、中位 0.73、p75 0.82、最大 0.98。
**阈值（R3-D10）：相干 ≥ 0.80，严重 < 0.65。** owner 的产品节奏判断：追求精准与参与感的用户不需要极速；约三成高度一致的用户走 Path 1，
六成在 Q4–Q5 经历一次微调（感知到系统在认真解构），一成触发强修正。324 条完整答题序列的实测（引擎按序只问被要求的题）：

| 路径                  | 序列数 | 占比  | 问题数 |
| --------------------- | ------ | ----- | ------ |
| Path 1 顺畅           | 80     | 24.7% | 5      |
| Path 2 轻微修正       | 200    | 61.7% | 6      |
| Path 3 严重冲突       | 28     | 8.6%  | 6      |
| Path 4 后置突变       | 16     | 4.9%  | 5      |
| Q6 候选（升阶门控前） | 26     | 8.0%  | —      |

平均 5.70 题。

**两个补充守卫（R3-D11，owner 的画像测试要求）**。画像签名空间把差异压得很扁（81 种组合最低也有 0.62），owner 定义的
「感官悖论」——选了极浅烘高酸花香，又选了重苦厚重——在签名空间只有 0.72（轻微），拦不住。于是加了：

1. **烘焙极性悖论守卫**：极性 = (+acidity, +floral, +herbal_green) − (bitter_roasted, woody_earthy, 0.7·nutty_chocolate)。两组答案的极性
   强烈反号（两侧 |极性| ≥ 0.55）即判严重，不看签名重叠。body 与 fruity 不进极性轴（Q3 每个选项都带 body，果香两边都有）。
2. **语境冲突检查**：V_pred 的极性与基础对反号（|极性| ≥ 0.25）时，第一次判定封顶为轻微 → Path 2。这是 owner 的 Persona B
   （选了深烘意式，却要鲜明水蜜桃果酸）：语境是软先验，只能触发修正，不能触发严重。曾试过把 V_pred 直接混进基础对向量：
   V_pred 是稠密的语料均值，签名被它主导，324 条序列 100% 成了 Path 1——这条路被否定，记录在此。

加守卫后的实测节奏（324 条序列）：无语境 21% / 52% / 27%（Path 1 / 2 / 3+4），浅烘手冲语境 20% / 53% / 27%，深烘意式语境
15% / 63% / 22%。守卫把约 13% 的序列从 Path 2 移进 Path 3——这是 owner 的取舍：Persona C 必须被拦截（「防范底线错误」），
节奏是软目标。测试区间相应放宽到 Path 3+4 ≤ 30%；关掉守卫（`polarity.min_magnitude` 设大）即回到 25 / 62 / 14。

owner 三个画像的实测（`tests/product-vector-v1-personas.test.ts`）：

| 画像                                                       | 语境 + 答案                             | 结果                                                                                        |
| ---------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------- |
| A 极致浅烘花果派「喜欢茉莉花香、柑橘酸，喝手冲，讨厌苦味」 | 浅烘手冲水洗；Q0=A Q1=A Q2=A Q3=A Q4=B  | 映射器给出 Q1=A、Q0=A、Q4=B（讨厌→否定）；Path 1，5 题，无 Q6                               |
| B 矛盾偏好者「选了深烘意式，但要强烈的水蜜桃鲜明果酸」     | 深烘意式；Q0=A Q1=C Q2=C Q3=B Q4=B Q5=A | 语境检查 0.79 轻微（悖论标记）→ Path 2，Q4 修正 Q5 确认，出卡，无 Q6                        |
| C 否定词口语「完全不酸、不要苦、要非常浓郁甜感」           | 中烘手冲；Q0=C Q1=C Q2=C Q3=B Q4=B Q5=B | 否定守卫强制 Q0=C、Q4=B；答案内部一致，无严重冲突，不触发 Q6（owner 原文是「若…无法收敛」） |
| C′ 感官悖论（浅烘高酸花香，然后焦糖黑巧 + 厚重 + 苦）      | 浅烘手冲；Q0=A Q1=A Q2=B Q3=C Q4=A Q5=B | 极性守卫 → 严重（0.64!）→ Path 3；升阶门控在勾选偏向感知时开 Q6                             |

示例：清亮花果（酸-A + 香-A）对花蜜甜（甜-A）0.77，对焦糖黑巧（甜-B）0.63；顺滑坚果（酸-C + 香-B）对焦糖黑巧 0.96，对花蜜甜 0.59。

### 3.2 题库文案（R3-D11）

`QUESTION_BANK.tsv` / bundle `question_bank`：Q0–Q5 的口语化中文提问与选项（**R3-D12 批准，`owner_reviewed=true`**），英文对照，
以及每个选项的提示词（cue words）。owner 修补了 Q0 的酸质文案——「亮亮的柑橘」是 bright 的直译腔，「很酸/尖锐」会让小白反感：
Q0「入口第一感觉，酸是哪一种？」A 鲜明多汁的柑橘 / 青苹果酸 · B 柔和温和的乳酸 / 发酵果酸（像酸奶、水果黄酒）· C 平顺无酸 / 低酸度（口感顺滑平衡）。

### 3.3 混合映射器（R3-D11，`lexicon.ts`）

消费者口语 → Q0–Q5 选项，双轨制：

```
[口语] → 否定词前缀扫描（不/没/无/毫无/几乎不/怕/不要/讨厌/不喜欢 …）
       → 方向敏感题 Q0 Q1 Q2 Q5：口语向量在该题维度子空间的投影，对每个选项向量取余弦
       → 平行/量级题 Q3 Q4：选项提示词命中
       → 综合得分 = α·余弦 + β·命中（α 1.0，β 0.5）；否定强制（不苦→Q4-B，不酸/怕酸→Q0-C）优先于一切
```

口语向量来自表达层同一套词汇（消费端词、概念极简词、维度词列表），否定的词只记录不加分。
28 条中文 + 5 条英文口语用例（`tests/product-vector-v1-lexicon.test.ts`）全部命中预期选项。

### 3.4 会话接口（R3-D12，`session.ts`）

前端只需要这一组纯函数，状态不可变，不碰存储：

```
createSession(context, locale, beans?)  → nextStep(session)   "ask"（题卡：提问 + 选项 + 进度）| "describe" | "picks" | "q6" | "final"
answer(session, slot, option)           → 按决策树推进；answerFromUtterance(session, 口语) 用映射器只填当前被问的槽位
firstDescription(session)               → 推理 + 3+5 描述，进入 picks 阶段
submitPicks(session, words)             → 升阶门控：分支 A 出总结卡（final）；分支 B 给 Q6 的 8 个选项（q6）
answerQ6(session, dimensions)           → α_strong 强修正，第二份描述 + 总结卡（final）
```

每一步写入 `history`（事件 + 摘要），是用户研究要的隐式反馈记录。用户本地库（IndexedDB）是另一个模块，通过 `beans` 传入。

### 3.5 应用接口层（R3-D13，先接口后视觉）

owner 的指令是先把接口写完并跑通，视觉稍后对齐。交付的都是纯 TS、无样式、无框架绑定：

| 模块       | 内容                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `view.ts`  | `contextCatalog(locale)`：C0–C2 五张卡（冲煮、烘焙、豆种含 SOE/拼配切换与上限 3、处理法、可选产地含提示语）；`normalizeContext`；`screenModel(session)`：每次用户操作后唯一需要调用的函数，返回 question / describe_ready / first_description / escalation / result 五种屏幕模型（对应 QuizCard、FirstDescriptionCard、EscalationModal、ResultCard）；`appShell(locale)`：首页文案（标题、导言、开始、About、语言切换、离线标记） |
| `user-db/` | Dexie 表 `user_beans`（id, name, roast_level, process, variety, concept_ids, created_at）；`addBean / listBeans / deleteBean / clearBeans`；`conceptIdsFromLabel(包装风味词)`；`beansAsVectors()` → `projectConcepts` → `BeanVector[]` 注入 `createSession(..., beans)` 离线匹配                                                                                                                                                  |
| `about.ts` | About 三板块（核心方法论、学术文献与理论支持、极简风味词典与数据血缘 + 隐私声明）双语内容，数字从 bundle 读取；四条引用各带证据状态（文献未入库时为 PENDING_INGEST）                                                                                                                                                                                                                                                              |

**栈的说明**：owner 的组件命名是 Vue 3 + Tailwind；仓库现有前端是 React 19 + React Router 8 + Vite，无 Vue、无 Tailwind。
接口层是框架无关的，两边都能一一绑定；选哪个栈在视觉对齐时定，这里不预设。

PWA 拓扑（owner）：单一全屏主界面 + About 覆盖层，无底部 Tab；顶栏左 ⓘ About、右 EN/中；Hero 一句导言 + 巨型「开始风味诊断」+ 离线可用标记。
流水线：打开 → 开始 → C0–C2 → Q0–Q5 一页一卡 → 第一次出卡 3+5 → 8 选 5 → 门控 → 总结卡（可保存/分享）或 Q6 → 精修卡。

### 3.6 交互闭环（R3-D9）

```
[阶段 1] C0–C2 + Q0–Q1，按 3.1 分支动态追问
[阶段 2] 第一份风味描述：3 + 5 = 8 个词（`describe()`，按 V_target 的维度轮询取词，每个词可归因到一个维度）
         末尾："请勾选出你觉得最符合你当前体验的 5 个风味描述" —— 隐式强信号（`picksToVector()`）
[阶段 3] 升阶门控（`escalationGate()`）：
         A  无严重冲突，或勾选未验证偏置 → 专属风味总结卡（用户自选的 5 个词 + 1–2 句科学归因 + "感谢使用，祝你享受这杯咖啡！"）
         B  流程里出现过严重冲突 且 勾选向量与 V_user 相干(≥ 0.85) 而与 V_pred 冲突(< 0.65) → Q6
             Q6 = 8 词勾选（|ΔV| 最大的 8 个非瑕疵维度各一个词，`q6Options()`），选中维度以 α_strong = 0.9 强修正（`applyQ6()`）
             → 第二份 3 + 5 描述卡（完结）
```

Q6 只在门控落入 B 时渲染。

---

## 4. 比较与校准

```
Sim(V_user, V_pred) = V_user · V_pred / (‖V_user‖ ‖V_pred‖)
ΔV       = V_user − V_pred                       # 感知偏置向量
V_target = normalize( V_pred + α · ΔV )          # α ∈ [0, 1]，默认 0.5，由 owner 定
画像      = 按 Sim(V_target, C_profile) 降序，取 top-1（+ 次选）
豆款      = 按 Sim(V_target, V_bean) 降序，在标杆库与用户库中各取 top-3
```

- ΔV 某维 > 0：用户对该萃取条件下这一维的感知高于理论值（或该冲煮实际过萃/欠萃）。
- 分数语义不变：余弦是**相似度，不是概率，未校准**（沿用 V0 合同里唯一保留的一条）。
- α 是产品里唯一的自由参数；先固定，不拟合。

---

## 5. 向量库与候选库

### 5.1 咖啡向量库（研究用）

`db/scripts/build-product-vector-v1.py` 从 83K 语料生成 `COFFEE_VECTOR_LIBRARY.tsv`（每杯咖啡 = 一个 effective record，
12 维单位向量，支持度，轴基础，权利标签）。轴的构成：描述词投影按该杯最强描述轴归一到 1；
**CoffeeReview 的 7,243 杯用其 Body / Acidity（1–10 编辑打分）的秩百分位替换 body / acidity 轴**（R3-D6 第三项，
`extract-coffeereview-structure-scores.py`；用秩而非 (score−1)/9，因为 Body 在 84% 的评论里是 8 或 9，只有秩带信息），
**结构轴 : 描述轴 = 0.6 : 1.0**（R3-D7）。结构打分只能加强一个风味向量，不能替代它：没有任何已映射描述词的杯不算可用
（否则它们的向量只剩结构方向，会自成两个假画像——首版 k-means 里的画像 8 和 10 就是这样来的）。

| 指标           | 8 维 + 仅描述词 | 12 维 + 打分 1:1 | **12 维 + 打分 0.6，需 ≥1 描述词** |
| -------------- | --------------- | ---------------- | ---------------------------------- |
| 咖啡总数       | 9,128           | 9,128            | 9,128                              |
| 可用向量       | 6,871           | 8,899            | **8,142**                          |
| 单薄 / 空      | 1,311 / 946     | 66 / 163         | 66 / 920                           |
| 杯均映射概念数 | 4.54            | 3.69             | 4.03                               |

### 5.2 候选库的权利出路（R3-D6 第二项）

CoffeeReview 的批准（R3-D2）是「内部研究」：它的向量用于标定 Matrix_K、构造画像、验证算法、模拟用户；
**不作为公开产品里被推荐的商品条目**。CoE 记录是公开发现、无许可声明，同样不直接推荐。owner 决定的复合模式：

1. **风味画像优先**：匹配结果第一优先输出「目标风味画像（Target Profile Vector）」——例如「高纬度水洗、强烈柑橘与清脆苹果酸质的中浅烘画像」。
2. **标杆豆款**：画像下方给出匹配该画像的代表性经典风味模板（瑰夏 / 肯尼亚 AA 等），由 owner 命名与挑选，不引用 CoffeeReview 具名商品。
3. **用户/社区自建库**：用户录入或扫码自己手头的豆子，本地离线匹配。

### 5.3 画像库（数据驱动的第一版，等 owner 命名）

`FLAVOR_PROFILE_LIBRARY.tsv`：对 8,142 个可用向量做确定性 k-means（k = 16，最远点初始化），每个画像有质心、成员数、
前三维、来源族构成、瑕疵均值，以及 owner 的命名与标杆豆款。

**命名怎么挂上去（R3-D8）**：owner 的 16 个命名写在 `PROFILE_NAME_ANCHORS.tsv`，每个名字带一个"锚点向量"（owner 陈述的质心特征）、
中英名、标杆豆款、3–4 个极简标签。构建时每个锚点按余弦挂到最相似的质心（一对一贪心，阈值 0.6），所以重建后名字不会错位。
本次结果：15 个 owner 锚点挂上（相似度 0.83–0.99）；`anchor-08 高拔明亮清冽酸质` 没有归宿（那个质心在 0.6 权重后消散，最佳 0.79，
保留在锚点表里等空间变化）；983 杯的「sweetness .72, fruity .54」画像 owner 未命名，操作员提案 `anchor-17 蜂蜜甜果与杏桃 / Honeyed Sweet Fruit`，
`owner_reviewed=false`，等确认或改名。

| 成员  | 质心前三维                                                | owner 命名 (zh / en)                                           | 标杆豆款                           | 极简标签 (zh-CN)               |
| ----- | --------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------- | ------------------------------ |
| 1,343 | fruity .79, acidity .42, sweetness .40                    | 熟果与黄桃甜感 / Tropical Stone Fruit                          | 哥伦比亚 厌氧日晒 / 埃塞 日晒 G1   | 黄桃｜熟果｜蔗糖｜柑橘         |
| 1,169 | nutty_chocolate .61, fruity .57, acidity .39              | 榛果巧克力与红莓 / Nutty Cocoa & Berry                         | 危地马拉 安提瓜水洗                | 榛果｜可可｜红莓｜柑橘         |
| 983   | sweetness .72, fruity .54, acidity .32                    | **蜂蜜甜果与杏桃 / Honeyed Sweet Fruit（操作员提案，待确认）** | 埃塞 西达摩 水洗 / 哥伦比亚 蜜处理 | 蜂蜜｜杏桃｜甜橙｜柔和         |
| 757   | nutty_chocolate .88, body .28, bitter_roasted .25         | 经典黑巧与烤榛果 / Dark Chocolate & Roasted Nut                | 哥伦比亚 惠兰水洗                  | 黑巧克力｜烤榛果｜红糖｜醇厚   |
| 720   | nutty_chocolate .61, woody_earthy .54, bitter_roasted .38 | 深烘烤雪松与松露 / Roasted Cedar & Earth                       | 苏门答腊 湿剥曼特宁                | 雪松｜松露｜黑巧克力｜烟熏     |
| 639   | fruity .71, acidity .64, body .25                         | 鲜明柑橘与柚子酸质 / Bright Citrus & Yuzu Acid                 | 肯尼亚 AA                          | 柚子｜柑橘｜黑加仑｜明亮       |
| 606   | sweetness .90, nutty_chocolate .24, body .23              | 蔗糖与纯净高甜 / Pure Cane Sweetness                           | 巴西 黄波本                        | 蔗糖｜蜂蜜｜焦糖｜柔和         |
| 592   | fruity .60, woody_earthy .55, acidity .40                 | 野生黑加仑与树莓 / Wild Forest Berry                           | 埃塞 哈拉尔                        | 黑加仑｜树莓｜木质｜红酒       |
| 387   | floral .72, acidity .37, fruity .33                       | 高锐茉莉花与白花 / Delicate Jasmine & Floral                   | 耶加雪菲水洗 / 瑰夏                | 茉莉花｜白花｜佛手柑｜水蜜桃   |
| 325   | woody_earthy .86, bitter_roasted .36, sweetness .22       | 泥炭烟熏与风干木 / Smoky Peat & Aged Wood                      | 爪哇 老深烘                        | 烟熏｜泥炭｜风干木｜烟草       |
| 273   | spice .75, acidity .31, fruity .29                        | 异域小豆蔻与肉桂 / Cardamom & Sweet Spice                      | 也门 摩卡                          | 小豆蔻｜肉桂｜红糖｜葡萄干     |
| 217   | bitter_roasted .87, nutty_chocolate .26, body .22         | 深烘重可可与回甘 / Deep Dark Cocoa Roast                       | 意式拼配 深烘                      | 重可可｜焦糖｜烘烤｜回甘       |
| 60    | fermented_winey .65, acidity .52, nutty_chocolate .48     | 厌氧朗姆与微醺酒香 / Anaerobic Rum & Winey                     | 洪都拉斯 雪莉桶 / 厌氧日晒瑰夏     | 厌氧朗姆｜酒香｜热带水果｜发酵 |
| 47    | herbal_green .77, acidity .36, fruity .34                 | 清脆草本与绿茶香 / Fresh Herbal & Green Tea                    | 巴拿马 浅烘铁皮卡                  | 茉莉绿茶｜柠檬草｜青苹果｜清脆 |
| 12    | defect .99                                                | 瑕疵预警风味 / Off-Flavor / Defect Group                       | （负向约束集合，不推荐）           | 瑕疵｜霉味｜纸味｜陈味         |
| 12    | body .91, acidity .36                                     | 丝绒醇厚与糖浆感 / Full Velvet Body                            | 巴西 半日晒                        | 丝绒｜糖浆｜奶油｜醇厚         |

0.6 权重与「≥1 描述词」规则之后，结构打分主导的假画像消失（首版的 550 + 334 杯降到 12 杯）。

---

## 6. 表达层：一个向量后端，两种语言（R3-D8）

后端只收敛向量；风味词是前端表达层。zh-CN 渲染中国精品咖啡圈的「极简风味词阵列」（词 A｜词 B｜词 C｜词 D），en 渲染科学化的叙述；
长解释收进「相关风味说明」折叠层（R3-D16 前叫「科学归因」）。数据与规则都在 bundle 的 `presentation` 里，引擎函数 `displayTags()` / `statementsFor()` / `present()`。

**6.1 标签选择（owner 规则）**

| 优先级      | 条件                                          | 做法                                                                                         |
| ----------- | --------------------------------------------- | -------------------------------------------------------------------------------------------- |
| 1 实体级    | 候选带规范概念 id（用户录入的豆子、标杆豆款） | 按概念投影向量与该向量的点积降序，取前 3–4 个具体名词（茉莉花｜水蜜桃｜佛手柑｜青柠）        |
| 2 维度级    | 只有向量（画像质心、用户未细化）              | 权重 > 0.15 的主导维度，映射到维度级中国词库，每维取列表里第一个未用过的词；不暴露抽象维度名 |
| defect 守卫 | 任何情况                                      | defect 词只在 defect ≥ 0.5（瑕疵预警卡）时出现；常规卡强制过滤                               |

**6.2 词库** `CONCEPT_FLAVOR_TAGS.tsv`（规范基底，94 行 R3-D11 批准）+ `CN_CONSUMER_FLAVOR_LEXICON.tsv`（消费端泛化）。
消费端词表现状（R3-D12，Step 5 第一轮）：owner 的 29 条种子 + 5 条 fermented_winey 补强（水果黄酒、微醺朗姆、微醺、威士忌桶、雪莉桶）

- **GACTT 消费者语料抽取的 61 条英文高频词**（`extract-gactt-consumer-terms.py`，4,042 位受访者 9,997 条盲测笔记，只输出聚合频次
  `GACTT_CONSUMER_TERM_FREQUENCY.tsv`，不输出任何原文）。61 条里 32 条可上卡（chocolate、citrus、berry、juicy、funky、wine、smokey、stone fruit、tropical…），
  29 条是结构/泛称词（body、thin、watery、acidic、bitterness…）只给映射器听、不上卡（`display_eligible=false`）。
  fermented_winey 在消费者口中的词频：fermented 221、funky 109、wine 78、vinegar 36、funk 32、cider 19。
  **owner 的中文本土化裁决（R3-D13）**：funky → 野果发酵（备选 厌氧风味 / 特异发酵感）、funk → 厌氧风味、fermented → 水果发酵酱（备选 厌氧发酵）、
  wine → 微醺酒香、winey → 朗姆酒香、cider → 苹果酒感（fermented_winey + acidity）；vinegar 不上卡，只做映射器的负向过滤词（defect + acidity）。
  规则：不直译成「菌香」或「臭味/怪味」，统一收敛为野果发酵、厌氧风味、微醺酒香。映射器里同名的词表词覆盖概念标签
  （"vinegar" 不再走 acetic_vinegar 的 fermented .7 投影）。中文社媒语料仍等 owner 提供。
  维度级取词顺序：owner 的 `DIMENSION_TAG_MAP_CN` 列表在前，消费端词在后。`CONCEPT_FLAVOR_TAGS.tsv`：12 个维度各一组中国本土词（owner 的 `DIMENSION_TAG_MAP_CN`：acidity → 清冽果酸｜明亮酸质｜柑橘酸；
  fruity → 水蜜桃｜黄桃｜黑加仑｜杏桃；fermented_winey → 厌氧酒香｜朗姆酒｜发酵果酱 …）+ 94 个规范概念各一个中/英极简词
  （按 owner 规则：stone fruit → 黄桃/杏桃，brown sugar → 红糖/蔗糖，winey → 厌氧酒香/朗姆，citrus → 柑橘/柚子，floral → 茉莉花/咖啡花）。
  概念行仍是操作员草案（`owner_reviewed=false`）。

**6.3 科学归因句与文献声明（R3-D14 两层显式标注）**

owner 的合规规则：文献引用必须在两个层面显式声明。(1) 界面层：总结卡与「科学解释」折叠层里每一句归因都带 `evidence_state` 与出处
（「证据级别：LITERATURE_CLAIM · 来源：UC Davis Coffee Center」），About 的文献板块列出三项研究的名称、DOI/链接与许可说明；
(2) 学术与合规层：原始 PDF/全文绝不进 Git，`source_locator` 指向文献，外部文献标 `LITERATURE_CLAIM`，与 owner 自建的 `OWNER_STATEMENT` 严格区分。

三份 claims 文件已按 owner 给的核心内容入库（`db/data/external-literature/*.claims.csv`，11 条）：WCR 4 条绑定 C2_variety（瑰夏）与 C1_roast，
UC Davis 4 条绑定 C0_brew（手冲、意式、冷萃、法压），Coffee Ad Astra 3 条绑定 C0_brew 与 C0×C1 组合句。**DOI/链接与许可说明尚未由 owner 补充**，
所以这 11 条的状态是 `LITERATURE_CLAIM_PENDING_LOCATOR`：界面照常显示出处，About 里注明「DOI / 链接待补充」；两项补齐后重跑 ingest 即升为 `LITERATURE_CLAIM`。
来源登记表 `LITERATURE_SOURCES.json` 随 ingest 生成，bundle 的 `presentation.sources` 供 About 读取。
总结卡的归因句：最具体的语境句 + 第一条适用的文献句（若有）+ 计算得到的偏置句，每句带证据级别与来源。

`CONTEXT_STATEMENTS.tsv`（owner 的统一 schema）：`context_id`（语境组合键，如 `C0_V60__C1_LIGHT`）、`context_parts`、
`statement_zh`、`statement_en`、`evidence_state`（`OWNER_STATEMENT` / `CORPUS_MEASURED` / `LITERATURE_CLAIM`）、`citation_ref`。
现有 27 条：21 条单选项句 + 6 条组合句（如浅烘 × V60、中深烘 × 厌氧）。文献接入后 `LITERATURE_CLAIMS.tsv` 以同一 schema 合并进来
（`CONTEXT_STATEMENTS_MERGED.tsv` 是合并后的可读表）。引擎只取「所有组成部分都被回答」的句子，最具体的在前。

**6.4 卡片形态**

```
[ 高锐茉莉花与白花 ]                         ← owner 命名（zh-CN）/ Delicate Jasmine & Floral（en）
茉莉花 ｜ 白花 ｜ 佛手柑 ｜ 水蜜桃            ← 3–4 个极简标签
▸ 科学归因                                   ← 折叠层：语境句（带证据级别）+ ΔV 最大两维的偏置句
  浅烘焙保留了绿原酸与高挥发性花果香，V60 快萃优先释放了前段极性酸质。  [OWNER_STATEMENT]
  你感受到的酸质比这个语境的理论值更明显。  [COMPUTED_DELTA]
```

---

## 7. 数据充分性：owner 的四项测试，当前读数

`db/data/product-vector-v1/PRODUCT_VECTOR_V1_MEASUREMENT.json`

**7.1 饱和曲线（Saturation）**

| 检查点 | 断言           | 聚类         | 聚类增长 / 数据增长 |
| ------ | -------------- | ------------ | ------------------- |
| 50K    | 50,034         | 3,215        | —                   |
| 77K    | 77,038 (+54%)  | 5,050 (+57%) | ≈ 1.0               |
| 83K    | 83,031 (+7.8%) | 5,656 (+12%) | ≈ 1.5               |

未饱和。但新聚类几乎全是长尾：`assertion_support ≥ 5` 的聚类只有 845 个，≥ 20 的 351 个。对余弦推荐而言，
空间的「主干」早已稳定；增长发生在对推荐没有影响的尾部。结论与 owner 一致：**停止无差别爬取，转向定向补缺。**

**7.2 交叉组合稀疏度（Sparsity）**：C0 × C1 见 §2 表；C2 未测（无字段）。

**7.3 分布均匀度（Uniformity）**，8,142 杯可用向量的「最强维度」占比：

| 维度               | fruity | nutty_chocolate | sweetness | acidity | woody_earthy | floral | bitter_roasted | spice | herbal_green | fermented_winey | body | defect |
| ------------------ | ------ | --------------- | --------- | ------- | ------------ | ------ | -------------- | ----- | ------------ | --------------- | ---- | ------ |
| 12 维 + 打分 0.6   | 31.7%  | 22.7%           | 20.3%     | 9.7%    | 5.1%         | 4.7%   | 3.3%           | 1.8%  | 0.3%         | 0.2%            | 0.1% | 0.1%   |
| （8 维、仅描述词） | 35.6%  | 23.4%           | 21.1%     | 10.3%   | —            | 5.3%   | 3.8%           | —     | —            | 0.1%            | 0.4% | —      |

「最强维度」几乎不会是 body：0.6 的权重使结构轴成为第二、第三维而非主导维，这正是 owner 要的效果（在 1:1 时 body 曾以
假画像的形式占 3.9%）。**fermented_winey 仍是空轴**（0.2%）——
专业评审很少把发酵感写成独立描述词，而 Q5-B / Q8-C 会把用户推向这一维。这是剩下的最后一个长尾区，
定向补缺的第一目标（厌氧/特殊处理豆的评论；GACTT 消费者描述里 "boozy / winey / funky" 的用法）。

**7.4 用户视野测试（Query Horizon）**，324 个模拟 V_user：

| 指标                          | 8 维、仅描述词  | 12 维 + 打分 1:1 | **12 维 + 打分 0.6，≥1 描述词** | owner 标准 |
| ----------------------------- | --------------- | ---------------- | ------------------------------- | ---------- |
| top-1 相似度均值 / 最小       | 0.927 / 0.786   | 0.949 / 0.838    | **0.934 / 0.779**               | —          |
| top-3 全部 > 0.85 的用户      | 266 / 324 (82%) | 309 / 324 (95%)  | **281 / 324 (87%)**             | 100%       |
| top-3 三杯互不重复的用户      | 324 / 324       | 324 / 324        | 324 / 324                       | 100%       |
| 出现在任何 top-3 里的不同咖啡 | 200             | 323              | **270**                         | 越多越好   |
| 单杯被推荐最多次数            | 35              | 33               | 31                              | —          |

0.6 权重是 owner 有意的取舍：1:1 时的 95% 有一部分是靠结构打分把 Q7-C（重醇厚）用户推给描述词稀少的杯换来的。
现在剩下的 43 个用户分两类：Q7-C 高 body 组合（结构轴不再主导）和 Q5-B + Q8-C 高发酵组合（7.3 的空轴）。前者靠
标杆豆款与用户自建库补（它们不受描述词稀疏影响），后者靠 fermented_winey 定向补缺。

---

**7.5 三套本地测试（R3-D11）**：语义歧义（口语 → 选项，含否定）、用户画像全路径（A/B/C/C′ + 10 个画像）、
词库自然度（3+5 描述的每个词都可归因到维度、双语同维度、无维度名泄漏）——都是 vitest，跑在 bundle 上，不碰 CI。

## 8. 运行时形态与应用壳（R3-D14：Vue 3 + Tailwind v3，物理隔离）

owner 的栈裁决：Vue 3（Composition API + TS）+ Tailwind CSS v3 + lucide 图标，与旧 React 组件物理隔离。实现：

- `apps/pwa/`：独立入口（自己的 `index.html`、`vite.config.ts`、`tsconfig.json`、Tailwind/PostCSS 配置），`@vitejs/plugin-vue` + `vite-plugin-pwa`
  （generateSW，manifest，离线预缓存）；根 `package.json` 增加 `pwa:dev / pwa:build / pwa:typecheck`。旧 React 应用留在 `app/`，不参与这条构建。
- `src/store.ts` 是算法与 UI 的唯一桥：单例 `session`，`screen = shallowRef(screenModel(session))`，每次用户操作调一个 session 函数再刷新；组件里没有任何风味计算。
- 组件（结构与绑定完成，无视觉）：`AppHeader`（About、EN/中、离线指示）、`ContextSetupCard`（C0–C2，SOE/拼配切换上限 3，产地可选 Chip）、
  `QuizCard`（一页一题 + 进度）、`FirstDescriptionCard`（3+5 阵列 + 8 选 5）、`EscalationModal`（Q6，仅门控打开时）、
  `FinalAttributionCard`（用户 5 词 + 每句归因的证据级别与来源 + 分享/再来一杯）、`AboutDrawer`（三板块 + 四条引用的链接/许可/状态）。
- `vue-tsc` 通过，`vite build` 通过并生成 `sw.js`。

**视觉与体验（R3-D15，owner 的参考图与逐条修正）**

- 调性：白纸 + 复古色块（书封配色：芥末、天蓝、薄荷、粉、棕、紫、鲑、石板、玫瑰、酒红，加深绿 / 陶土），几乎不可见的纸纹；中文 MiSans、英文 Stack Sans（自托管，文件与许可放 `public/fonts`，未到位前回退系统字体）。
- 布局：整页 1 : 4 平铺切分——上方白色带（两行 logo「flavor / words」、信息 icon、EN/中、离线点、已答卡片的堆叠），下方色带随当前卡片换色，无外框无圆角"卡片在背景上"。
- 卡片流：一次一张；题目占上半、选项等分撑满下半；点选高亮后卡片上折收进上方堆叠（CSS 过渡），下一张升入；下一步为通栏大按钮；语境卡 5 张（含 SOE / 拼配切换、7 档烘焙含极浅、可选产地）。
- 面向用户的表达层：卡片与折叠层不露任何工程枚举；证据级别映射为「烘焙与萃取成因 / 物理萃取规律 / 感官偏置校准」，文献句带「引用自：…」；偏置句改为感官报告语气（"在当前的感知中，花香的表达比理论物理值更显突出，可能受萃取温度或降温速率的影响"）；无"您"，无致谢，无营销语。第一次出卡标题「风味描述预览」，终卡「风味描述」；「科学归因」默认折叠（CSS Grid 0fr→1fr，不测 DOM 高度）。
- 终卡：小标题 → ［画像名］ → 3 词（最大）│ → 其余词 · → 所选词维度色条 → 科学归因折叠 → 底部三个 icon（首页、重新体验、分享）。
- About：手机全屏抽屉；顶部数据可视化「风味光谱」由 bundle 数据生成——16 个画像各一道光谱，长度按咖啡数对数刻度，色段是画像质心在 12 维上的重心；其后是计数条；两个折叠段：「方法」（动态设计、公式设计、语义搜索不是排序、相干与极性）与「数据与文献」（四条出处 + 许可）；页脚一句本地自治。owner 的原话文案已替换掉 AI 腔与"词典与自治"段。
- 体验细节：纯 CSS 触感反馈（:active 缩放）、骨架光晕（收集阶段）、`overscroll-behavior-y: none`、安全区 padding、`-webkit-tap-highlight-color` 透明。Lottie 未加（无素材）。分享 PNG 导出留到最后设计，当前为系统分享 / 剪贴板文本。

- 一个 JSON：投影矩阵、Matrix_K、Matrix_Q、画像库（16 个质心 + owner 命名）、标杆豆款向量、α。
- 一段前端代码：加权求和 + 余弦 + top-k + 表达层（`displayTags` / `present`，locale = zh-CN | en）；用户自建库存本地（IndexedDB），匹配离线完成。
- 落点 `packages/flavor-data/src/`（现有 `research/session.ts` 消费的 v0.2 目录将被替换为 `product-vector-v1`）。
- 无服务器、无训练、无模型文件。MLP 仅当 Matrix_K 的线性求和被证明不够时才考虑，且输入输出都在这 12 维内；当前不计划。

**文案审核（R3-D16，owner 逐条审核 `docs/product/FRONTEND_COPY_REVIEW.md` 后的裁决）**

- 定位句：「flavorwords 帮助咖啡爱好者辨认和描述杯中的风味。通过几次选择，把酸质、香气与口感整理成一张由你确认的风味卡，并提供相关资料，帮助你进一步理解这杯咖啡。」首页：说清这一杯的风味 / 从酸质、香气与口感开始，找到贴近你感受的描述 / 开始描述。「诊断」「归因」「精修」「校准」「偏置」「悖论」「拦截」不再出现在用户文案里。
- 说明标签按内容性质区分，读者能看出是哪一种：`OWNER_STATEMENT` → 参考说明，`CORPUS_MEASURED` → 资料统计，`LITERATURE_CLAIM` → 研究参考，`COMPUTED_DELTA` → 描述差异；`LITERATURE_CLAIM_PENDING_LOCATOR` 与新增的 `LITERATURE_CLAIM_NEEDS_REVERIFICATION` 没有标签，`displayable_evidence_states` 之外的句子不上屏（`statementsFor` 过滤）。折叠层叫「相关风味说明」，前缀「参考资料：」。
- ΔV 只是描述与参考向量之差，不叫「偏置」，也不把差异归因到水温或降温速率：模板改为「这次的描述中，{维度}更突出。仅凭目前的信息，还无法判断这种差异的原因。」
- 三条文献句复核后下线（`review_state = NEEDS_REVERIFICATION`，claims CSV 新增两列）：WCR 词汇表不能支撑「瑰夏基因型单萜烯表达上限」；UC Davis 的分段研究报告前段更酸也更苦、后段更甜更花香，「先酸后苦」不是安全的概括（V60 与 espresso 两条）。冷萃句去掉「前段」。Coffee Ad Astra 作者统一为 Jonathan Gagné。owner 自建句改为「常见表现」语气：瑰夏句去「基因上限」，厌氧句去「极高识别度」，日晒句去「波本感」，中深烘 + 厌氧句改为「水温偏低是可能的原因之一，但仅凭描述无法确定」。11 条文献句 → 8 条上线、3 条待复核；About 逐来源列出「n 条待复核，未上线」。
- 题库：Q0 选项收窄到一个维度（柑橘 / 青苹果那种酸；乳酸 / 发酵果酸；酸感不明显）；Q2 新增 D「甜感不明显」（Matrix_Q 增量为空）；Q4 新增 C「苦味明显，盖过其他味道」（bitter_roasted:2）；Q5 去掉褒义（味道一层一层，分得清 / 味道混在一起，饱满）。映射器：否定前缀加「没有 / 没什么 / 几乎没 / 不太」，`forced_by_negation` 加 甜 → Q2-D；Q4-A 的线索只留轻度标记（去掉裸「苦」），Q4-C 收强度标记。产地提示改为「不清楚产地也可以继续。」
- 流程规则（设计缺陷修正）：Q2 为「不明显」时增量为空，而 Q3 单独一组方向退化（三种口感答案同向），Q2–Q3 检查不能据此判「明显不一致」——`absentAnswer` 把首次检查封顶在 mild（多问一题，永不 Path 3）。实测：有方向证据的 486 个序列上 Path 1 / 2 / 3+4 = 21 / 52 / 27，与 R3-D10 节奏一致；全部 648 个序列上 Path 1 = 15.7%，因为「不明显」按定义只能走 Path 2。
- 16 组参考风味改名为「两个主要感官参照，不加修饰」：茉莉与白花、小豆蔻与肉桂、蔗糖与蜂蜜、黑加仑与树莓、朗姆与发酵果香、雪松与烟熏、丝绒与糖浆口感、黄桃与熟果、榛果可可与红莓、黑巧克力与烤榛果、柑橘与柚子酸质、烟熏与风干木、重可可与回甘、草本与绿茶、蜂蜜与杏桃、纸味与陈味（原「瑕疵预警」：终卡附一句「值得再喝一口确认，这里不对这杯咖啡做质量判断」，`defect_note`）；成员与质心不变；「标杆豆款」改称「参考实例」，不上屏。
- 维度与概念校对：`fermented_winey` 中文「发酵与酒香」（去「厌氧」）；香料词去「异域」；醋酸 → 醋味；黑糖 → 糖蜜（黑糖留在消费端词表）；红酒 → 酒香；肯尼亚产地标签去「高磷酸」。
- About 阅读顺序：产品用途 → 示例风味卡（标明示例）→ 作者与具体工作（研究、设计与开发 · 潘岱，三个数字各带用途：12 类风味特征 / 16 组参考风味 / 94 个风味词）→ 资料范围（83,031 条风味描述记录；9,128 条评审记录，其中 8,142 条进入分组；4,042 位 GACTT 消费者，非本产品用户；3 份来源，8 条上线 / 3 条待复核；版本与统计日期）→ 两张图（「评审资料如何用于风味描述」，带宽 = 累计权重；「16 组参考风味」）→「风味描述如何形成」（参考资料 / 提问方式 / 描述的选择与确认 / 结果的适用范围）→「技术说明」（公式、阈值、余弦；「不训练模型」只作实现说明）→「资料来源」（本项目如何使用这份资料）。「平均 5.7 道题」不再出现在用户文案。
- 文案总表改为由 esbuild 执行 `view.ts` / `about.ts` 导出，组件内固定文案仍手工登记；每次改源头后重跑 `db/scripts/export-frontend-copy.py`。

**文案审核二 + 移动端整改（R3-D17）**

- 硬错误：UC Davis 条目的 DOI `10.1016/j.foodchem.2020.126567` 实际对应 Chao 等人的姜黄粉光谱鉴别论文，四条 UC Davis 说明全部撤下（`review_state = NEEDS_REVERIFICATION`，locator 清空），来源从读者可见的列表移到内部记录；WCR 许可按官方页面所见记录（可免费下载、打印供个人使用，页面无 CC BY-SA 声明），claims CSV 新增 `use_note` 列，「来源条款」与「本项目的使用」分开展示；owner 自建的成因句是项目规则，改在 About「初始参考如何形成」里解释，不再上卡；中深烘 + 厌氧句去掉「水温偏低」。
- 卡片折叠层「关于这段描述」：初始参考句（由 V_pred 计算：「根据 手冲、浅烘、水洗，初始参考侧重酸质、花香、果香。初始参考来自评审资料的统计，只是起点，不是这杯咖啡的测定。」）→ 第一条有来源的研究参考 → 差异句「相较于初始参考，你的描述中，{特征}更突出 / 较弱。」证据标签：初始参考 / 资料统计 / 研究参考 / 你的描述 / 提示。
- 终卡分组名跟随确认的词：`confirmedProfile = rankProfiles(normalize(V_target + picks))`；用户选的词离开建议分组时，标题随之改变（测试锁定）。
- 题库：Q1 新增「闻不出明显的香气」（增量为空），Q4 改为纯强度（有一点苦 1 / 没有明显苦感 0 / 苦感明显 2，原 A 的 nutty_chocolate 随「回甘」措辞一起去掉）；任何缺席回答都把首次相干检查封顶在 mild。处理法九个选项（日晒、水洗、蜜处理、半水洗、湿刨法、厌氧发酵、乳酸发酵、酒桶发酵、低因），蜜处理等五个在可用向量里不足 30 条，没有参考行，`basis` 写明，V_pred 不受其影响；产地只显示地名。
- 首页：标题中英文都用「Put this cup into words」；上 1 : 下 2，wordmark 放大；下方两块瓷砖「开始 / 关于」，右上角只留中英文切换；流程中回到 1 : 3。所有 icon 控件 54 × 54，chip ≥ 48，选项 ≥ 60，题目置顶，语境 chip 两行（名称 / 拉丁名），卡片进出用 GSAP 弹性缓动。
- About 四页：1 从品饮，到表达 + 风味卡示例；2 研究、设计与开发 · 潘岱 + 三个折叠条目（词汇与风味分组 / 提问方式 / 资料与方法）；3 「评审资料如何用于风味描述」在 320dvh 的轨道里随滚动绘制（面板柱先长出、来源逐个揭开、特征标签最后到位，记录数随进度计数）；4 「本项目整理的 16 组参考风味」随滚动一条条画出射线；末尾资料来源（条款与使用分列）。GSAP ScrollTrigger 以抽屉为 scroller；`prefers-reduced-motion` 时直接完整显示。
- 英文单独编辑：flavor 拼写统一；About this description；3 main suggestions and 5 alternatives；From coffee reviews to flavor descriptions。
- owner 追加：首页两块瓷砖接近正方形；语言切换改为黑色圆角长方形徽章（参考图上的「极浅烘」标签）；配色对齐 Big Sur Coffee 的豆袋卡片——终卡与示例卡用图一的深蓝 #1F3B5C（对比更高），语境与题卡分别用薰衣草紫、青柠绿、赭黄、粉、陶土橙、蜜桃、橄榄绿（图八）。

**文案审核三 + 品牌（R3-D18）**

- 风味卡是产品对象：奶白卡片三层——上层只列已填的这杯信息（冲煮 / 烘焙 / 豆种 / 处理 / 产地，虚线引导）；中层五个确认的词等大（紫色划线的「选择痕迹」当天被 owner 撤回：任何地方不加划线，选中态仍是反白）；下层「参考风味 · 分组名」与 flavorwords 署名；卡顶一排由所选词的特征色生成的图形（叶 / 圆 / 扇）。分组名不再做卡片标题。同一组件 `FlavorCard.vue` 用于终卡、首页与 About 的示例。
- 首页按 owner 的比例：上方 hero 2.25 : 下方 1；字标缩小加粗，「Put this cup into words」加粗，示例风味卡作为主要展示对象；去掉状态绿点；下方两块高长方形亮色按钮（开始 陶土橙 / 关于 青柠绿），语言切换为黑色圆角徽章。
- About：标题「从品味，到表达」；导言两句 + 使命段（8 组评审来源、83,031 条描述、4,042 位消费者、大众点评 / 小红书 / 淘宝烘焙商标签的中文说法）；作者段压缩为一句关注点 + 一句工作；三个折叠条目不变；大数字退出标题层。
- 两张可视化改为整页黑底、随滚动绘制（各 420dvh）：图三「评审资料如何用于风味描述」参照灭绝海报——A–L 十二根柱子（对数刻度、按评审族深浅分段、柱顶数值），底部汇成 8,142 条记录的主干，附评审族索引与特征图例；图四「本项目整理的 16 组参考风味」参照 connect-the-dots——编号圆圈按记录数定大小、按最强特征着色、两环排布，白色曲线连到最接近的两组，C1–C6 标出最接近的几对并列出共同特征，附编号索引与图例。所有文字 ≥ 9.5px。
- 产地按 owner 的产区图：19 个国家按非洲 / 亚洲 / 美洲分组，chip 只显示地名，δ 0.1 的偏置来自各洲常见倾向（非洲果香花香、亚洲木质香料、美洲坚果可可）与少数国家特例。
- 字标 serif 提案（七个 OFL 字体的对比页）已交 owner：Fraunces、Instrument Serif、Young Serif 为推荐顺序。
- owner 追加：About 顺序改为 从品味，到表达 → 柱状主干海报（去掉标题，加占比、细网格与评审族刻度）→ 分组网络（版式收紧，最小字号 11px，SVG 限高）→ 研究、设计与开发 + 三个条目 → 资料来源独占一页（每份资料默认显示用途与本项目使用，链接与条款折叠，页底「回到顶端」）。

**品牌（R3-D19）**

- 首页不再放风味卡（卡片只在流程结尾出现）：上 60% 的白色带里，小字标（「words」用 owner 选定的 Fraunces，自托管，OFL 许可在 `public/fonts`），居中的口号 EVERY TASTE HAS ITS OWN VOCABULARY.、标题「风味，自有表达。」/ Put this cup into words.、owner 的导言段、五个品牌 glyph、行动主张「Put this cup into words.」与带下划线的「从这一口开始 →」；下 40% 两块亮色按钮「开始 / 关于」。链接与按钮是同一动作（交互冗余）。
- About：第一页留白后放 glyph 与 owner 的三段文案（从品味，到表达）；两张海报轨道延长到 560dvh，绘制在 72% 处完成，其余是阅读时间；网络页垂直居中；「设计思路 / 为品味而设计」一页（owner 文案 + 三个条目的 owner 摘要 + 署名行）放在两张可视化之后；末页标题「引用与来源」，去掉导语小字。

**owner 第四轮（R3-D20）**

- 首页：大标题「Every taste has its own vocabulary.」句首大写、只有 taste 的五个字母各一种颜色；「风味，自有表达。」/ Put this cup into words. 为语言标题；导言为正文墨色；「Put this cup into words.」与「从这一口开始 →」两行口号，点击即开始，无下划线（与下方「开始」按钮是同一动作）；下方色带略高，两块按钮 1 : 1.2。字标 FLAVOR / WORDS（WORDS 用 Fraunces 大写）；语言徽章缩小 10%。
- 几何 svg 套件 `BrandGlyphs`（叶 / 圆 / 扇 / 滴 / 环 / 拱 / 楔 / 波）：风味卡顶部一排、首页、About 第一页共用同一组件。
- 题库四选项：Q0 加「酸苦，带点刺激」（owner 原话：酸中带点苦 / 酸苦且带有刺激风味；acidity 2 + bitter_roasted 1 + defect 0.5），Q3 加「有点涩，发干」（body 1 + defect 0.5），Q5 改为 分得清 / 饱满 / 有点杂（fermented 0.5 + defect 0.5）/ 说不上来（空）。有方向证据的序列上节奏实测 20 / 49 / 31，测试带宽相应放宽。
- 语境题按饮者口吻：怎么制作的？/ 咖啡豆的处理法 / 咖啡豆的产地（可选）；大洲标题与自己的 chip 贴合并放大一倍。
- 卡片：勾选后的收集卡题为「候选风味描述」；五个词行距收紧；切换语言时 `relocalize` 重新推导描述、勾选与卡片（修复英文状态下卡片不切换）；分享导出 1200×1200 PNG（Canvas 2D 绘制，同一模型），底部三个圆角矩形按钮上移。
- About：海报页居中并放大字号；英文网络页不再溢出；「动态问答模型」；设计页与来源页各自 pin 一拍（170dvh 轨道 + sticky），三个「+」三种颜色，署名行在条目之后；来源页右下角 TOP；关闭按钮圆角矩形；资料范围块不再在数字、日期、版本号中折行。
- MiSans：从 owner 下载的 woff2 用 `apps/pwa/scripts/subset-fonts.py` 裁到应用可显示的 963 个字符（每个字重约 133KB），进入 service worker 预缓存。

**owner 第五轮（R3-D21）**

- 风味词只用具体对象：酸质 葡萄柚 / 血橙 / 青柠，甜感 蔗糖 / 蜂蜜 / 焦糖，醇厚 丝绒奶油 / 慕斯 / 奶油，烘烤 黑巧克力 / 烟熏可可 / 炭烧，发酵 朗姆酒 / 红酒 / 酒酿，香料 小豆蔻 / 肉桂 / 丁香，草本 茉莉绿茶 / 高山乌龙 / 柠檬草，瑕疵 纸味 / 陈味 / 霉味；原先的形容词（清冽果酸、高甜感、丝绒感、黑巧回甘…）留作输入别名，不再出词。
- 第一题九种做法：意式萃取、手冲、摩卡壶、冷萃、虹吸壶、冰滴、法压壶、土耳其壶、爱乐压；滤泡与浸泡借杯测行，摩卡与冷做法没有参考行。前两张语境卡换更亮的颜色。
- Q3-D「发涩，像喝了浓茶」；Q4「微苦，像可可或坚果皮 / 没有明显苦感 / 苦得明显，像浓缩或炭烧」；Q5 按 owner 的四句：味道混在一起，各种风味都有一点（fermented 0.5 + body 0.5 + fruity 0.5）/ 饱满圆润，一致性很高（body 1 + sweetness 0.5）/ 能分清楚多种味道，层次明确（floral 1 + acidity 1）/ 感觉不错但说不上来（空）。
- 卡片折叠层的研究参考与差异句随确认的词变化（`textSeed` 选参考句与措辞，含双特征句式）；卡上五个词的位置下移。
- 字标改为单个 SVG（FLAVOR 用 Stack Sans、WORDS 用 Fraunces，`textLength` 让两行等宽）；首页文字块上移一点；两块按钮加高 20px。
- About：设计页与来源页只在折叠态 pin（展开即解除，去掉内层滚动的卡顿）；TOP 改为淡出、跳转、淡入，不再倒放绘制动画；产地大洲标题独占一行贴自己的选项。
- Stack Sans Text 从 owner 下载的可变 TTF 转为 woff2 自托管，OFL 随附；三套字体到齐。

**第二行说明的变化、Q6 门槛、英文适配、部署层（R3-D22）**

- 卡片折叠层第二行：每条上线的研究参考带第二种措辞（claims CSV `claim_*_alt`，同一来源），另有「资料统计」句（这杯语境里一条实测参考行的记录数与前两个特征），三者按杯、回答与所选词的种子轮换。
- Q6 门槛：原来的绝对阈值组合（≥0.80 且 <0.65）几乎不可能同时成立，9,216 个序列 × 3 个语境里只有 2.8% 开启；改为「出现过明显冲突后，勾选更偏向自己的回答而非初始参考（相似度差 ≥ 0.08）」即开启。
- 英文：首页导言缩短、语言标题略小，口号起点与中文版对齐；About 标题 Design for taste，段落与条目摘要缩短；海报页英文版导语通栏、索引换行不截断。
- 动态问答模型（owner：固定顺序 + 静态选项 + 几乎不开的 Q6 不算动态）：第二题起每一题的提问承接上一题的回答（`prompt_variants`，Q1–Q4 各四种、Q5 三种，中英文）；每题选项按「该选项增量与 normalize(V_pred + Σ 已答增量) 的余弦」重新排序，「不明显」类永远在最后（`session.rankedOptions`）；第二轮（Q6）在流程判定的修正路径（2/3/4）上、勾选更偏向自己的回答而非初始参考（相似度差 ≥ 0.08）时开启，明显冲突后勾选离开参考也开启。9,216 个序列 × 3 语境实测：默认勾选下 Q6 开启 37.9%（Path 1 从不、Path 2 40%、Path 3 67%、Path 4 27%），偏向自己的勾选下 66%；一致的 Persona A 仍是五题无 Q6。
- 部署：仓库根目录 `vercel.json`（npm ci → npm run pwa:build → apps/pwa/dist，sw.js 不缓存、字体与资源长缓存）；`index.html` 带描述、Open Graph、hreflang、canonical、SVG 图标、JSON-LD（WebApplication：作者、引用、语言）与双语 noscript 摘要；`public/` 有 robots.txt、sitemap.xml、humans.txt 与 `llms.txt`（产品做什么、方法、资料范围与来源），manifest 补齐名称、描述与图标。

---

**Q6 触发概率、前台测试序列、英文 About、推送准备（R3-D23）**

- 触发概率按穷举推定：题库全部 3,072 种答案组合 × 6 种语境 = 18,432 条序列。按候选顺序勾前 5 个词时 34.2% 开启 Q6，随机勾 5 个时 20.1%，勾选偏向自己答案的 5 个时 63.3%。Path 1（12.5% 的序列）永远不开，是设计；Path 2 为 36 / 22 / 70%，Path 3 为 65 / 33 / 96%，Path 4 为 32 / 24 / 67%。门槛同时看路径与勾选，所以最容易触发的序列在 56 种 5 词组合里也只有约一半会开 Q6；测试序列因此写明要勾的 5 个词。
- 前台测试集 `docs/product/Q6_TRIGGER_TEST_SET.md`：7 条会开 Q6 的序列（含精确的题面、选项顺序、候选词与勾选）加 1 条 Path 1 对照；回归测试 `tests/product-vector-v1-q6-trigger.test.ts` 固定下限（Path 1 = 0；前 5 个 ≥ 20%；偏向自己 ≥ 45%；各分歧路径 ≥ 25%）并逐条验证 7 条序列进入 Q6、更新后卡片标记已确认。第 1 条与第 6 条在浏览器里走通。
- 英文 About：来源海报的评审族标签缩短、图表上限 50dvh、引言缩短一行，383 × 827 下内容顶部落在 sticky 头之下、底部余 27 px；风味谱系页英文上边距 116 → 106 px，中文不变。
- 推送准备：分支新增的两份来源账本（109.9 MB、100.8 MB）超过或逼近 GitHub 100 MiB 硬限制，迁入 Git LFS（未推送分支用 `git lfs migrate import` 重写历史）；读取它们的两个 workflow 的 checkout 打开 `lfs: true`；Vercel 侧 LFS 保持关闭。`package.json` 固定 Node 22.x；`vercel.json` 过 prettier；Vercel 导入表单逐项写在 `docs/deploy/VERCEL_DEPLOYMENT.md`。
- PWA 与 GitHub 就绪：图标只有白底加现有 wordmark（FLAVOR / WORDS 从随包的 Stack Sans、Fraunces 描成轮廓，SVG 不依赖字体；另出 PNG 192 / 512 / apple-touch 180 与 maskable 项）。仓库的 prettier 契约覆盖到 PWA 与 product-vector 源码（生成器产物加入 ignore），删去两个未引用组件，product-inference-v0.2 的 SHA256SUMS 按 F19 修复与设计 V1 重新生成的两份文件刷新——否则 GitHub 的 checks 任务会红。

**平板与桌面布局（R3-D24）**

- 仍是移动优先：宽屏上色带保持全出血，内容放进一列居中的内容列。手机全宽；640px 起（iPad mini、iPad Air 竖屏）600px；1024px 起（平板横屏、桌面）680px。首页两块按钮保持 1 : 1.32，改由色带高度与半列宽度约束，不再随宽度拉伸压住标题。About 抽屉的顶栏、第 1 页与四个 sticky 面板、Q6 弹层用同一列。没有新增元素、字号或文案。
- 用无头 Chromium 在 744×1133、820×1180、1180×820、1440×900 截图核对首页、语境卡与 About 五页；390×844 手机回归不变。

## 9. 脚本统筹（229 个脚本）

| 组                                     | 处置            | 内容                                                                                                                                                                                                                                                                                                                                |
| -------------------------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **主管线（保留、继续维护）**           | 8 个            | `acquire-professional-descriptors-batch2.py`, `acquire-coffeereview-round3.py`, `generate-current-descriptor-data.py`, `generate-batch4-cleaned-30k.py`, `generate-batch6-semantic-corpus.py`, `descriptor-pipeline.py`, `generate-ci-artifact-checksums.py`, `ci-verify-current-artifacts.sh`                                      |
| **产品向量层（新）**                   | 4 个 + 前端引擎 | `extract-coffeereview-structure-scores.py`（结构打分、烘焙度、产地国）, `extract-coffeereview-c2-labels.py`（品种/处理法标签）, `build-product-vector-v1.py`（投影 → 向量库 → 画像 → 四项测量）, `build-matrix-k-v1.py`（Matrix_K + 运行时 bundle `product-vector-v1.json`）; `packages/flavor-data/src/product-vector-v1/index.ts` |
| **归档：推理策略线**                   | 7 个            | `inference_state_machine_round2.py`, `proposition_lattice_round2.py`, `evidence_reader_round2.py`, `output_generator_round2.py`, `generate-product-inference-v0.py`, `generate-product-inference-v02.py`, `run-product-inference-v0.py`                                                                                             |
| **冻结：研究轮次 R1–R12 / round3a–3m** | ~190 个         | 训练实验、监督、审计、各轮 artefact 生成器。保持可复现（CI 仍跑），不再扩展                                                                                                                                                                                                                                                         |
| **测试**                               | 23 个           | 只保留主管线的 15 阶段 CI 作为提交闸门；不再为归档线新增测试；不再为产品向量层写测试脚手架，用 §7 的四项测量代替                                                                                                                                                                                                                    |

规则：归档脚本与其数据目录保持原样（多处 sha256 血缘指向它们），只加「ARCHIVED」标记；新工作一律进产品向量层。

---

## 10. 产品定位与开发状态预估

**定位（一句话）：** 一个不需要账号、不需要服务器的 PWA，**科学感官诊断与风味探索工具**：用三道语境题 + 六道感官题描述一杯咖啡，
告诉你「理论上它该是什么味、你实际尝到了什么、差在哪、为什么」，先给出你最契合的目标风味画像，再给经典标杆豆款和你自己库里最接近的那一支。
它的护城河不是模型，而是**这份被清洗、去膨胀、带权利标签的 83K 专业描述语料和它投影出的向量空间**。

**开发状态：**

| 层           | 状态                                                                                                                     | 依据         |
| ------------ | ------------------------------------------------------------------------------------------------------------------------ | ------------ |
| 语料与语义层 | **完成**（83K，5,656 聚类，141,460 关系边）                                                                              | CR-1b / CR-2 |
| 投影矩阵     | 12 维草案完成，94/94 覆盖，**待 owner 逐行审阅**                                                                         | §1.2         |
| 向量库       | **完成**（8,899 可用，含结构打分轴）                                                                                     | §5.1         |
| 画像库       | 16 个画像，15 个挂上 owner 命名与标杆豆款；1 个操作员提案待确认                                                          | §5.3         |
| Matrix_Q     | 完成（owner 给定）                                                                                                       | §3           |
| Matrix_K     | C0×C1 可算未算；C2 缺数据                                                                                                | §2           |
| 比较/校准    | 公式定稿；α = 0.5（R3-D8，不再微调）；结构轴权重 0.6                                                                     | §4 / §5.3    |
| 表达层       | 完成：词库（12 维列表 + 94 概念 + 29 条消费端词）、27 条归因句、双语 `present()`                                         | §6           |
| 问答流       | 完成：相干性决策树（签名空间 0.80 / 0.65 + 极性悖论守卫 + 语境冲突检查）、3+5 描述、8 选 5、升阶门控、Q6（α_strong 0.9） | §3.1 / §3.4  |
| 题库与映射器 | 完成：口语化题库（R3-D12 批准）、混合映射器、否定守卫                                                                    | §3.2 / §3.3  |
| 会话接口     | 完成：`session.ts` 全链路（题卡 → 描述 → 8 选 5 → 门控 → 总结卡 / Q6），历史记录                                         | §3.4         |
| 消费端词表   | 第一轮：29 + 5 中文，61 英文（GACTT）；中文社媒扩充等语料                                                                | §6.2         |
| 应用接口层   | 完成：视图模型、Dexie 用户库、About 内容；拼配与产地进引擎                                                               | §3.5         |
| 应用壳       | 视觉第一轮完成：调性、1 : 4 布局、卡片折叠流、表达层、About 光谱；分享 PNG 与字体文件待 owner                            | §8           |
| 文献声明     | 11 条 claims 入库并在界面与 About 两层标注；DOI/许可待 owner 补                                                          | §6.3         |
| 测试         | 51 个：引擎 / 表达层 / 节奏 / 语义歧义 28+5 / 画像 4+10 / 会话 6 / 应用层 8                                              | §7.5         |
| 用户自建库   | 未开始（本地存储 + 录入表单 + 扫码）                                                                                     | §8           |
| 前端运行时   | 未开始；现有前端是 v0.2 目录的 demo                                                                                      | §8           |
| 充分性       | 4 项里 3 项过（饱和、稀疏主干、视野 95%），均匀度差最后一个轴（fermented_winey）                                         | §7           |

**已决定（R3-D6 / R3-D7）：** 12 维；画像优先 + 标杆豆款 + 用户自建库；CoffeeReview 1–10 打分接入 body/acidity，权重 0.6 : 1.0；
WCR Varieties Catalog、UC Davis Coffee Center、Coffee Ad Astra 批准接入（机理句标 `LITERATURE_CLAIM`）。

**owner 的执行顺序与状态：**

| Step | 内容                                                                          | 状态                                                                                                                                          |
| ---- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | 12 维投影矩阵，94 行审阅 → `owner_reviewed=true`                              | 完成（按 R3-D7 以草案整体批准登记；逐行修正随时可改）                                                                                         |
| 2    | 从 83K 语料导出 C0×C1 的 Matrix_K，融合 Body/Acidity 打分                     | 完成（`MATRIX_K.tsv`，22 行）                                                                                                                 |
| 3    | 解析评论正文，抽取品种/处理法，补齐 K[C2]                                     | 完成第一版（10 个品种行 + 4 个处理法行；honey 词表待细化；WCR 行待接入）                                                                      |
| 4    | 前端运行时 `packages/flavor-data/src/product-vector-v1`，纯 JS 推荐与归因引擎 | 引擎完成（`infer()`：V_pred / V_user / ΔV / V_target / 画像与豆款排序 / 语境证据基础），5 个引擎测试通过；页面与用户自建库（IndexedDB）未开始 |
| 5    | 产品级风味描述与用户用语对齐（owner 新要求）                                  | 未开始：用已批准的 GACTT 消费者描述建立「消费者用语 → 12 维」词表，画像命名与归因文案都从它取词                                               |

**仍待 owner：** 视觉参考（下一步）；三份文献的 DOI/链接与许可说明；WCR / UC Davis / Coffee Ad Astra 的 `*.claims.csv` 放入 `db/data/external-literature/`（README 有列定义），
`ingest-external-literature.py` 会把它们并入归因句表。

---

## 11. 补充数据源（按「逐一审阅后批准」规则，未取数）

| 来源                                                  | 用途                                                             | 状态                                                                           |
| ----------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| WCR Varieties Catalog                                 | K[C2_variety] 的 sensory potential；品种词表；标杆豆款的品种依据 | **批准（R3-D7）**；接入口 `db/data/external-literature/<source_id>.claims.csv` |
| UC Davis Coffee Center（研磨度–水温–萃取率–感官图谱） | K[C0] 的萃取机理句证据，`LITERATURE_CLAIM`                       | **批准（R3-D7）**；同上                                                        |
| Coffee Ad Astra（Gagné：EY% / TDS 与风味强度）        | 归因里的萃取解释，`LITERATURE_CLAIM`                             | **批准（R3-D7）**；同上                                                        |
| CoffeeReview Body/Acidity 打分列                      | 已接入（R3-D6）                                                  | 完成                                                                           |
| GACTT（T2 消费者描述）                                | 消费者语言 → Q5–Q10 文案校准；fermented 轴用词                   | 已批准，未接入                                                                 |
| Dryad B8993H（消费者偏好）                            | 校准层                                                           | 已在 R1                                                                        |

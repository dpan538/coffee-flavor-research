# 风味向量设计 V1 (Flavor Vector Design V1)

**Status:** ACTIVE — owner decisions R3-D5 (pivot), R3-D6 (dimension count, candidate-library path, structure axes) and R3-D7 (confirmation: 0.6 : 1.0 structure weight, data sources, Steps 1–4), 2026-09-12
(`db/data/backend-sequential-model-v2/revisions/round3/owner_decisions_round3.json`).
**Supersedes:** the adaptive-question / proposition-lattice / product-inference v0–v0.2 line. Those artefacts are archived, not deleted: `docs/archive/adaptive-question-policy-20260912/README.md`.
**Owner's words:** 「做向量然后进行相似度算法设计 … 做一个小而美的产品，后续产品中不再需要训练或者 transformer。停止无意义测试，数据的可用性比测试更重要。」

---

## 0. 这一轮决定了什么

| 保留 | 替换 |
|---|---|
| 数据管线：acquire → clean → semantic → consolidation（83K 检查点）| 推理机制：有限状态机 + 命题格 + 问题轴策略 → **12 维向量 + 余弦相似度** |
| 概念注册表（94 个规范概念）与 5,656 个聚类 | 产品策略检查点 product-inference v0 / v0.2（120 用例、100 行审阅包）→ 归档 |
| 权利治理：按数据集逐一审批；分数不是概率；不训练 | 「训练/不训练」的争论 → 设计上不需要训练；MLP 只是 V_pred 的可选实现，未计划 |
| 语境层 C0（冲煮）/ C1（烘焙）| 语境扩展为 **C0–C2 三道题**：冲煮、烘焙、豆种 + 处理法 |
| —— | 产品定位：**科学感官诊断与风味探索工具**，不是咖啡导购。输出先给「目标风味画像」，再给标杆豆款与用户自建库的匹配 |

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

5,656 个聚类中 83 + 8 + 3 个已经指向规范概念（EXISTING_CANONICAL_*），直接继承投影行。
其余 4,396 个 GENUINE_ONTOLOGY_CANDIDATE 里，`assertion_support ≥ 20` 的只有 351 个 —— 这 351 个是「完成标准空间量化」
真正要人工映射的范围，其余是长尾，先不映射（它们对余弦几乎没有贡献）。

---

## 2. 前置语境 C0–C2 → V_pred

三道题，四个变量：

| 题 | 变量 | 选项 | 后台物理/化学逻辑（owner 表述，证据状态见 §6）|
|---|---|---|---|
| C0 | 冲煮方式 | 手冲(V60) / 意式浓缩 / 冷萃 / 法压 | 萃取动力学与分子量截断：冷萃抑制低挥发酸；意式放大醇厚度与油脂 |
| C1 | 烘焙度 | 浅 / 中 / 深（数据侧对应 CoffeeReview 的 Light … Very Dark 六档）| 绿原酸降解与美拉德产物占比：浅烘高酸/花果，深烘高醇厚/焦糖苦 |
| C2 | 豆种 + 处理法（一题两栏）| 瑰夏 / 波本 / 铁皮卡 / 罗布斯塔 … × 水洗 / 日晒 / 蜜处理 / 厌氧 | 品种定风味上限（基因型），处理法定前体物质积累：日晒→还原糖/游离氨基酸↑→果酱、热带水果、高甜；水洗→内源有机酸突出→干净、柑橘、花香、高酸；厌氧→乳酸与外源酯类→酸奶、酒香 |

`V_pred = normalize( K[C0] + K[C1] + K[C2_variety] + K[C2_process] )`，`Matrix_K` 每个选项一行 12 维。

**Matrix_K 的来源分两层，状态不同：**

1. **可以现在从 83K 语料算出来的**：C0 × C1。CoffeeReview 每条评论带 Roast Level 与冲煮方式（cupping / espresso），
   按格子统计向量均值即得 K 行。格子密度（7,300 杯）：

   | 格子 | 杯数 | 格子 | 杯数 |
   |---|---|---|---|
   | CUPPING × Medium-Light | 3,110 | ESPRESSO × Medium-Light | 315 |
   | CUPPING × Light | 1,215 | ESPRESSO × Medium | 279 |
   | CUPPING × Medium | 1,110 | ESPRESSO × Medium-Dark | 131 |
   | CUPPING × Medium-Dark | 448 | ESPRESSO × Dark | 18 |
   | CUPPING × Very Dark | 272 | ESPRESSO × Light | 16 |
   | CUPPING × Dark | 121 | ESPRESSO × Very Dark | 13 |

   主干格子远超 owner 的 100+ 标准；意式 × 浅/极深两格只有十几杯，属于「插值」格子。冷萃、法压在语料里没有。

   **已算出（Step 2，`build-matrix-k-v1.py` → `MATRIX_K.tsv`, `MATRIX_K_C0_C1_CELLS.tsv`）**：C0 两行（cupping 作 V60 / 法压的
   滤泡代理，espresso 实测），C1 六行，12 个 C0×C1 联合格子（8 个 MAIN ≥100 杯，4 个 INTERPOLATION 10–99 杯）。冷萃无语料行，
   标 `NO_CORPUS_ROW_LITERATURE_CLAIM_PENDING`，等 UC Davis / Coffee Ad Astra 的萃取结论。

2. **C2（Step 3，`extract-coffeereview-c2-labels.py` → `COFFEEREVIEW_C2_LABELS.tsv`）**：用关键词词表在评论名称、产地与正文里
   抽取品种与处理法（只输出类别标签，不输出文本）。8,387 条评论：品种可解析 3,586（43%），处理法 4,304（51%），两者皆有 2,517。
   进入 Matrix_K 的行（单标签、成员 ≥ 50 / ≥ 30）：

   | 品种 | 杯 | 品种 | 杯 | 处理法 | 杯 |
   |---|---|---|---|---|---|
   | ethiopian_landrace | 565 | caturra | 166 | washed | 1,819 |
   | gesha | 447 | bourbon | 154 | natural | 879 |
   | sl28_sl34 | 259 | catuai | 90 | decaf | 66 |
   | typica | 88 | robusta | 64 | anaerobic | 52 |
   | pacamara | 55 | castillo | 51 | | |

   honey（145 条）因大多同时出现 washed/natural 字样被判多标签而未入行，需要词表细化。WCR Varieties Catalog（已批准）
   将补 K[C2_variety] 的 sensory potential 与标准品种词表；语料实测行与 WCR 行并列，各带 basis。

---

## 3. 感知题 Q5–Q10 → V_user

`V_user = normalize( Σ Q[question][answer] )`，增量按 owner 给定（只作用于前 8 维；spice / herbal_green / woody_earthy / defect
在 V_user 中为 0，等新的感知题再补）：

| 题 | 选项 | 增量 |
|---|---|---|
| Q5 酸质 | A 鲜明柑橘/苹果酸 | acidity+2, fruity+1 |
| | B 柔和乳酸/发酵酸 | acidity+1, fermented_winey+2 |
| | C 几乎无酸，平顺 | body+1 |
| Q6 甜感 | A 花蜜/蔗糖 | floral+1, sweetness+2 |
| | B 焦糖/黑巧 | nutty_chocolate+2, bitter_roasted+1 |
| | C 熟果/果酱 | fruity+2, sweetness+2 |
| Q7 触感 | A 绿茶/果汁 | body+1 |
| | B 牛奶/丝绒 | body+2 |
| | C 黑巧/糖浆 | body+3, bitter_roasted+1 |
| Q8 香气 | A 花香草本 | floral+3 |
| | B 坚果烤面包 | nutty_chocolate+3 |
| | C 热带水果微醺 | fermented_winey+2, fruity+2 |
| Q9 苦感 | A 微苦回甘 | nutty_chocolate+1, bitter_roasted+1 |
| | B 无苦 | （无增量）|
| Q10 复杂度 | A 层次分明干净 | floral+1, acidity+1 |
| | B 交融浓郁 | fermented_winey+1, body+1 |

3×3×3×3×2×2 = 324 种答案组合，即 324 个可能的 V_user；§7 的用户视野测试就是穷举这 324 个。

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

| 指标 | 8 维 + 仅描述词 | 12 维 + 打分 1:1 | **12 维 + 打分 0.6，需 ≥1 描述词** |
|---|---|---|---|
| 咖啡总数 | 9,128 | 9,128 | 9,128 |
| 可用向量 | 6,871 | 8,899 | **8,142** |
| 单薄 / 空 | 1,311 / 946 | 66 / 163 | 66 / 920 |
| 杯均映射概念数 | 4.54 | 3.69 | 4.03 |

### 5.2 候选库的权利出路（R3-D6 第二项）

CoffeeReview 的批准（R3-D2）是「内部研究」：它的向量用于标定 Matrix_K、构造画像、验证算法、模拟用户；
**不作为公开产品里被推荐的商品条目**。CoE 记录是公开发现、无许可声明，同样不直接推荐。owner 决定的复合模式：

1. **风味画像优先**：匹配结果第一优先输出「目标风味画像（Target Profile Vector）」——例如「高纬度水洗、强烈柑橘与清脆苹果酸质的中浅烘画像」。
2. **标杆豆款**：画像下方给出匹配该画像的代表性经典风味模板（瑰夏 / 肯尼亚 AA 等），由 owner 命名与挑选，不引用 CoffeeReview 具名商品。
3. **用户/社区自建库**：用户录入或扫码自己手头的豆子，本地离线匹配。

### 5.3 画像库（数据驱动的第一版，等 owner 命名）

`FLAVOR_PROFILE_LIBRARY.tsv`：对 8,142 个可用向量做确定性 k-means（k = 16，最远点初始化），每个画像有质心、成员数、
前三维、来源族构成、瑕疵均值，以及留空的 `owner_name_zh / owner_name_en / benchmark_beans`。

| # | 成员 | 质心前三维 | 读法 |
|---|---|---|---|
| 1 | 1,343 | fruity .79, acidity .42, sweetness .40 | 甜果主干 |
| 2 | 1,169 | nutty_chocolate .61, fruity .57, acidity .39 | 坚果巧克力 + 果 |
| 3 | 983 | sweetness .72, fruity .54, acidity .32 | 甜果 |
| 4 | 757 | nutty_chocolate .88, body .28, bitter_roasted .25 | 经典坚果巧克力 |
| 5 | 720 | nutty_chocolate .61, woody_earthy .54, bitter_roasted .38 | 深烘坚果木质 |
| 6 | 639 | fruity .71, acidity .64, body .25 | 明亮果酸 |
| 7 | 606 | sweetness .90, nutty_chocolate .24, body .23 | 甜为主 |
| 8 | 592 | fruity .60, woody_earthy .55, acidity .40 | 果 + 木质 |
| 9 | 387 | floral .72, acidity .37, fruity .33 | 花香 |
| 10 | 325 | woody_earthy .86, bitter_roasted .36, sweetness .22 | 木质烟熏 |
| 11 | 273 | spice .75, acidity .31, fruity .29 | 香料 |
| 12 | 217 | bitter_roasted .87, nutty_chocolate .26, body .22 | 深烘苦 |
| 13 | 60 | fermented_winey .65, acidity .52, nutty_chocolate .48 | 发酵酒香 |
| 14 | 47 | herbal_green .77, acidity .36, fruity .34 | 草本青草 |
| 15 | 12 | defect .99 | 瑕疵（负向集合）|
| 16 | 12 | body .91, acidity .36 | 结构主导残余（12 杯，可并入 7）|

0.6 权重与「≥1 描述词」规则之后，结构打分主导的假画像消失（首版的 550 + 334 杯降到 12 杯）。

---

## 6. 归因输出

推送画像与候选时给出结合物理化学的解释。模板由三部分拼成：

1. **吻合/偏置陈述**：取 |ΔV| 最大的 1–2 维，按符号选「吻合」或「发现有趣偏置」句式。
2. **语境物理句**：从 §2 的物理/化学逻辑表取该 C0–C2 组合对应的句子。
3. **证据指针**：每条物理句必须带 `evidence_state`：`LITERATURE_CLAIM`（有 round3h `relationship_evidence_claims.tsv` 条目）
   / `CORPUS_MEASURED`（Matrix_K 从 83K 算出）/ `OWNER_STATEMENT`（仅 owner 表述，未对证）。

owner 给的两个示例（匹配度 94%…；发现有趣偏置…）作为文案基准收录在 `docs/product/attribution_examples_zh.md`（待写）。
「V60 冲煮水温偏低导致后段大分子苦酚萃取不足」这类机理句在写入产品前需要 Coffee Ad Astra / UC Davis 的对应数据（§11）。

---

## 7. 数据充分性：owner 的四项测试，当前读数

`db/data/product-vector-v1/PRODUCT_VECTOR_V1_MEASUREMENT.json`

**7.1 饱和曲线（Saturation）**

| 检查点 | 断言 | 聚类 | 聚类增长 / 数据增长 |
|---|---|---|---|
| 50K | 50,034 | 3,215 | — |
| 77K | 77,038 (+54%) | 5,050 (+57%) | ≈ 1.0 |
| 83K | 83,031 (+7.8%) | 5,656 (+12%) | ≈ 1.5 |

未饱和。但新聚类几乎全是长尾：`assertion_support ≥ 5` 的聚类只有 845 个，≥ 20 的 351 个。对余弦推荐而言，
空间的「主干」早已稳定；增长发生在对推荐没有影响的尾部。结论与 owner 一致：**停止无差别爬取，转向定向补缺。**

**7.2 交叉组合稀疏度（Sparsity）**：C0 × C1 见 §2 表；C2 未测（无字段）。

**7.3 分布均匀度（Uniformity）**，8,142 杯可用向量的「最强维度」占比：

| 维度 | fruity | nutty_chocolate | sweetness | acidity | woody_earthy | floral | bitter_roasted | spice | herbal_green | fermented_winey | body | defect |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 12 维 + 打分 0.6 | 31.7% | 22.7% | 20.3% | 9.7% | 5.1% | 4.7% | 3.3% | 1.8% | 0.3% | 0.2% | 0.1% | 0.1% |
| （8 维、仅描述词）| 35.6% | 23.4% | 21.1% | 10.3% | — | 5.3% | 3.8% | — | — | 0.1% | 0.4% | — |

「最强维度」几乎不会是 body：0.6 的权重使结构轴成为第二、第三维而非主导维，这正是 owner 要的效果（在 1:1 时 body 曾以
假画像的形式占 3.9%）。**fermented_winey 仍是空轴**（0.2%）——
专业评审很少把发酵感写成独立描述词，而 Q5-B / Q8-C 会把用户推向这一维。这是剩下的最后一个长尾区，
定向补缺的第一目标（厌氧/特殊处理豆的评论；GACTT 消费者描述里 "boozy / winey / funky" 的用法）。

**7.4 用户视野测试（Query Horizon）**，324 个模拟 V_user：

| 指标 | 8 维、仅描述词 | 12 维 + 打分 1:1 | **12 维 + 打分 0.6，≥1 描述词** | owner 标准 |
|---|---|---|---|---|
| top-1 相似度均值 / 最小 | 0.927 / 0.786 | 0.949 / 0.838 | **0.934 / 0.779** | — |
| top-3 全部 > 0.85 的用户 | 266 / 324 (82%) | 309 / 324 (95%) | **281 / 324 (87%)** | 100% |
| top-3 三杯互不重复的用户 | 324 / 324 | 324 / 324 | 324 / 324 | 100% |
| 出现在任何 top-3 里的不同咖啡 | 200 | 323 | **270** | 越多越好 |
| 单杯被推荐最多次数 | 35 | 33 | 31 | — |

0.6 权重是 owner 有意的取舍：1:1 时的 95% 有一部分是靠结构打分把 Q7-C（重醇厚）用户推给描述词稀少的杯换来的。
现在剩下的 43 个用户分两类：Q7-C 高 body 组合（结构轴不再主导）和 Q5-B + Q8-C 高发酵组合（7.3 的空轴）。前者靠
标杆豆款与用户自建库补（它们不受描述词稀疏影响），后者靠 fermented_winey 定向补缺。

---

## 8. 运行时形态

- 一个 JSON：投影矩阵、Matrix_K、Matrix_Q、画像库（16 个质心 + owner 命名）、标杆豆款向量、α。
- 一段前端代码：加权求和 + 余弦 + top-k + 模板拼接；用户自建库存本地（IndexedDB），匹配离线完成。
- 落点 `packages/flavor-data/src/`（现有 `research/session.ts` 消费的 v0.2 目录将被替换为 `product-vector-v1`）。
- 无服务器、无训练、无模型文件。MLP 仅当 Matrix_K 的线性求和被证明不够时才考虑，且输入输出都在这 12 维内；当前不计划。

---

## 9. 脚本统筹（229 个脚本）

| 组 | 处置 | 内容 |
|---|---|---|
| **主管线（保留、继续维护）** | 8 个 | `acquire-professional-descriptors-batch2.py`, `acquire-coffeereview-round3.py`, `generate-current-descriptor-data.py`, `generate-batch4-cleaned-30k.py`, `generate-batch6-semantic-corpus.py`, `descriptor-pipeline.py`, `generate-ci-artifact-checksums.py`, `ci-verify-current-artifacts.sh` |
| **产品向量层（新）** | 4 个 + 前端引擎 | `extract-coffeereview-structure-scores.py`（结构打分、烘焙度、产地国）, `extract-coffeereview-c2-labels.py`（品种/处理法标签）, `build-product-vector-v1.py`（投影 → 向量库 → 画像 → 四项测量）, `build-matrix-k-v1.py`（Matrix_K + 运行时 bundle `product-vector-v1.json`）; `packages/flavor-data/src/product-vector-v1/index.ts` |
| **归档：推理策略线** | 7 个 | `inference_state_machine_round2.py`, `proposition_lattice_round2.py`, `evidence_reader_round2.py`, `output_generator_round2.py`, `generate-product-inference-v0.py`, `generate-product-inference-v02.py`, `run-product-inference-v0.py` |
| **冻结：研究轮次 R1–R12 / round3a–3m** | ~190 个 | 训练实验、监督、审计、各轮 artefact 生成器。保持可复现（CI 仍跑），不再扩展 |
| **测试** | 23 个 | 只保留主管线的 15 阶段 CI 作为提交闸门；不再为归档线新增测试；不再为产品向量层写测试脚手架，用 §7 的四项测量代替 |

规则：归档脚本与其数据目录保持原样（多处 sha256 血缘指向它们），只加「ARCHIVED」标记；新工作一律进产品向量层。

---

## 10. 产品定位与开发状态预估

**定位（一句话）：** 一个不需要账号、不需要服务器的 PWA，**科学感官诊断与风味探索工具**：用三道语境题 + 六道感官题描述一杯咖啡，
告诉你「理论上它该是什么味、你实际尝到了什么、差在哪、为什么」，先给出你最契合的目标风味画像，再给经典标杆豆款和你自己库里最接近的那一支。
它的护城河不是模型，而是**这份被清洗、去膨胀、带权利标签的 83K 专业描述语料和它投影出的向量空间**。

**开发状态：**

| 层 | 状态 | 依据 |
|---|---|---|
| 语料与语义层 | **完成**（83K，5,656 聚类，141,460 关系边）| CR-1b / CR-2 |
| 投影矩阵 | 12 维草案完成，94/94 覆盖，**待 owner 逐行审阅** | §1.2 |
| 向量库 | **完成**（8,899 可用，含结构打分轴）| §5.1 |
| 画像库 | 16 个数据驱动画像已切出，**待 owner 命名与配标杆豆款** | §5.3 |
| Matrix_Q | 完成（owner 给定）| §3 |
| Matrix_K | C0×C1 可算未算；C2 缺数据 | §2 |
| 比较/校准 | 公式定稿；α 与「结构轴 : 描述轴」权重待定 | §4 / §5.3 |
| 归因文案 | 模板结构定稿；机理句缺证据 | §6 |
| 用户自建库 | 未开始（本地存储 + 录入表单 + 扫码）| §8 |
| 前端运行时 | 未开始；现有前端是 v0.2 目录的 demo | §8 |
| 充分性 | 4 项里 3 项过（饱和、稀疏主干、视野 95%），均匀度差最后一个轴（fermented_winey）| §7 |

**已决定（R3-D6 / R3-D7）：** 12 维；画像优先 + 标杆豆款 + 用户自建库；CoffeeReview 1–10 打分接入 body/acidity，权重 0.6 : 1.0；
WCR Varieties Catalog、UC Davis Coffee Center、Coffee Ad Astra 批准接入（机理句标 `LITERATURE_CLAIM`）。

**owner 的执行顺序与状态：**

| Step | 内容 | 状态 |
|---|---|---|
| 1 | 12 维投影矩阵，94 行审阅 → `owner_reviewed=true` | 完成（按 R3-D7 以草案整体批准登记；逐行修正随时可改）|
| 2 | 从 83K 语料导出 C0×C1 的 Matrix_K，融合 Body/Acidity 打分 | 完成（`MATRIX_K.tsv`，22 行）|
| 3 | 解析评论正文，抽取品种/处理法，补齐 K[C2] | 完成第一版（10 个品种行 + 4 个处理法行；honey 词表待细化；WCR 行待接入）|
| 4 | 前端运行时 `packages/flavor-data/src/product-vector-v1`，纯 JS 推荐与归因引擎 | 引擎完成（`infer()`：V_pred / V_user / ΔV / V_target / 画像与豆款排序 / 语境证据基础），5 个引擎测试通过；页面与用户自建库（IndexedDB）未开始 |
| 5 | 产品级风味描述与用户用语对齐（owner 新要求）| 未开始：用已批准的 GACTT 消费者描述建立「消费者用语 → 12 维」词表，画像命名与归因文案都从它取词 |

**仍待 owner：** 16 个画像的命名与标杆豆款；α（默认 0.5）；WCR / UC Davis / Coffee Ad Astra 三份材料的具体文件（按逐一审阅规则由 owner 提供）。

---

## 11. 补充数据源（按「逐一审阅后批准」规则，未取数）

| 来源 | 用途 | 状态 |
|---|---|---|
| WCR Varieties Catalog | K[C2_variety] 的 sensory potential；品种词表；标杆豆款的品种依据 | **批准（R3-D7）**；等 owner 提供文件 |
| UC Davis Coffee Center（研磨度–水温–萃取率–感官图谱）| K[C0] 的萃取机理句证据，`LITERATURE_CLAIM` | **批准（R3-D7）**；等 owner 提供文件 |
| Coffee Ad Astra（Gagné：EY% / TDS 与风味强度）| 归因里的萃取解释，`LITERATURE_CLAIM` | **批准（R3-D7）**；等 owner 提供文件 |
| CoffeeReview Body/Acidity 打分列 | 已接入（R3-D6）| 完成 |
| GACTT（T2 消费者描述）| 消费者语言 → Q5–Q10 文案校准；fermented 轴用词 | 已批准，未接入 |
| Dryad B8993H（消费者偏好）| 校准层 | 已在 R1 |

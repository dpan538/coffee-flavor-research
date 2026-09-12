# 风味向量设计 V1 (Flavor Vector Design V1)

**Status:** ACTIVE — owner decisions R3-D5 (pivot), R3-D6 (dimension count, candidate-library path, structure axes) R3-D7 (confirmation: 0.6 : 1.0 structure weight, data sources, Steps 1–4) R3-D8 (profile names, α = 0.5, literature intake, bilingual presentation layer) and R3-D9 (coherence decision tree, 8-pick-5 feedback, Q6 escalation gate, consumer lexicon), 2026-09-12
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

### 3.1 问答流：相干性决策树（R3-D9）

六道感知题不再固定顺序全问，而是按 owner 的决策树动态分支（`packages/flavor-data/src/product-vector-v1/flow.ts`，`flowStep()`）。
槽位 Q0–Q5 到 Matrix_Q 六题的映射是操作员提案（`question_flow.slots`，`slot_mapping_owner_reviewed=false`）：
Q0 = 酸质、Q1 = 香气（基础对，两题移动最强的维度）；Q2 = 甜感、Q3 = 触感（校验）；Q4 = 苦感、Q5 = 复杂度（确认/修正）；Q6 = 8 词勾选强修正。

```
C0–C2 + Q0–Q1 → 问 Q2 → 相干度(Q0-Q1, Q2)
   ≥ 0.85 相干 → 问 Q3 → 相干度(Q0-Q1, Q2-Q3)
        相干  → 问 Q4（轻微确认）→ 相干度(Q0-Q2, Q3-Q4) 严重? → Path 4（后置突变，Q6 候选）: Path 1 交付
        轻微  → Path 2；严重 → Path 3
   0.65–0.85 轻微 → Path 2：问 Q3-Q4（修正）→ 问 Q5（确认）→ Q5 与 (0-1+3-4) 或 (2+3-4) 相干 → 交付；否则 Q6 候选
   < 0.65 严重   → Path 3：问 Q3、Q4-Q5（修正）→ Q4-5 与 0-1 或 2-3 相干 → 交付；均不相干 → Q6 候选
```

**相干度不在原始答案子向量上算。** 每个答案只动 1–2 个维度，两个内容一致但涉及不同维度的答案余弦为 0
（实测 Q0-Q1 对 Q2-Q3 的 81 种组合里 76 种 < 0.65）。引擎先把每组答案映射成「画像签名」——对 16 个画像质心的余弦向量——再取两组签名的余弦：
问的是「这些答案指向同一批画像吗」。校准（81 种组合）：最小 0.62、中位 0.73、p75 0.82、最大 0.98；按 owner 的阈值 0.85 / 0.65，
18 种相干、56 种轻微、7 种严重，即 **Path 2 会是常见路径**。若希望 Path 1 常见，阈值可调到 0.80 / 0.65 或 0.75 / 0.62（bundle 里一处改）。
示例：清亮花果（酸-A + 香-A）对花蜜甜（甜-A）0.77，对焦糖黑巧（甜-B）0.63；顺滑坚果（酸-C + 香-B）对焦糖黑巧 0.96，对花蜜甜 0.59。

### 3.2 交互闭环（R3-D9）

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
前三维、来源族构成、瑕疵均值，以及 owner 的命名与标杆豆款。

**命名怎么挂上去（R3-D8）**：owner 的 16 个命名写在 `PROFILE_NAME_ANCHORS.tsv`，每个名字带一个"锚点向量"（owner 陈述的质心特征）、
中英名、标杆豆款、3–4 个极简标签。构建时每个锚点按余弦挂到最相似的质心（一对一贪心，阈值 0.6），所以重建后名字不会错位。
本次结果：15 个 owner 锚点挂上（相似度 0.83–0.99）；`anchor-08 高拔明亮清冽酸质` 没有归宿（那个质心在 0.6 权重后消散，最佳 0.79，
保留在锚点表里等空间变化）；983 杯的「sweetness .72, fruity .54」画像 owner 未命名，操作员提案 `anchor-17 蜂蜜甜果与杏桃 / Honeyed Sweet Fruit`，
`owner_reviewed=false`，等确认或改名。

| 成员 | 质心前三维 | owner 命名 (zh / en) | 标杆豆款 | 极简标签 (zh-CN) |
|---|---|---|---|---|
| 1,343 | fruity .79, acidity .42, sweetness .40 | 熟果与黄桃甜感 / Tropical Stone Fruit | 哥伦比亚 厌氧日晒 / 埃塞 日晒 G1 | 黄桃｜熟果｜蔗糖｜柑橘 |
| 1,169 | nutty_chocolate .61, fruity .57, acidity .39 | 榛果巧克力与红莓 / Nutty Cocoa & Berry | 危地马拉 安提瓜水洗 | 榛果｜可可｜红莓｜柑橘 |
| 983 | sweetness .72, fruity .54, acidity .32 | **蜂蜜甜果与杏桃 / Honeyed Sweet Fruit（操作员提案，待确认）** | 埃塞 西达摩 水洗 / 哥伦比亚 蜜处理 | 蜂蜜｜杏桃｜甜橙｜柔和 |
| 757 | nutty_chocolate .88, body .28, bitter_roasted .25 | 经典黑巧与烤榛果 / Dark Chocolate & Roasted Nut | 哥伦比亚 惠兰水洗 | 黑巧克力｜烤榛果｜红糖｜醇厚 |
| 720 | nutty_chocolate .61, woody_earthy .54, bitter_roasted .38 | 深烘烤雪松与松露 / Roasted Cedar & Earth | 苏门答腊 湿剥曼特宁 | 雪松｜松露｜黑巧克力｜烟熏 |
| 639 | fruity .71, acidity .64, body .25 | 鲜明柑橘与柚子酸质 / Bright Citrus & Yuzu Acid | 肯尼亚 AA | 柚子｜柑橘｜黑加仑｜明亮 |
| 606 | sweetness .90, nutty_chocolate .24, body .23 | 蔗糖与纯净高甜 / Pure Cane Sweetness | 巴西 黄波本 | 蔗糖｜蜂蜜｜焦糖｜柔和 |
| 592 | fruity .60, woody_earthy .55, acidity .40 | 野生黑加仑与树莓 / Wild Forest Berry | 埃塞 哈拉尔 | 黑加仑｜树莓｜木质｜红酒 |
| 387 | floral .72, acidity .37, fruity .33 | 高锐茉莉花与白花 / Delicate Jasmine & Floral | 耶加雪菲水洗 / 瑰夏 | 茉莉花｜白花｜佛手柑｜水蜜桃 |
| 325 | woody_earthy .86, bitter_roasted .36, sweetness .22 | 泥炭烟熏与风干木 / Smoky Peat & Aged Wood | 爪哇 老深烘 | 烟熏｜泥炭｜风干木｜烟草 |
| 273 | spice .75, acidity .31, fruity .29 | 异域小豆蔻与肉桂 / Cardamom & Sweet Spice | 也门 摩卡 | 小豆蔻｜肉桂｜红糖｜葡萄干 |
| 217 | bitter_roasted .87, nutty_chocolate .26, body .22 | 深烘重可可与回甘 / Deep Dark Cocoa Roast | 意式拼配 深烘 | 重可可｜焦糖｜烘烤｜回甘 |
| 60 | fermented_winey .65, acidity .52, nutty_chocolate .48 | 厌氧朗姆与微醺酒香 / Anaerobic Rum & Winey | 洪都拉斯 雪莉桶 / 厌氧日晒瑰夏 | 厌氧朗姆｜酒香｜热带水果｜发酵 |
| 47 | herbal_green .77, acidity .36, fruity .34 | 清脆草本与绿茶香 / Fresh Herbal & Green Tea | 巴拿马 浅烘铁皮卡 | 茉莉绿茶｜柠檬草｜青苹果｜清脆 |
| 12 | defect .99 | 瑕疵预警风味 / Off-Flavor / Defect Group | （负向约束集合，不推荐）| 瑕疵｜霉味｜纸味｜陈味 |
| 12 | body .91, acidity .36 | 丝绒醇厚与糖浆感 / Full Velvet Body | 巴西 半日晒 | 丝绒｜糖浆｜奶油｜醇厚 |

0.6 权重与「≥1 描述词」规则之后，结构打分主导的假画像消失（首版的 550 + 334 杯降到 12 杯）。

---

## 6. 表达层：一个向量后端，两种语言（R3-D8）

后端只收敛向量；风味词是前端表达层。zh-CN 渲染中国精品咖啡圈的「极简风味词阵列」（词 A｜词 B｜词 C｜词 D），en 渲染科学化的叙述；
长解释收进「科学归因」折叠层。数据与规则都在 bundle 的 `presentation` 里，引擎函数 `displayTags()` / `statementsFor()` / `present()`。

**6.1 标签选择（owner 规则）**

| 优先级 | 条件 | 做法 |
|---|---|---|
| 1 实体级 | 候选带规范概念 id（用户录入的豆子、标杆豆款）| 按概念投影向量与该向量的点积降序，取前 3–4 个具体名词（茉莉花｜水蜜桃｜佛手柑｜青柠）|
| 2 维度级 | 只有向量（画像质心、用户未细化）| 权重 > 0.15 的主导维度，映射到维度级中国词库，每维取列表里第一个未用过的词；不暴露抽象维度名 |
| defect 守卫 | 任何情况 | defect 词只在 defect ≥ 0.5（瑕疵预警卡）时出现；常规卡强制过滤 |

**6.2 词库** `CONCEPT_FLAVOR_TAGS.tsv`（规范基底）+ `CN_CONSUMER_FLAVOR_LEXICON.tsv`（消费端泛化，R3-D9 种子 29 条：桂花、栀子花、荔枝、杨梅、
冰糖雪梨、太妃糖、高山龙井、鸭屎香、米酒、酒酿、烤杏仁、黑芝麻……各挂主维度与可选规范概念；Step 5 用 GACTT 与社媒语料扩充）。
维度级取词顺序：owner 的 `DIMENSION_TAG_MAP_CN` 列表在前，消费端词在后。`CONCEPT_FLAVOR_TAGS.tsv`：12 个维度各一组中国本土词（owner 的 `DIMENSION_TAG_MAP_CN`：acidity → 清冽果酸｜明亮酸质｜柑橘酸；
fruity → 水蜜桃｜黄桃｜黑加仑｜杏桃；fermented_winey → 厌氧酒香｜朗姆酒｜发酵果酱 …）+ 94 个规范概念各一个中/英极简词
（按 owner 规则：stone fruit → 黄桃/杏桃，brown sugar → 红糖/蔗糖，winey → 厌氧酒香/朗姆，citrus → 柑橘/柚子，floral → 茉莉花/咖啡花）。
概念行仍是操作员草案（`owner_reviewed=false`）。

**6.3 科学归因句** `CONTEXT_STATEMENTS.tsv`（owner 的统一 schema）：`context_id`（语境组合键，如 `C0_V60__C1_LIGHT`）、`context_parts`、
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
- 一段前端代码：加权求和 + 余弦 + top-k + 表达层（`displayTags` / `present`，locale = zh-CN | en）；用户自建库存本地（IndexedDB），匹配离线完成。
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
| 画像库 | 16 个画像，15 个挂上 owner 命名与标杆豆款；1 个操作员提案待确认 | §5.3 |
| Matrix_Q | 完成（owner 给定）| §3 |
| Matrix_K | C0×C1 可算未算；C2 缺数据 | §2 |
| 比较/校准 | 公式定稿；α = 0.5（R3-D8，不再微调）；结构轴权重 0.6 | §4 / §5.3 |
| 表达层 | 完成：词库（12 维列表 + 94 概念 + 29 条消费端词）、27 条归因句、双语 `present()` | §6 |
| 问答流 | 完成：相干性决策树（画像签名空间）、3+5 描述、8 选 5、升阶门控、Q6 强修正；17 个测试 | §3.1 / §3.2 |
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

**仍待 owner：** Q0–Q5 槽位到六题的映射；相干阈值是否按校准调整（0.85/0.65 → Path 2 常见）；94 个概念级极简词过目；WCR / UC Davis / Coffee Ad Astra 的 `*.claims.csv` 放入 `db/data/external-literature/`（README 有列定义），
`ingest-external-literature.py` 会把它们并入归因句表。

---

## 11. 补充数据源（按「逐一审阅后批准」规则，未取数）

| 来源 | 用途 | 状态 |
|---|---|---|
| WCR Varieties Catalog | K[C2_variety] 的 sensory potential；品种词表；标杆豆款的品种依据 | **批准（R3-D7）**；接入口 `db/data/external-literature/<source_id>.claims.csv` |
| UC Davis Coffee Center（研磨度–水温–萃取率–感官图谱）| K[C0] 的萃取机理句证据，`LITERATURE_CLAIM` | **批准（R3-D7）**；同上 |
| Coffee Ad Astra（Gagné：EY% / TDS 与风味强度）| 归因里的萃取解释，`LITERATURE_CLAIM` | **批准（R3-D7）**；同上 |
| CoffeeReview Body/Acidity 打分列 | 已接入（R3-D6）| 完成 |
| GACTT（T2 消费者描述）| 消费者语言 → Q5–Q10 文案校准；fermented 轴用词 | 已批准，未接入 |
| Dryad B8993H（消费者偏好）| 校准层 | 已在 R1 |

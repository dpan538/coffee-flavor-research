# flavorwords 前端文案总表（审核稿）

自动导出自 `product-vector-v1.json`（product-vector-v1）与组件内固定文案。每一行都是用户会在屏幕上看到的字。修改后请告诉我改哪一行，我改源头再重新导出。

## 1. 界面固定文案（组件与 view.ts）

### 首页 Hero（view.ts appShell）

| 位置 | 中文 | English |
|---|---|---|
| 标题 | 感官归因与风味诊断 | Sensory attribution & flavor diagnosis |
| 副标题 | 感官物理学 × 12 维向量空间 | Sensory physics × a 12-dimension vector space |
| 导言 | 描述直觉里的这一口，看它在物理上为什么这样。 | Describe the sip as you feel it; see why the cup tastes that way. |
| 开始按钮 | 开始风味诊断 | Start the diagnosis |
| About 按钮 aria | 关于 | About |
| 语言切换 | EN | 中 |
| 离线标记 title | 离线可用 | Works offline |

### 语境卡 ContextSetupCard

| 位置 | 中文 | English |
|---|---|---|
| 小标签 | 这杯咖啡 | This cup |
| C0 标题 | 怎么冲的？ | How was it brewed? |
| C1 标题 | 烘焙度 | Roast level |
| C2 标题 | 豆种 | Variety |
| 处理法标题 | 处理法 | Processing |
| 产地标题 | 产地（可选） | Origin (optional) |
| 产地提示 | 跳过也没关系：豆种和处理法已经决定了大部分预测 | Skip if unsure: variety and processing already carry most of the prediction |
| 单品 / 拼配切换 | 单品 SOE ｜ 拼配 Blend ≤ 3 | Single origin ｜ Blend ≤ 3 |
| 下一步 / 跳过 | 下一步 ｜ 跳过 | Next ｜ Skip |
| C0 选项 | 手冲 (V60) ｜ 法压 ｜ 意式浓缩 ｜ 冷萃 | Pour-over (V60) ｜ French press ｜ Espresso ｜ Cold brew |
| C1 选项 | 极浅烘 ｜ 浅烘 ｜ 中浅烘 ｜ 中烘 ｜ 中深烘 ｜ 深烘 ｜ 极深烘 | Very light ｜ Light ｜ Medium-light ｜ Medium ｜ Medium-dark ｜ Dark ｜ Very dark |
| C2 豆种选项 | 波本 Bourbon ｜ 卡斯蒂略 Castillo ｜ 卡杜艾 Catuai ｜ 卡杜拉 Caturra ｜ 埃塞原生种 Heirloom ｜ 瑰夏 Gesha ｜ 帕卡马拉 Pacamara ｜ 罗布斯塔 Robusta ｜ SL28 / SL34 ｜ 铁皮卡 Typica | Bourbon ｜ Castillo ｜ Catuai ｜ Caturra ｜ Ethiopian landrace ｜ Gesha ｜ Pacamara ｜ Robusta ｜ SL28 / SL34 ｜ Typica |
| 处理法选项 | 水洗 ｜ 日晒 ｜ 厌氧发酵 ｜ 低因 | Washed ｜ Natural ｜ Anaerobic ｜ Decaf |

### 题卡 QuizCard

| 位置 | 中文 | English |
|---|---|---|
| 小标签 | 这一口 | This sip |

### 第一次出卡 FirstDescriptionCard

| 位置 | 中文 | English |
|---|---|---|
| 提交按钮 | 生成我的风味卡 | Make my card |

### Q6 EscalationModal

| 位置 | 中文 | English |
|---|---|---|
| 小标签 | 再确认一次 | One more check |
| 标题 | 再确认一次：勾选你确实尝到的 | One more check: tick what you actually tasted |
| 提交按钮 | 生成精修风味卡 | Refine my card |

### 终卡 FinalAttributionCard

| 位置 | 中文 | English |
|---|---|---|
| 精修标记 | 精修 | refined |
| 底部 icon aria | 首页 ｜ 重新体验 ｜ 分享 | Home ｜ Start over ｜ Share |

### 上方堆叠 CollectedStack

| 位置 | 中文 | English |
|---|---|---|
| 勾选卡标题 | 你的 5 个词 | Your 5 words |
| 收集中 aria | 收集中 | collecting |

### About 抽屉 AboutDrawer

| 位置 | 中文 | English |
|---|---|---|
| 关闭 aria | 关闭 | Close |
| 展开 / 收起 | 展开 ｜ 收起 | Details ｜ Collapse |
| 数据流标题 | 数据从哪来，变成了什么 | Where the data came from, what it became |
| 数据流注 | 左：来源评审族与咖啡数；右：12 个维度；带宽是该来源在该维度上的质量 | left: source panels and their coffees; right: the 12 dimensions; ribbon width is that source's mass on that dimension |
| 光谱标题 | 十六个风味画像 | Sixteen flavor profiles |
| 光谱注 | 每一道射线是一个画像，长度按咖啡数的对数刻度，刻度色是它在各维度上的重心 | each ray is a profile, length on a log scale of its coffees, tick colours its weight across the dimensions |
| 证据链标题 | 证据链 | Evidence chain |
| 证据链行前缀 | 给引擎的是 | gives the engine |
| 来源族名 | CoffeeReview 编辑评审 ｜ Cup of Excellence 评审 ｜ Q-grader 储藏实验 ｜ Q-grader 数据集 ｜ 罗布斯塔 Q-grader 评审 ｜ 其他评审 | CoffeeReview editorial reviews ｜ Cup of Excellence juries ｜ Q-grader storage panel ｜ Q-grader dataset ｜ Robusta Q-grader panel ｜ other panels |

## 2. 卡片标题与折叠层标签（bundle.presentation）

| 位置 | 中文 | English |
|---|---|---|
| 第一次出卡标题 | 风味描述预览 | Flavor preview |
| 终卡标题 | 风味描述 | Flavor description |
| 折叠层标题 | 科学归因 | Attribution |
| 引用前缀 | 引用自： | From:  |
| 证据级别标签 OWNER_STATEMENT | 烘焙与萃取成因 | Roast & extraction |
| 证据级别标签 CORPUS_MEASURED | 语料实测 | Measured in the corpus |
| 证据级别标签 LITERATURE_CLAIM | 物理萃取规律 | Extraction physics |
| 证据级别标签 LITERATURE_CLAIM_PENDING_LOCATOR | 物理萃取规律 | Extraction physics |
| 证据级别标签 COMPUTED_DELTA | 感官偏置校准 | Perception calibration |
| 偏置句模板 pos | 在当前的感知中，{label}的表达比理论物理值更显突出，可能受萃取温度或降温速率的影响。 | In this cup, {label} reads more pronounced than the physics predicts; water temperature or cooling rate may be pushing it forward. |
| 偏置句模板 neg | 在当前的感知中，{label}的表达比理论物理值稍显收敛，可能受降温速率或水温偏置影响。 | In this cup, {label} reads a little more restrained than the physics predicts; cooling rate or water temperature may be holding it back. |
| 勾选提示（describe） | 请勾选出你觉得最符合你当前体验的 5 个风味描述 | Pick the 5 words that best match what you tasted |

## 3. 题库 Q0–Q5（bundle.question_bank）

| 题 | 位置 | 中文 | English |
|---|---|---|---|
| Q0 | 提问 | 喝到酸了吗？是哪一种？ | Any acidity? Which kind? |
| Q0 | 选项 A | 鲜明多汁的柑橘 / 青苹果酸 | Bright & juicy citrus / green-apple acidity |
| Q0 | 选项 B | 柔和温和的乳酸 / 发酵果酸（像酸奶、水果黄酒） | Soft lactic / fermented fruit acidity (like yoghurt) |
| Q0 | 选项 C | 平顺无酸 / 低酸度（口感顺滑平衡） | Smooth & low acidity (balanced, easy to drink) |
| Q1 | 提问 | 闻起来最像什么？ | What does it smell like? |
| Q1 | 选项 A | 花香、茶感、草本 | floral, tea-like, herbal |
| Q1 | 选项 B | 坚果、烤面包、烤榛果 | nuts, toast, roasted hazelnut |
| Q1 | 选项 C | 热带水果，带一点微醺酒香 | tropical fruit with a boozy edge |
| Q2 | 提问 | 能喝出甜味吗？更像哪一种？ | Do you taste sweetness? Which kind? |
| Q2 | 选项 A | 清爽的花蜜 / 蔗糖甜 | light nectar or cane-sugar sweetness |
| Q2 | 选项 B | 浓郁的焦糖 / 黑巧克力 | rich caramel or dark chocolate |
| Q2 | 选项 C | 熟果、果酱那种浓稠的甜 | ripe-fruit, jammy sweetness |
| Q3 | 提问 | 口感如何？ | How does it feel in the mouth? |
| Q3 | 选项 A | 清爽，像绿茶或果汁 | light, like green tea or juice |
| Q3 | 选项 B | 顺滑，像牛奶或丝绒 | smooth, like milk or velvet |
| Q3 | 选项 C | 厚重，像黑巧或糖浆 | heavy, like dark chocolate or syrup |
| Q4 | 提问 | 尾段苦吗？ | Bitter at the end? |
| Q4 | 选项 A | 有一点苦，但像黑巧一样回甘 | a little, but it turns sweet like dark chocolate |
| Q4 | 选项 B | 完全不苦 | none at all |
| Q5 | 提问 | 整体更像哪种？ | Overall, which is closer? |
| Q5 | 选项 A | 层次分明，很干净 | clear layers, very clean |
| Q5 | 选项 B | 风味交融，浓郁复杂 | flavours blend together, rich and complex |

## 4. 十六个风味画像（终卡标题与标签）

| 中文名 | English | 标签 zh | tags en | 标杆豆款 | 咖啡数 |
|---|---|---|---|---|---|
| 熟果与黄桃甜感 | Tropical Stone Fruit | 黄桃 ｜ 熟果 ｜ 蔗糖 ｜ 柑橘 | yellow peach ｜ ripe fruit ｜ cane sugar ｜ citrus | 哥伦比亚 厌氧日晒 / 埃塞俄比亚 日晒 G1 | 1343 |
| 榛果巧克力与红莓 | Nutty Cocoa & Berry | 榛果 ｜ 可可 ｜ 红莓 ｜ 柑橘 | hazelnut ｜ cocoa ｜ red berry ｜ citrus | 危地马拉 安提瓜水洗 (Guatemala Antigua) | 1169 |
| 蜂蜜甜果与杏桃 | Honeyed Sweet Fruit & Apricot | 蜂蜜 ｜ 杏桃 ｜ 甜橙 ｜ 柔和 | honey ｜ apricot ｜ sweet orange ｜ smooth | 埃塞俄比亚 西达摩 水洗 / 哥伦比亚 蜜处理 | 983 |
| 经典黑巧与烤榛果 | Dark Chocolate & Roasted Nut | 黑巧克力 ｜ 烤榛果 ｜ 红糖 ｜ 醇厚 | dark chocolate ｜ roasted hazelnut ｜ brown sugar ｜ full body | 哥伦比亚 惠兰水洗 (Colombia Huila) | 757 |
| 深烘烤雪松与松露 | Roasted Cedar & Earth | 雪松 ｜ 松露 ｜ 黑巧克力 ｜ 烟熏 | cedar ｜ truffle ｜ dark chocolate ｜ smoke | 苏门答腊 湿剥曼特宁 (Sumatra Mandheling PWN) | 720 |
| 鲜明柑橘与柚子酸质 | Bright Citrus & Yuzu Acid | 柚子 ｜ 柑橘 ｜ 黑加仑 ｜ 明亮 | yuzu ｜ citrus ｜ blackcurrant ｜ bright | 肯尼亚 AA (Kenya AA SL28/SL34) | 639 |
| 蔗糖与纯净高甜 | Pure Cane Sweetness | 蔗糖 ｜ 蜂蜜 ｜ 焦糖 ｜ 柔和 | cane sugar ｜ honey ｜ caramel ｜ smooth | 巴西 黄波本 (Brazil Yellow Bourbon) | 606 |
| 野生黑加仑与树莓 | Wild Forest Berry | 黑加仑 ｜ 树莓 ｜ 木质 ｜ 红酒 | blackcurrant ｜ raspberry ｜ woody ｜ red wine | 埃塞俄比亚 哈拉尔 (Ethiopia Harrar) | 592 |
| 高锐茉莉花与白花 | Delicate Jasmine & Floral | 茉莉花 ｜ 白花 ｜ 佛手柑 ｜ 水蜜桃 | jasmine ｜ white flowers ｜ bergamot ｜ peach | 埃塞俄比亚 耶加雪菲水洗 / 瑰夏 (Geisha) | 387 |
| 泥炭烟熏与风干木 | Smoky Peat & Aged Wood | 烟熏 ｜ 泥炭 ｜ 风干木 ｜ 烟草 | smoke ｜ peat ｜ aged wood ｜ tobacco | 爪哇 老深烘 (Java Arabica / Old Brown) | 325 |
| 异域小豆蔻与肉桂 | Cardamom & Sweet Spice | 小豆蔻 ｜ 肉桂 ｜ 红糖 ｜ 葡萄干 | cardamom ｜ cinnamon ｜ brown sugar ｜ raisin | 也门 摩卡 (Yemen Matari) | 273 |
| 深烘重可可与回甘 | Deep Dark Cocoa Roast | 重可可 ｜ 焦糖 ｜ 烘烤 ｜ 回甘 | dark cocoa ｜ caramel ｜ roast ｜ lingering sweet | 意式拼配 深烘 (Italian Dark Roast Blend) | 217 |
| 厌氧朗姆与微醺酒香 | Anaerobic Rum & Winey | 厌氧朗姆 ｜ 酒香 ｜ 热带水果 ｜ 发酵 | anaerobic rum ｜ winey ｜ tropical fruit ｜ fermented | 洪都拉斯 威士忌雪莉桶 / 厌氧日晒瑰夏 | 60 |
| 清脆草本与绿茶香 | Fresh Herbal & Green Tea | 茉莉绿茶 ｜ 柠檬草 ｜ 青苹果 ｜ 清脆 | jasmine green tea ｜ lemongrass ｜ green apple ｜ crisp | 巴拿马 浅烘铁皮卡 (Panama Typica) | 47 |
| 瑕疵预警风味 | Off-Flavor / Defect Group | 瑕疵 ｜ 霉味 ｜ 纸味 ｜ 陈味 | defect ｜ musty ｜ papery ｜ stale | （负向约束集合，不推荐商品） | 12 |
| 丝绒醇厚与糖浆感 | Full Velvet Body | 丝绒 ｜ 糖浆 ｜ 奶油 ｜ 醇厚 | velvet ｜ syrup ｜ cream ｜ full body | 巴西 半日晒 / 罗布斯塔精选 (Brazil Pulped Natural) | 12 |

## 5. 维度词（描述与勾选时按维度取的词）

| 维度 | 标签 zh | label en | 维度词 zh | words en | 消费端补充 zh | consumer en |
|---|---|---|---|---|---|---|
| acidity | 酸质 | acidity | 清冽果酸 ｜ 明亮酸质 ｜ 柑橘酸 | crisp acidity ｜ bright acidity ｜ citric |  | citrus ｜ juicy ｜ tart ｜ crisp ｜ citrusy ｜ tangy ｜ lemony |
| sweetness | 甜感 | sweetness | 高甜感 ｜ 蔗糖甜 ｜ 蜂蜜感 | high sweetness ｜ cane sugar ｜ honeyed | 冰糖雪梨 ｜ 太妃糖 ｜ 麦芽糖 ｜ 黑糖 ｜ 罗汉果甜 | rock-sugar pear ｜ toffee ｜ maltose ｜ dark brown sugar ｜ monk-fruit sweetness ｜ jam ｜ candy ｜ syrup ｜ jammy |
| body | 醇厚度 | body | 丝绒感 ｜ 醇厚 ｜ 圆润口感 | velvety ｜ full body ｜ round mouthfeel |  | silky |
| floral | 花香 | floral | 茉莉花 ｜ 玉兰花 ｜ 白花 | jasmine ｜ magnolia ｜ white flowers | 桂花 ｜ 栀子花 ｜ 咖啡花 ｜ 白兰花 ｜ 洋甘菊 | osmanthus ｜ gardenia ｜ coffee blossom ｜ white magnolia ｜ chamomile ｜ floral ｜ tea-like |
| fruity | 果香 | fruity | 水蜜桃 ｜ 黄桃 ｜ 黑加仑 ｜ 杏桃 | peach ｜ yellow peach ｜ blackcurrant ｜ apricot | 巨峰葡萄 ｜ 荔枝 ｜ 杨梅 ｜ 西梅 ｜ 青梅 ｜ 红心芭乐 | Kyoho grape ｜ lychee ｜ bayberry ｜ prune ｜ green plum ｜ pink guava ｜ berry ｜ berries ｜ stone fruit ｜ tropical ｜ melon |
| nutty_chocolate | 坚果巧克力 | nutty & chocolate | 烤榛果 ｜ 黑莓可可 ｜ 提拉米苏 | roasted hazelnut ｜ berry cocoa ｜ tiramisu |  | chocolate |
| fermented_winey | 厌氧酒香 | fermented & winey | 厌氧酒香 ｜ 朗姆酒 ｜ 发酵果酱 | anaerobic winey ｜ rum ｜ fermented jam | 米酒 ｜ 酒酿 ｜ 酒酿圆子 ｜ 黄酒 ｜ 热带水果发酵酱 ｜ 水果黄酒 ｜ 微醺朗姆 ｜ 微醺 ｜ 威士忌桶 ｜ 雪莉桶 ｜ 野果发酵 ｜ 微醺酒香 ｜ 厌氧风味 ｜ 苹果酒感 ｜ 水果发酵酱 ｜ 朗姆酒香 | rice wine ｜ jiuniang (sweet fermented rice) ｜ jiuniang rice balls ｜ huangjiu ｜ tropical fruit ferment ｜ fruit huangjiu ｜ tipsy rum ｜ tipsy ｜ whisky barrel ｜ sherry cask ｜ funky ｜ wine ｜ funk ｜ cider ｜ fermented ｜ winey |
| bitter_roasted | 烘烤苦感 | roast & bitter | 黑巧回甘 ｜ 烟熏可可 ｜ 重烘焙香 | dark chocolate finish ｜ smoky cocoa ｜ deep roast | 烤杏仁 ｜ 烘焙麦芽 ｜ 黑芝麻 ｜ 松露巧克力 | roasted almond ｜ roasted malt ｜ black sesame ｜ truffle chocolate ｜ smokey ｜ roasted ｜ dark roast ｜ ashy |
| spice | 香料 | spice | 小豆蔻 ｜ 肉桂 ｜ 异域辛香 | cardamom ｜ cinnamon ｜ exotic spice |  |  |
| herbal_green | 草本绿茶 | herbal & green | 茉莉绿茶 ｜ 高山乌龙 ｜ 草本清香 | jasmine green tea ｜ high-mountain oolong ｜ fresh herbal | 高山龙井 ｜ 武夷岩茶 ｜ 鸭屎香 ｜ 普洱茶韵 | high-mountain Longjing ｜ Wuyi rock tea ｜ Ya Shi Xiang (Dancong) ｜ Pu'er tea finish ｜ tea ｜ grass ｜ grassy ｜ herbal |
| woody_earthy | 木质泥土 | woody & earthy | 风干雪松 ｜ 泥炭木质 ｜ 松露 | aged cedar ｜ peaty wood ｜ truffle |  |  |
| defect | 瑕疵 | defect | 风味瑕疵 ｜ 过发酵味 | off-flavor ｜ over-fermented |  |  |

## 6. 94 个规范概念的极简词（用户录入豆子时上卡）

| 概念 | 中文 | English |
|---|---|---|
| acetic_vinegar | 醋酸 | vinegar |
| alcoholic | 酒精感 | boozy |
| almond | 杏仁 | almond |
| anise | 八角 | anise |
| apple | 苹果 | apple |
| ash | 灰烬 | ash |
| astringent | 涩感 | astringent |
| baked_bread | 烤面包 | baked bread |
| banana | 香蕉 | banana |
| bell_pepper | 青椒 | bell pepper |
| bergamot | 佛手柑 | bergamot |
| bitter | 苦 | bitter |
| black_pepper | 黑胡椒 | black pepper |
| black_tea | 红茶 | black tea |
| blackberry | 黑莓 | blackberry |
| blackcurrant | 黑加仑 | blackcurrant |
| blueberry | 蓝莓 | blueberry |
| brown_sugar | 红糖 | brown sugar |
| burnt | 焦苦 | burnt |
| butter | 黄油 | butter |
| caramel | 焦糖 | caramel |
| cardamom | 小豆蔻 | cardamom |
| cardboard | 纸板味 | cardboard |
| cedar | 雪松 | cedar |
| cereal_grain | 谷物 | grain |
| chamomile | 洋甘菊 | chamomile |
| cherry | 车厘子 | cherry |
| cinnamon | 肉桂 | cinnamon |
| clove | 丁香 | clove |
| cocoa | 可可 | cocoa |
| coconut | 椰子 | coconut |
| creamy_mouthfeel | 奶油质地 | creamy |
| dark_chocolate | 黑巧克力 | dark chocolate |
| drying | 干涩 | drying |
| dusty | 灰尘味 | dusty |
| earthy | 泥土 | earthy |
| eucalyptus | 尤加利 | eucalyptus |
| fermented_character | 发酵感 | fermented |
| fresh_grass | 青草 | fresh grass |
| fullness | 饱满 | full |
| ginger | 姜 | ginger |
| grape | 葡萄 | grape |
| grapefruit | 西柚 | grapefruit |
| green_tea | 绿茶 | green tea |
| green_vegetal | 青蔬 | vegetal |
| hay | 干草 | hay |
| hazelnut | 榛果 | hazelnut |
| honey | 蜂蜜 | honey |
| jasmine | 茉莉花 | jasmine |
| leather | 皮革 | leather |
| lemon | 柠檬 | lemon |
| lemongrass | 柠檬草 | lemongrass |
| lime | 青柠 | lime |
| malt | 麦芽 | malt |
| mango | 芒果 | mango |
| metallic | 金属味 | metallic |
| mint | 薄荷 | mint |
| molasses | 黑糖 | molasses |
| moldy | 霉变 | moldy |
| mouth_coating | 挂口 | coating |
| mushroom | 蘑菇 | mushroom |
| musty | 霉味 | musty |
| nutmeg | 肉豆蔻 | nutmeg |
| orange | 甜橙 | orange |
| orange_blossom | 橙花 | orange blossom |
| paper | 纸味 | papery |
| pea_pod | 豌豆荚 | pea pod |
| peach | 水蜜桃 | peach |
| peanut | 花生 | peanut |
| pear | 梨 | pear |
| pineapple | 菠萝 | pineapple |
| pink_grapefruit | 红心西柚 | pink grapefruit |
| plum | 李子 | plum |
| pomegranate | 石榴 | pomegranate |
| prune | 西梅 | prune |
| raisin | 葡萄干 | raisin |
| raspberry | 树莓 | raspberry |
| roasted_character | 烘烤 | roasty |
| rose | 玫瑰 | rose |
| rubber | 橡胶味 | rubbery |
| salty | 咸 | salty |
| smoky | 烟熏 | smoky |
| smooth_mouthfeel | 顺滑 | smooth |
| sour | 尖酸 | sour |
| stale | 陈味 | stale |
| strawberry | 草莓 | strawberry |
| sweet | 甜 | sweet |
| syrupy_mouthfeel | 糖浆感 | syrupy |
| toast | 吐司 | toast |
| tobacco | 烟草 | tobacco |
| vanilla | 香草 | vanilla |
| walnut | 核桃 | walnut |
| wine_like_character | 红酒 | winey |
| woody | 木质 | woody |

## 7. 科学归因句（折叠层里的成因句）

| 语境 | 标签 | 中文 | English | 出处 |
|---|---|---|---|---|
| C0_ESPRESSO | 烘焙与萃取成因 | 意式浓缩放大醇厚度与油脂，前段高挥发花果香被压缩。 | Espresso amplifies body and oils; the volatile floral and fruit top notes are compressed. | owner |
| C0_COLD_BREW | 烘焙与萃取成因 | 冷萃抑制低挥发酸，酸质与花香偏弱，甜感与醇厚更突出。 | Cold brew suppresses the low-volatility acids: less acidity and floral lift, more sweetness and body. | owner |
| C0_V60 | 烘焙与萃取成因 | 手冲快萃优先释放前段高挥发花香与单体果酸。 | Pour-over releases the early, volatile floral and fruit acids first. | owner |
| C0_FRENCH_PRESS | 烘焙与萃取成因 | 浸泡式萃取带入更多油脂与细粉，醇厚度上升，干净度下降。 | Immersion brewing carries more oils and fines: more body, less clarity. | owner |
| C1_LIGHT | 烘焙与萃取成因 | 浅烘保留更多绿原酸与高挥发香气，酸质与花果香突出。 | Light roasts keep more chlorogenic acids and volatile aromatics: acidity and floral-fruit notes lead. | owner |
| C1_MEDIUM_LIGHT | 烘焙与萃取成因 | 中浅烘保留花果酸质，同时开始形成焦糖化甜感。 | Medium-light roasts keep the floral-fruit acidity while caramelisation sweetness begins. | owner |
| C1_MEDIUM | 烘焙与萃取成因 | 中烘平衡酸质与美拉德产物，坚果与焦糖增强。 | Medium roasts balance acidity against Maillard products: nut and caramel rise. | owner |
| C1_MEDIUM_DARK | 烘焙与萃取成因 | 中深烘美拉德产物占比高，醇厚度、巧克力与苦感上升，酸质下降。 | Medium-dark roasts are Maillard-dominated: body, chocolate and bitterness rise, acidity falls. | owner |
| C1_DARK | 烘焙与萃取成因 | 深烘绿原酸大量降解，焦糖苦与烟熏占主导。 | Dark roasts degrade most chlorogenic acids: caramelised bitterness and smoke dominate. | owner |
| C1_VERY_DARK | 烘焙与萃取成因 | 极深烘以碳化与烟熏为主，品种与产地特征基本被覆盖。 | Very dark roasts are carbonised and smoky; origin and variety character is mostly covered. | owner |
| C2_process_WASHED | 烘焙与萃取成因 | 水洗去胶质快，内源有机酸突出：干净度高、柑橘、花香、高酸。 | Washed processing removes mucilage quickly; the bean's own organic acids stand out: clean, citrus, floral, high acidity. | owner |
| C2_process_NATURAL | 烘焙与萃取成因 | 日晒让果肉糖分长时间发酵渗入豆内，还原糖与游离氨基酸升高：果酱、热带水果、高甜、波本感。 | Natural processing lets fruit sugars ferment into the seed: more reducing sugars and free amino acids — jam, tropical fruit, high sweetness. | owner |
| C2_process_ANAEROBIC | 烘焙与萃取成因 | 厌氧发酵产生大量乳酸与外源酯类：酸奶、厌氧酒香、极高识别度。 | Anaerobic fermentation produces lactic acid and exogenous esters: yoghurt, winey notes, very distinctive. | owner |
| C2_process_HONEY | 烘焙与萃取成因 | 蜜处理保留部分果胶发酵，甜感与醇厚介于水洗与日晒之间。 | Honey processing keeps part of the mucilage: sweetness and body between washed and natural. | owner |
| C2_process_DECAF | 烘焙与萃取成因 | 脱因工艺去除部分前体物质，香气强度整体下降。 | Decaffeination removes some precursors; aroma intensity drops overall. | owner |
| C2_variety_GESHA | 烘焙与萃取成因 | 瑰夏基因型花香与柑橘酸质上限极高，醇厚度偏轻。 | The Gesha genotype has a very high ceiling for floral and citrus acidity with a lighter body. | owner |
| C2_variety_BOURBON | 烘焙与萃取成因 | 波本甜感与平衡度好，焦糖与红果常见。 | Bourbon is sweet and balanced; caramel and red fruit are typical. | owner |
| C2_variety_SL28_SL34 | 烘焙与萃取成因 | SL28/SL34 以黑加仑与明亮柑橘酸质著称。 | SL28/SL34 are known for blackcurrant and bright citric acidity. | owner |
| C2_variety_ETHIOPIAN_LANDRACE | 烘焙与萃取成因 | 埃塞原生种以茉莉花、柑橘与蓝莓（日晒）为标志。 | Ethiopian landraces are marked by jasmine, citrus and, when natural, blueberry. | owner |
| C2_variety_TYPICA | 烘焙与萃取成因 | 铁皮卡干净、甜感柔和，醇厚适中。 | Typica is clean and gently sweet with moderate body. | owner |
| C2_variety_ROBUSTA | 烘焙与萃取成因 | 罗布斯塔前体糖分低、绿原酸与咖啡因高：苦感与醇厚重，花果弱。 | Robusta has low sugar precursors and high chlorogenic acid and caffeine: heavy bitterness and body, little floral-fruit. | owner |
| C0_V60__C1_LIGHT | 烘焙与萃取成因 | 浅烘焙保留了绿原酸与高挥发性花果香，V60 快萃优先释放了前段极性酸质。 | Light roast preserves volatile florals and fruit acids, and V60 fast extraction targets these front-end acids. | owner |
| C0_ESPRESSO__C1_MEDIUM_DARK | 烘焙与萃取成因 | 中深烘的美拉德产物在意式高压下被油脂放大：黑巧、焦糖与厚重口感主导，酸质退到后段。 | Medium-dark Maillard products are amplified by espresso pressure and oils: dark chocolate, caramel and weight lead; acidity retreats. | owner |
| C0_COLD_BREW__C1_LIGHT | 烘焙与萃取成因 | 冷萃压低了浅烘的低挥发酸，花香减弱、甜感与茶感更清晰。 | Cold brew flattens the light roast's low-volatility acids: less floral lift, clearer sweetness and tea-like body. | owner |
| C1_LIGHT__C2_process_WASHED | 烘焙与萃取成因 | 浅烘 + 水洗保留了柠檬酸与高极性酯类：柑橘、茉莉与干净的酸质。 | Light roast plus washed processing keeps citric acid and polar esters: citrus, jasmine and clean acidity. | owner |
| C1_LIGHT__C2_process_NATURAL | 烘焙与萃取成因 | 浅烘 + 日晒把发酵进豆内的果糖与酯类完整保留：蓝莓、果酱与高甜。 | Light roast plus natural processing keeps the fermented fruit sugars and esters: blueberry, jam and high sweetness. | owner |
| C1_MEDIUM_DARK__C2_process_ANAEROBIC | 烘焙与萃取成因 | 中深烘 + 厌氧本应呈现较强的黑巧与发酵感；若你尝到更高的酸质，通常是冲煮水温偏低使后段大分子苦酚萃取不足。 | Medium-dark plus anaerobic should read as dark chocolate and fermentation; a brighter acidity usually means the brew ran cool and under-extracted the late bitter phenolics. | owner |
| C1_VERY_LIGHT | 烘焙与萃取成因 | 极浅烘几乎不动豆子的原始结构：绿原酸与挥发性花果香保留最完整，酸质最锐利，甜感与醇厚尚未展开。 | A very light roast barely touches the bean's original structure: chlorogenic acids and volatile florals stay almost intact, acidity is at its sharpest, sweetness and body have not opened yet. | owner |
| C0_POUR_OVER_V60 | 物理萃取规律 | 粉床细粉迁移引发微观通道效应时，局部过萃会导致中段甜感中断，并在余韵中引入涩感与杂味。 | When fines migrate and open micro-channels in the bed, local over-extraction breaks the mid-palate sweetness and brings astringency and off-notes into the finish. | Coffee Ad Astra (Jonathan Gagné) |
| C0_POUR_OVER_V60__C1_LIGHT | 物理萃取规律 | 浅烘手冲时，萃取率落在合适区间才有饱满的中段甜感；萃取率不足则酸而空，过高则涩。 | For light roasts on pour-over, mid-palate sweetness fills in only inside the right extraction-yield window; under-extraction reads sour and hollow, over-extraction astringent. | Coffee Ad Astra (Jonathan Gagné) |
| C0_ESPRESSO__C1_MEDIUM_DARK | 物理萃取规律 | 中深烘意式在高压下通道效应更敏感：粉饼不均会同时出现欠萃的酸与过萃的苦。 | Medium-dark espresso is more sensitive to channeling under pressure: an uneven puck shows under-extracted sourness and over-extracted bitterness at once. | Coffee Ad Astra (Jonathan Gagné) |
| C0_POUR_OVER_V60 | 物理萃取规律 | 快萃与较高水温优先溶解极性较高的有机酸分子，前段酸质与花果香先被释放。 | Fast extraction at higher water temperature dissolves the more polar organic acids first, so acidity and floral-fruit notes lead. | UC Davis Coffee Center |
| C0_ESPRESSO | 物理萃取规律 | 研磨度过细会加速大分子绿原酸内酯的释放，从而增加尾段苦感；高压萃取同时带出更多油脂与醇厚度。 | Too fine a grind accelerates the release of large chlorogenic-acid lactones and adds late bitterness; pressure extraction also carries more oils and body. | UC Davis Coffee Center |
| C0_COLD_BREW | 物理萃取规律 | 低温长时萃取压低挥发酸与前段酸质，TDS 与感官图谱偏向甜感与圆润。 | Long, cold extraction suppresses volatile acids and front-end acidity; the TDS–sensory map shifts toward sweetness and roundness. | UC Davis Coffee Center |
| C0_FRENCH_PRESS | 物理萃取规律 | 浸泡式萃取与金属滤网让更多细粉与油脂进入杯中，醇厚度上升、干净度下降。 | Immersion brewing through a metal filter passes more fines and oils: more body, less clarity. | UC Davis Coffee Center |
| C2_variety_GESHA | 物理萃取规律 | 瑰夏（Gesha）基因决定了其高挥发性单萜烯（如芳樟醇）的高表达上限，浅烘焙下呈现高锐白花与单醇果酸。 | The Gesha genotype sets a high ceiling for volatile monoterpenes such as linalool; at light roast it reads as sharp white florals and clean, single-note fruit acidity. | World Coffee Research |
| C1_LIGHT | 物理萃取规律 | 浅烘保留品种的花香与果酸参照物（花香、柑橘酸、单醇甜感），焦糖化产物尚未主导。 | Light roasting keeps the variety's floral and fruit-acid references (florals, citric acidity, clean sweetness) before caramelisation products take over. | World Coffee Research |
| C1_MEDIUM | 物理萃取规律 | 中烘时焦糖化与美拉德参照物（红糖、坚果、可可）与残余果酸达到平衡。 | At medium roast the caramelisation and Maillard references (brown sugar, nut, cocoa) balance the remaining fruit acidity. | World Coffee Research |
| C1_DARK | 物理萃取规律 | 深烘下花香与果酸参照物被烘烤参照物（烟熏、焦糖苦、灰烬）覆盖。 | At dark roast the floral and fruit-acid references are covered by roast references (smoke, burnt caramel, ash). | World Coffee Research |

## 8. About（about.ts）

About 的正文（our approach、感官物理学与几何归因四段、证据链四条）见 `packages/flavor-data/src/product-vector-v1/about.ts`，中英并列；本表只列标题级文案：

| 位置 | 中文 | English |
|---|---|---|
| Eyebrow | Our approach | Our approach |
| 标题 | 把一口咖啡，还原成它的物理成因 | Trace a sip back to its physics |
| 作者 | 潘岱 · Dai Pan | Dai Pan · 潘岱 |
| 问题 1 | 包装上的风味词是营销写的，杯子里的味道是烘焙与萃取决定的，两者之间没有一座桥。 | The flavor words on a bag are written by marketing; the taste in the cup is decided by roast and extraction, and nothing bridges the two. |
| 问题 2 | 喝到了什么、为什么是这样、下一杯该往哪走——爱好者手边一直没有一件像样的工具。 | What did I taste, why, and where should the next cup go — the enthusiast never had a proper instrument for that. |
| 段 1 | flavorwords 是一间放在口袋里的感官实验室。它把一口咖啡的直觉描述投影成一个向量，拿它去对照烘焙与萃取的物理先验，再用精品咖啡圈真正在用的词把结果说回来。 | flavorwords is a sensory lab that fits in a pocket. It projects the intuitive description of a sip into a vector, holds it against the physical priors of the roast and the brew, and answers in the words the specialty scene actually uses. |
| 段 2 | 它不训练模型，不打分，不排名。它只做三件事：把 83,031 条专业感官记录压成一个 12 维空间，用几何而不是问卷去问，以及把每一句成因都注明出处。 | It trains no model, gives no score, ranks nothing. It does three things: compresses 83,031 professional sensory records into a 12-dimension space, asks with geometry instead of a questionnaire, and cites the source of every causal sentence. |
| 方法段标题 | 感官物理学与几何归因 | Sensory physics & geometric attribution |
| 方法段摘要 | 把风味拆成 12 个正交维度；用向量的语义搜索给决策树剪枝，而不是给咖啡打分排序。 | Flavor is split into 12 orthogonal dimensions; vector semantic search prunes the decision tree — it never ranks coffees. |
| 方法四小节标题 | 动态设计 ｜ 公式设计 ｜ 语义搜索，不是排序 ｜ 相干与极性 | Dynamic design ｜ Formula design ｜ Semantic search, not ranking ｜ Coherence and polarity |
| 数据标签 | 条专业感官断言 ｜ 杯经专业评审的咖啡 ｜ 条语义关系边 ｜ 位消费者的盲测笔记 | professional sensory assertions ｜ professionally reviewed coffees ｜ semantic relation edges ｜ consumers' blind-tasting notes |
| 证据链四条 | World Coffee Research (WCR) ｜ UC Davis Coffee Center ｜ Coffee Ad Astra (Dr. Christopher H. Gagné) ｜ Great American Coffee Taste Test (GACTT) | same |
| 证据链 gives | 规范概念的标准定义、品种的基因上限 ｜ 研磨、水温、TDS 如何先释放酸、后释放苦 ｜ 通道效应与萃取率如何决定中段甜与尾段涩 ｜ 4,042 位消费者真实用词的频次 | canonical definitions, the genetic ceiling of varieties ｜ how grind, temperature and TDS release acids first and bitterness last ｜ how channeling and extraction yield decide mid-palate sweetness and late astringency ｜ the real vocabulary of 4,042 consumers, by frequency |


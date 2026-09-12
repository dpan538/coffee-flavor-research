# flavorwords 前端文案总表（审核稿）

自动导出自 `product-vector-v1.json`（product-vector-v1）、`view.ts` / `about.ts`（经 esbuild 执行）与组件内固定文案。每一行都是用户会在屏幕上看到的字。修改后请告诉我改哪一行，我改源头再重新导出。

## 1. 首页与流程界面

### 首页 Hero（view.ts appShell）

| 位置 | 中文 | English |
|---|---|---|
| 标题 | 说清这一杯的风味 | Put this cup into words |
| 副标题 | 从酸质、香气与口感开始，找到贴近你感受的描述。 | Start from acidity, aroma and mouthfeel, and find the words closest to what you tasted. |
| 导言 | 几次选择之后，你会得到一张由你确认的风味卡，和几条帮助理解这杯咖啡的参考说明。 | A few choices lead to a flavor card you confirm yourself, with reference notes to help you understand the cup. |
| 开始按钮 | 开始描述 | Describe this cup |
| About 按钮 aria | 关于 | About |
| 语言切换 | EN | 中 |
| 离线标记 title | 离线可用 | Works offline |

### 语境卡（view.ts contextCatalog）

| 位置 | 中文 | English |
|---|---|---|
| c0_preparation 标题 | 怎么冲的？ | How was it brewed? |
| c0_preparation 选项 | 手冲 (V60) ｜ 法压 ｜ 意式浓缩 ｜ 冷萃 | Pour-over (V60) ｜ French press ｜ Espresso ｜ Cold brew |
| c1_roast 标题 | 烘焙度 | Roast level |
| c1_roast 选项 | 极浅烘 ｜ 浅烘 ｜ 中浅烘 ｜ 中烘 ｜ 中深烘 ｜ 深烘 ｜ 极深烘 | Very light ｜ Light ｜ Medium-light ｜ Medium ｜ Medium-dark ｜ Dark ｜ Very dark |
| c2_variety 标题 | 豆种 | Variety |
| c2_variety 单品 / 拼配 | 单品 SOE ｜ 拼配 Blend | Single origin ｜ Blend |
| c2_variety 选项 | 波本 Bourbon ｜ 卡斯蒂略 Castillo ｜ 卡杜艾 Catuai ｜ 卡杜拉 Caturra ｜ 埃塞原生种 Heirloom ｜ 瑰夏 Gesha ｜ 帕卡马拉 Pacamara ｜ 罗布斯塔 Robusta ｜ SL28 / SL34 ｜ 铁皮卡 Typica | Bourbon ｜ Castillo ｜ Catuai ｜ Caturra ｜ Ethiopian landrace ｜ Gesha ｜ Pacamara ｜ Robusta ｜ SL28 / SL34 ｜ Typica |
| c2_process 标题 | 处理法 | Processing |
| c2_process 选项 | 厌氧发酵 ｜ 低因 ｜ 日晒 ｜ 水洗 | Anaerobic ｜ Decaf ｜ Natural ｜ Washed |
| c2_origin 标题 | 产地（可选） | Origin (optional) |
| c2_origin 提示 | 不清楚产地也可以继续。 | Not sure? You can skip this. |
| c2_origin 选项 | 埃塞俄比亚 / 东非（花香果酸） ｜ 哥伦比亚 / 中南美（均衡果酸） ｜ 云南（坚果 / 红糖 / 厌氧） ｜ 肯尼亚（黑加仑 / 乌梅） | Ethiopia / East Africa (floral, bright) ｜ Colombia / Central & South America (balanced fruit acidity) ｜ Yunnan (nutty, brown sugar, anaerobic) ｜ Kenya (blackcurrant, dark plum) |

### 再确认 Q6（view.ts）

| 位置 | 中文 | English |
|---|---|---|
| 标题 | 哪些描述更贴近你的感受？ | Which of these are closer to what you tasted? |
| 提交按钮 | 更新风味卡 | Update my card |

### 组件内固定文案

#### 语境卡 ContextSetupCard

| 位置 | 中文 | English |
|---|---|---|
| 小标签 | 这杯咖啡 | This cup |
| 单品 / 拼配切换后缀 | ≤ 3 | ≤ 3 |
| 下一步 / 跳过 / 已选 | 下一步 ｜ 跳过 ｜ 已选 | Next ｜ Skip ｜ chosen |

#### 题卡 QuizCard

| 位置 | 中文 | English |
|---|---|---|
| 小标签 | 这一口 | This sip |

#### 第一次出卡 FirstDescriptionCard

| 位置 | 中文 | English |
|---|---|---|
| 提交按钮 | 确认风味卡 | Confirm my card |

#### Q6 EscalationModal

| 位置 | 中文 | English |
|---|---|---|
| 小标签 | 再看一眼 | One more look |

#### 终卡 FinalAttributionCard

| 位置 | 中文 | English |
|---|---|---|
| 再确认后的标记 | 已确认 | confirmed |
| 底部 icon aria | 首页 ｜ 重新体验 ｜ 分享 | Home ｜ Start over ｜ Share |
| 操作区 aria | 操作 | Actions |

#### 上方堆叠 CollectedStack

| 位置 | 中文 | English |
|---|---|---|
| 勾选卡标题 | 你的 5 个词 | Your 5 words |
| 收集中 aria | 收集中 | collecting |

#### About 抽屉 AboutDrawer

| 位置 | 中文 | English |
|---|---|---|
| 关闭 aria | 关闭 | Close |
| 展开 / 收起 | 展开 ｜ 收起 | Details ｜ Collapse |
| 数据流标题 | 评审资料如何用于风味描述 | How the review material feeds the descriptions |
| 数据流注 | 左：来源评审族与记录数；右：12 类风味特征；带宽是该来源在该特征上的累计权重（每条记录的风味词投影到该特征后求和） | left: source panels and their record counts; right: the 12 flavor features; ribbon width is that source's cumulative weight on that feature (each record's flavor words projected onto the feature, summed) |
| 光谱标题 | 16 组参考风味 | 16 reference profiles |
| 光谱注 | 本项目从所用资料中整理的分组，不是咖啡的全部分类；每条射线一组，长度按记录数的对数刻度，刻度色是它主要的风味特征 | groups organised from the material used here, not a taxonomy of all coffee; one ray per group, length on a log scale of its records, tick colours its main flavor features |
| 来源标题 / 行前缀 / 待复核 | 资料来源 ｜ 本项目如何使用这份资料 ｜ 条待复核，未上线 | Sources ｜ How this project uses it ｜ held back until re-verified |
| 来源族名 | CoffeeReview 编辑评审 ｜ Cup of Excellence 评审 ｜ Q-grader 储藏实验 ｜ Q-grader 数据集 ｜ 罗布斯塔 Q-grader 评审 ｜ 其他评审 | CoffeeReview editorial reviews ｜ Cup of Excellence juries ｜ Q-grader storage panel ｜ Q-grader dataset ｜ Robusta Q-grader panel ｜ other panels |

## 2. 卡片标题、说明标签与差异句（bundle.presentation）

| 位置 | 中文 | English |
|---|---|---|
| 第一次出卡标题 | 这杯咖啡的风味 | This cup's flavor |
| 终卡标题 | 风味卡 | Flavor card |
| 折叠层标题 | 相关风味说明 | Flavor notes |
| 参考资料前缀 | 参考资料： | Reference:  |
| 说明标签 OWNER_STATEMENT | 参考说明 | Reference note |
| 说明标签 CORPUS_MEASURED | 资料统计 | From the data |
| 说明标签 LITERATURE_CLAIM | 研究参考 | Research reference |
| 说明标签 COMPUTED_DELTA | 描述差异 | Where your description differs |
| 差异句模板 pos | 这次的描述中，{label}更突出。仅凭目前的信息，还无法判断这种差异的原因。 | In this description, {label} stands out more than this cup's setup usually shows. From what we have, the reason cannot be told. |
| 差异句模板 neg | 这次的描述中，{label}不太明显。仅凭目前的信息，还无法判断这种差异的原因。 | In this description, {label} comes through less than this cup's setup usually shows. From what we have, the reason cannot be told. |
| 纸味 / 陈味组的提示 | 这些描述常与储存或处理有关，值得再喝一口确认。这里不对这杯咖啡做质量判断。 | These descriptions are often linked to storage or processing; worth a second sip to confirm. No quality judgement is made here. |
| 勾选提示（describe） | 选出最贴近你感受的 5 个词。 | Pick the 5 words closest to what you tasted. |

上屏的说明状态：OWNER_STATEMENT, CORPUS_MEASURED, LITERATURE_CLAIM, COMPUTED_DELTA；待补链接或待复核的文献句不上屏。

## 3. 题库 Q0–Q5（bundle.question_bank）

| 题 | 位置 | 中文 | English |
|---|---|---|---|
| Q0 | 提问 | 喝到酸了吗？是哪一种？ | Any acidity? Which kind? |
| Q0 | 选项 A | 柑橘 / 青苹果那种酸 | citrus / green-apple acidity |
| Q0 | 选项 B | 乳酸 / 发酵果酸（像酸奶、水果黄酒） | lactic / fermented-fruit acidity (like yoghurt) |
| Q0 | 选项 C | 酸感不明显 | acidity not noticeable |
| Q1 | 提问 | 闻起来最像什么？ | What does it smell like? |
| Q1 | 选项 A | 花香、茶感、草本 | floral, tea-like, herbal |
| Q1 | 选项 B | 坚果、烤面包、烤榛果 | nuts, toast, roasted hazelnut |
| Q1 | 选项 C | 热带水果，带一点微醺酒香 | tropical fruit with a boozy edge |
| Q2 | 提问 | 能喝出甜味吗？更像哪一种？ | Do you taste sweetness? Which kind? |
| Q2 | 选项 A | 清爽的花蜜 / 蔗糖甜 | light nectar or cane-sugar sweetness |
| Q2 | 选项 B | 浓郁的焦糖 / 黑巧克力 | rich caramel or dark chocolate |
| Q2 | 选项 C | 熟果、果酱那种浓稠的甜 | ripe-fruit, jammy sweetness |
| Q2 | 选项 D | 甜感不明显 | hardly any sweetness |
| Q3 | 提问 | 口感如何？ | How does it feel in the mouth? |
| Q3 | 选项 A | 清爽，像绿茶或果汁 | light, like green tea or juice |
| Q3 | 选项 B | 顺滑，像牛奶或丝绒 | smooth, like milk or velvet |
| Q3 | 选项 C | 厚重，像黑巧或糖浆 | heavy, like dark chocolate or syrup |
| Q4 | 提问 | 尾段苦吗？ | Bitter at the end? |
| Q4 | 选项 A | 有一点苦，但像黑巧一样回甘 | a little, but it turns sweet like dark chocolate |
| Q4 | 选项 B | 完全不苦 | none at all |
| Q4 | 选项 C | 苦味明显，盖过其他味道 | clearly bitter, over the other flavours |
| Q5 | 提问 | 整体更像哪种？ | Overall, which is closer? |
| Q5 | 选项 A | 味道一层一层，分得清 | flavours come one at a time, distinct |
| Q5 | 选项 B | 味道混在一起，饱满 | flavours blend together, full |

## 4. 十六组参考风味（终卡标题与标签）

「参考实例」一列不上屏，只作内部对照；命名规则：两个主要感官参照，不加修饰词。

| 中文名 | English | 标签 zh | tags en | 参考实例（未上屏） | 记录数 |
|---|---|---|---|---|---|
| 黄桃与熟果 | Yellow Peach & Ripe Fruit | 黄桃 ｜ 熟果 ｜ 蔗糖 ｜ 柑橘 | yellow peach ｜ ripe fruit ｜ cane sugar ｜ citrus | 哥伦比亚 厌氧日晒 / 埃塞俄比亚 日晒 G1 | 1343 |
| 榛果可可与红莓 | Hazelnut Cocoa & Red Berry | 榛果 ｜ 可可 ｜ 红莓 ｜ 柑橘 | hazelnut ｜ cocoa ｜ red berry ｜ citrus | 危地马拉 安提瓜水洗 (Guatemala Antigua) | 1169 |
| 蜂蜜与杏桃 | Honey & Apricot | 蜂蜜 ｜ 杏桃 ｜ 甜橙 ｜ 柔和 | honey ｜ apricot ｜ sweet orange ｜ smooth | 埃塞俄比亚 西达摩 水洗 / 哥伦比亚 蜜处理 | 983 |
| 黑巧克力与烤榛果 | Dark Chocolate & Roasted Hazelnut | 黑巧克力 ｜ 烤榛果 ｜ 红糖 ｜ 醇厚 | dark chocolate ｜ roasted hazelnut ｜ brown sugar ｜ full body | 哥伦比亚 惠兰水洗 (Colombia Huila) | 757 |
| 雪松与烟熏 | Cedar & Smoke | 雪松 ｜ 烟熏 ｜ 黑巧克力 ｜ 松露 | cedar ｜ smoke ｜ dark chocolate ｜ truffle | 苏门答腊 湿剥曼特宁 (Sumatra Mandheling PWN) | 720 |
| 柑橘与柚子酸质 | Citrus & Yuzu Acidity | 柚子 ｜ 柑橘 ｜ 黑加仑 ｜ 明亮 | yuzu ｜ citrus ｜ blackcurrant ｜ bright | 肯尼亚 AA (Kenya AA SL28/SL34) | 639 |
| 蔗糖与蜂蜜 | Cane Sugar & Honey | 蔗糖 ｜ 蜂蜜 ｜ 焦糖 ｜ 柔和 | cane sugar ｜ honey ｜ caramel ｜ smooth | 巴西 黄波本 (Brazil Yellow Bourbon) | 606 |
| 黑加仑与树莓 | Blackcurrant & Raspberry | 黑加仑 ｜ 树莓 ｜ 木质 ｜ 酒香 | blackcurrant ｜ raspberry ｜ woody ｜ winey | 埃塞俄比亚 哈拉尔 (Ethiopia Harrar) | 592 |
| 茉莉与白花 | Jasmine & White Flowers | 茉莉花 ｜ 白花 ｜ 佛手柑 ｜ 水蜜桃 | jasmine ｜ white flowers ｜ bergamot ｜ peach | 埃塞俄比亚 耶加雪菲水洗 / 瑰夏 (Geisha) | 387 |
| 烟熏与风干木 | Smoke & Aged Wood | 烟熏 ｜ 泥炭 ｜ 风干木 ｜ 烟草 | smoke ｜ peat ｜ aged wood ｜ tobacco | 爪哇 老深烘 (Java Arabica / Old Brown) | 325 |
| 小豆蔻与肉桂 | Cardamom & Cinnamon | 小豆蔻 ｜ 肉桂 ｜ 红糖 ｜ 葡萄干 | cardamom ｜ cinnamon ｜ brown sugar ｜ raisin | 也门 摩卡 (Yemen Matari) | 273 |
| 重可可与回甘 | Dark Cocoa & Sweet Finish | 重可可 ｜ 焦糖 ｜ 烘烤 ｜ 回甘 | dark cocoa ｜ caramel ｜ roast ｜ lingering sweet | 意式拼配 深烘 (Italian Dark Roast Blend) | 217 |
| 朗姆与发酵果香 | Rum & Fermented Fruit | 朗姆酒香 ｜ 发酵果香 ｜ 热带水果 ｜ 酒香 | rum ｜ fermented fruit ｜ tropical fruit ｜ winey | 洪都拉斯 威士忌雪莉桶 / 厌氧日晒瑰夏 | 60 |
| 草本与绿茶 | Herbal & Green Tea | 茉莉绿茶 ｜ 柠檬草 ｜ 青苹果 ｜ 清脆 | jasmine green tea ｜ lemongrass ｜ green apple ｜ crisp | 巴拿马 浅烘铁皮卡 (Panama Typica) | 47 |
| 纸味与陈味 | Papery & Stale | 纸味 ｜ 陈味 ｜ 霉味 ｜ 过发酵 | papery ｜ stale ｜ musty ｜ over-fermented | （负向约束集合，不推荐商品） | 12 |
| 丝绒与糖浆口感 | Velvet & Syrup Mouthfeel | 丝绒 ｜ 糖浆 ｜ 奶油 ｜ 醇厚 | velvet ｜ syrup ｜ cream ｜ full body | 巴西 半日晒 / 罗布斯塔精选 (Brazil Pulped Natural) | 12 |

## 5. 维度词（描述与勾选时按维度取的词）

| 维度 | 标签 zh | label en | 维度词 zh | words en | 消费端补充 zh | consumer en |
|---|---|---|---|---|---|---|
| acidity | 酸质 | acidity | 清冽果酸 ｜ 明亮酸质 ｜ 柑橘酸 | crisp acidity ｜ bright acidity ｜ citric |  | citrus ｜ juicy ｜ tart ｜ crisp ｜ citrusy ｜ tangy ｜ lemony |
| sweetness | 甜感 | sweetness | 高甜感 ｜ 蔗糖甜 ｜ 蜂蜜感 | high sweetness ｜ cane sugar ｜ honeyed | 冰糖雪梨 ｜ 太妃糖 ｜ 麦芽糖 ｜ 黑糖 ｜ 罗汉果甜 | rock-sugar pear ｜ toffee ｜ maltose ｜ dark brown sugar ｜ monk-fruit sweetness ｜ jam ｜ candy ｜ syrup ｜ jammy |
| body | 醇厚度 | body | 丝绒感 ｜ 醇厚 ｜ 圆润口感 | velvety ｜ full body ｜ round mouthfeel |  | silky |
| floral | 花香 | floral | 茉莉花 ｜ 玉兰花 ｜ 白花 | jasmine ｜ magnolia ｜ white flowers | 桂花 ｜ 栀子花 ｜ 咖啡花 ｜ 白兰花 ｜ 洋甘菊 | osmanthus ｜ gardenia ｜ coffee blossom ｜ white magnolia ｜ chamomile ｜ floral ｜ tea-like |
| fruity | 果香 | fruity | 水蜜桃 ｜ 黄桃 ｜ 黑加仑 ｜ 杏桃 | peach ｜ yellow peach ｜ blackcurrant ｜ apricot | 巨峰葡萄 ｜ 荔枝 ｜ 杨梅 ｜ 西梅 ｜ 青梅 ｜ 红心芭乐 | Kyoho grape ｜ lychee ｜ bayberry ｜ prune ｜ green plum ｜ pink guava ｜ berry ｜ berries ｜ stone fruit ｜ tropical ｜ melon |
| nutty_chocolate | 坚果巧克力 | nutty & chocolate | 烤榛果 ｜ 黑莓可可 ｜ 提拉米苏 | roasted hazelnut ｜ berry cocoa ｜ tiramisu |  | chocolate |
| fermented_winey | 发酵与酒香 | fermented & winey | 酒香 ｜ 朗姆酒 ｜ 发酵果酱 | anaerobic winey ｜ rum ｜ fermented jam | 米酒 ｜ 酒酿 ｜ 酒酿圆子 ｜ 黄酒 ｜ 热带水果发酵酱 ｜ 水果黄酒 ｜ 微醺朗姆 ｜ 微醺 ｜ 威士忌桶 ｜ 雪莉桶 ｜ 野果发酵 ｜ 微醺酒香 ｜ 厌氧风味 ｜ 苹果酒感 ｜ 水果发酵酱 ｜ 朗姆酒香 | rice wine ｜ jiuniang (sweet fermented rice) ｜ jiuniang rice balls ｜ huangjiu ｜ tropical fruit ferment ｜ fruit huangjiu ｜ tipsy rum ｜ tipsy ｜ whisky barrel ｜ sherry cask ｜ funky ｜ wine ｜ funk ｜ cider ｜ fermented ｜ winey |
| bitter_roasted | 烘烤苦感 | roast & bitter | 黑巧回甘 ｜ 烟熏可可 ｜ 重烘焙香 | dark chocolate finish ｜ smoky cocoa ｜ deep roast | 烤杏仁 ｜ 烘焙麦芽 ｜ 黑芝麻 ｜ 松露巧克力 | roasted almond ｜ roasted malt ｜ black sesame ｜ truffle chocolate ｜ smokey ｜ roasted ｜ dark roast ｜ ashy |
| spice | 香料 | spice | 小豆蔻 ｜ 肉桂 ｜ 辛香料 | cardamom ｜ cinnamon ｜ warm spice |  |  |
| herbal_green | 草本绿茶 | herbal & green | 茉莉绿茶 ｜ 高山乌龙 ｜ 草本清香 | jasmine green tea ｜ high-mountain oolong ｜ fresh herbal | 高山龙井 ｜ 武夷岩茶 ｜ 鸭屎香 ｜ 普洱茶韵 | high-mountain Longjing ｜ Wuyi rock tea ｜ Ya Shi Xiang (Dancong) ｜ Pu'er tea finish ｜ tea ｜ grass ｜ grassy ｜ herbal |
| woody_earthy | 木质泥土 | woody & earthy | 风干雪松 ｜ 泥炭木质 ｜ 松露 | aged cedar ｜ peaty wood ｜ truffle |  |  |
| defect | 瑕疵 | defect | 风味瑕疵 ｜ 过发酵味 | off-flavor ｜ over-fermented |  |  |

## 6. 94 个规范概念的极简词（用户录入豆子时上卡）

| 概念 | 中文 | English |
|---|---|---|
| acetic_vinegar | 醋味 | vinegar |
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
| molasses | 糖蜜 | molasses |
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
| wine_like_character | 酒香 | winey |
| woody | 木质 | woody |

## 7. 相关风味说明（折叠层里的句子）

标签为空的行不上屏（待复核）。

| 语境 | 标签 | 中文 | English | 出处 |
|---|---|---|---|---|
| C0_ESPRESSO | 参考说明 | 意式浓缩放大醇厚度与油脂，前段高挥发花果香被压缩。 | Espresso amplifies body and oils; the volatile floral and fruit top notes are compressed. | owner |
| C0_COLD_BREW | 参考说明 | 冷萃抑制低挥发酸，酸质与花香偏弱，甜感与醇厚更突出。 | Cold brew suppresses the low-volatility acids: less acidity and floral lift, more sweetness and body. | owner |
| C0_V60 | 参考说明 | 手冲常见的表现是花香与果酸更清晰，醇厚较轻。 | Pour-over tends to show florals and fruit acidity more clearly, with a lighter body. | owner |
| C0_FRENCH_PRESS | 参考说明 | 浸泡式萃取带入更多油脂与细粉，醇厚度上升，干净度下降。 | Immersion brewing carries more oils and fines: more body, less clarity. | owner |
| C1_LIGHT | 参考说明 | 浅烘保留更多绿原酸与高挥发香气，酸质与花果香突出。 | Light roasts keep more chlorogenic acids and volatile aromatics: acidity and floral-fruit notes lead. | owner |
| C1_MEDIUM_LIGHT | 参考说明 | 中浅烘保留花果酸质，同时开始形成焦糖化甜感。 | Medium-light roasts keep the floral-fruit acidity while caramelisation sweetness begins. | owner |
| C1_MEDIUM | 参考说明 | 中烘平衡酸质与美拉德产物，坚果与焦糖增强。 | Medium roasts balance acidity against Maillard products: nut and caramel rise. | owner |
| C1_MEDIUM_DARK | 参考说明 | 中深烘美拉德产物占比高，醇厚度、巧克力与苦感上升，酸质下降。 | Medium-dark roasts are Maillard-dominated: body, chocolate and bitterness rise, acidity falls. | owner |
| C1_DARK | 参考说明 | 深烘绿原酸大量降解，焦糖苦与烟熏占主导。 | Dark roasts degrade most chlorogenic acids: caramelised bitterness and smoke dominate. | owner |
| C1_VERY_DARK | 参考说明 | 极深烘以碳化与烟熏为主，品种与产地特征基本被覆盖。 | Very dark roasts are carbonised and smoky; origin and variety character is mostly covered. | owner |
| C2_process_WASHED | 参考说明 | 水洗去胶质快，内源有机酸突出：干净度高、柑橘、花香、高酸。 | Washed processing removes mucilage quickly; the bean's own organic acids stand out: clean, citrus, floral, high acidity. | owner |
| C2_process_NATURAL | 参考说明 | 日晒让果肉糖分在发酵中渗入豆内，还原糖与游离氨基酸升高：果酱、热带水果、高甜。 | Natural processing lets fruit sugars ferment into the seed: more reducing sugars and free amino acids — jam, tropical fruit, high sweetness. | owner |
| C2_process_ANAEROBIC | 参考说明 | 厌氧发酵常带来更多乳酸与酯类风味：酸奶感与酒香。 | Anaerobic fermentation tends to add lactic and ester notes: yoghurt and winey character. | owner |
| C2_process_HONEY | 参考说明 | 蜜处理保留部分果胶发酵，甜感与醇厚介于水洗与日晒之间。 | Honey processing keeps part of the mucilage: sweetness and body between washed and natural. | owner |
| C2_process_DECAF | 参考说明 | 脱因工艺去除部分前体物质，香气强度整体下降。 | Decaffeination removes some precursors; aroma intensity drops overall. | owner |
| C2_variety_GESHA | 参考说明 | 瑰夏常见茉莉、白花与柑橘酸质，醇厚偏轻。 | Gesha commonly shows jasmine, white florals and citrus acidity with a lighter body. | owner |
| C2_variety_BOURBON | 参考说明 | 波本甜感与平衡度好，焦糖与红果常见。 | Bourbon is sweet and balanced; caramel and red fruit are typical. | owner |
| C2_variety_SL28_SL34 | 参考说明 | SL28/SL34 以黑加仑与明亮柑橘酸质著称。 | SL28/SL34 are known for blackcurrant and bright citric acidity. | owner |
| C2_variety_ETHIOPIAN_LANDRACE | 参考说明 | 埃塞原生种以茉莉花、柑橘与蓝莓（日晒）为标志。 | Ethiopian landraces are marked by jasmine, citrus and, when natural, blueberry. | owner |
| C2_variety_TYPICA | 参考说明 | 铁皮卡干净、甜感柔和，醇厚适中。 | Typica is clean and gently sweet with moderate body. | owner |
| C2_variety_ROBUSTA | 参考说明 | 罗布斯塔前体糖分低、绿原酸与咖啡因高：苦感与醇厚重，花果弱。 | Robusta has low sugar precursors and high chlorogenic acid and caffeine: heavy bitterness and body, little floral-fruit. | owner |
| C0_V60__C1_LIGHT | 参考说明 | 浅烘保留了更多绿原酸与挥发性花果香，手冲又让这些花香与果酸更清晰。 | Light roast keeps more chlorogenic acids and volatile floral-fruit aromatics, and pour-over lets those florals and acids read clearly. | owner |
| C0_ESPRESSO__C1_MEDIUM_DARK | 参考说明 | 中深烘的美拉德产物在意式高压下被油脂放大：黑巧、焦糖与厚重口感主导，酸质退到后段。 | Medium-dark Maillard products are amplified by espresso pressure and oils: dark chocolate, caramel and weight lead; acidity retreats. | owner |
| C0_COLD_BREW__C1_LIGHT | 参考说明 | 冷萃压低了浅烘的低挥发酸，花香减弱、甜感与茶感更清晰。 | Cold brew flattens the light roast's low-volatility acids: less floral lift, clearer sweetness and tea-like body. | owner |
| C1_LIGHT__C2_process_WASHED | 参考说明 | 浅烘 + 水洗保留了柠檬酸与高极性酯类：柑橘、茉莉与干净的酸质。 | Light roast plus washed processing keeps citric acid and polar esters: citrus, jasmine and clean acidity. | owner |
| C1_LIGHT__C2_process_NATURAL | 参考说明 | 浅烘 + 日晒把发酵进豆内的果糖与酯类完整保留：蓝莓、果酱与高甜。 | Light roast plus natural processing keeps the fermented fruit sugars and esters: blueberry, jam and high sweetness. | owner |
| C1_MEDIUM_DARK__C2_process_ANAEROBIC | 参考说明 | 中深烘 + 厌氧常见的表现是黑巧与发酵感并存；若你尝到的酸质更高，与这个组合的常见表现不同。水温偏低是可能的原因之一，但仅凭描述无法确定。 | Medium-dark plus anaerobic usually reads as dark chocolate with fermentation; a brighter acidity differs from the usual pattern for this combination. A cool brew is one possible reason, but the description alone cannot tell. | owner |
| C1_VERY_LIGHT | 参考说明 | 极浅烘几乎不动豆子的原始结构：绿原酸与挥发性花果香保留最完整，酸质最突出，甜感与醇厚尚未展开。 | A very light roast barely touches the bean's original structure: chlorogenic acids and volatile florals stay almost intact, acidity is at its most pronounced, sweetness and body have not opened yet. | owner |
| C0_POUR_OVER_V60 | 研究参考 | 粉床细粉迁移引发微观通道效应时，局部过萃会导致中段甜感中断，并在余韵中引入涩感与杂味。 | When fines migrate and open micro-channels in the bed, local over-extraction breaks the mid-palate sweetness and brings astringency and off-notes into the finish. | Coffee Ad Astra (Jonathan Gagné) |
| C0_POUR_OVER_V60__C1_LIGHT | 研究参考 | 浅烘手冲时，萃取率落在合适区间才有饱满的中段甜感；萃取率不足则酸而空，过高则涩。 | For light roasts on pour-over, mid-palate sweetness fills in only inside the right extraction-yield window; under-extraction reads sour and hollow, over-extraction astringent. | Coffee Ad Astra (Jonathan Gagné) |
| C0_ESPRESSO__C1_MEDIUM_DARK | 研究参考 | 中深烘意式在高压下通道效应更敏感：粉饼不均会同时出现欠萃的酸与过萃的苦。 | Medium-dark espresso is more sensitive to channeling under pressure: an uneven puck shows under-extracted sourness and over-extracted bitterness at once. | Coffee Ad Astra (Jonathan Gagné) |
| C0_POUR_OVER_V60 | （不上屏：LITERATURE_CLAIM_NEEDS_REVERIFICATION） | 快萃与较高水温优先溶解极性较高的有机酸分子，前段酸质与花果香先被释放。 | Fast extraction at higher water temperature dissolves the more polar organic acids first, so acidity and floral-fruit notes lead. | UC Davis Coffee Center |
| C0_ESPRESSO | （不上屏：LITERATURE_CLAIM_NEEDS_REVERIFICATION） | 研磨度过细会加速大分子绿原酸内酯的释放，从而增加尾段苦感；高压萃取同时带出更多油脂与醇厚度。 | Too fine a grind accelerates the release of large chlorogenic-acid lactones and adds late bitterness; pressure extraction also carries more oils and body. | UC Davis Coffee Center |
| C0_COLD_BREW | 研究参考 | 低温长时萃取下，挥发性酸与酸质通常更弱，感官图谱偏向甜感与圆润。 | Under long, cold extraction the volatile acids and acidity are usually weaker; the sensory map shifts toward sweetness and roundness. | UC Davis Coffee Center |
| C0_FRENCH_PRESS | 研究参考 | 浸泡式萃取与金属滤网让更多细粉与油脂进入杯中，醇厚度上升、干净度下降。 | Immersion brewing through a metal filter passes more fines and oils: more body, less clarity. | UC Davis Coffee Center |
| C2_variety_GESHA | （不上屏：LITERATURE_CLAIM_NEEDS_REVERIFICATION） | 瑰夏（Gesha）基因决定了其高挥发性单萜烯（如芳樟醇）的高表达上限，浅烘焙下呈现高锐白花与单醇果酸。 | The Gesha genotype sets a high ceiling for volatile monoterpenes such as linalool; at light roast it reads as sharp white florals and clean, single-note fruit acidity. | World Coffee Research |
| C1_LIGHT | 研究参考 | 浅烘保留品种的花香与果酸参照物（花香、柑橘酸、单醇甜感），焦糖化产物尚未主导。 | Light roasting keeps the variety's floral and fruit-acid references (florals, citric acidity, clean sweetness) before caramelisation products take over. | World Coffee Research |
| C1_MEDIUM | 研究参考 | 中烘时焦糖化与美拉德参照物（红糖、坚果、可可）与残余果酸达到平衡。 | At medium roast the caramelisation and Maillard references (brown sugar, nut, cocoa) balance the remaining fruit acidity. | World Coffee Research |
| C1_DARK | 研究参考 | 深烘下花香与果酸参照物被烘烤参照物（烟熏、焦糖苦、灰烬）覆盖。 | At dark roast the floral and fruit-acid references are covered by roast references (smoke, burnt caramel, ash). | World Coffee Research |

## 8. About（about.ts，经执行导出）

| 位置 | 中文 | English |
|---|---|---|
| 页面小标题 | 风味描述如何形成 | How a flavor card is made |
| Eyebrow | 关于 flavorwords | About flavorwords |
| 标题 | 说清这一杯的风味 | Put this cup into words |
| 导言 1 | 酸质像柑橘，还是青苹果？甜感接近蜂蜜，还是焦糖？一杯咖啡留下的感受，有时还需要几个合适的词才能说清楚。 | Is the acidity closer to citrus or green apple? Is the sweetness more like honey or caramel? What a coffee leaves behind sometimes takes a few well-chosen words to say. |
| 导言 2 | flavorwords 从你喝到的感受出发，围绕酸质、香气、甜感和口感，逐步缩小描述的范围。你选出贴近这一杯的词，组成自己的风味卡。 | flavorwords starts from what you tasted and narrows the description step by step, through acidity, aroma, sweetness and mouthfeel. You pick the words that fit this cup, and they become your flavor card. |
| 参考段标题 | 为日常品饮整理的参考 | A reference for everyday drinking |
| 参考段 1 | 产品中的风味词与参考风味，来自对咖啡评审、感官词汇和消费者表达资料的整理。它们帮助你比较不同描述，找到更接近当前感受的说法。 | The flavor words and reference profiles come from organising public coffee reviews, sensory lexicons and consumer vocabulary. They help you compare descriptions and find the one closest to what you taste. |
| 参考段 2 | 相关的咖啡资料与研究说明，提供进一步理解这杯咖啡的参考。资料来源和使用方式列在方法说明中。 | Related coffee references and research notes offer a way to understand the cup a little further. Sources and how they are used are listed under the method notes. |
| 示例卡 eyebrow | 示例风味卡 | Sample flavor card |
| 示例卡标题 | 茉莉与白花 | Jasmine & White Flowers |
| 示例卡词 | 茉莉花 ｜ 白花 ｜ 佛手柑 ｜ 水蜜桃 ｜ 清冽果酸 | jasmine ｜ white flowers ｜ bergamot ｜ peach ｜ crisp acidity |
| 示例卡注 | 示例，不是真实结果：一次浅烘手冲的描述可能长这样。 | A sample, not a real result: what a light-roast pour-over description might look like. |
| 作者段 eyebrow | 研究、设计与开发 | Research, design and development |
| 作者 | 潘岱 · Dai Pan | Dai Pan · 潘岱 |
| 作者段 1 | 我整理公开咖啡评审与感官词汇资料，建立描述之间的对应关系，并设计了从品饮感受到风味卡的交互过程。flavorwords 的工作，集中在资料组织、词汇编排、提问方式和产品实现上。 | I organised public coffee reviews and sensory lexicons, built the correspondences between descriptions, and designed the path from what you taste to a flavor card. The work in flavorwords is in organising the material, arranging the vocabulary, the way questions are asked, and building the product. |
| 作者段 2 | 专业评审与研究结论来自各自的原始作者，具体来源列于资料说明中。 | Professional reviews and research findings belong to their original authors; the sources are listed under the data notes. |
| 贡献 12 | 12 类风味特征：每个风味词都归到其中一类；提问、出词和风味卡都按这些类取词。 | 12 flavor features: every flavor word belongs to one of them; questions, suggested words and the card all draw from these. |
| 贡献 16 | 16 组参考风味：从评审资料整理的分组，用来给出第一版描述；不是咖啡的全部分类。 | 16 reference profiles: groups organised from the review material to give a first description; not a taxonomy of all coffee. |
| 贡献 94 | 94 个风味词：对照专业感官词汇整理的双语基础词表，加上中文消费端的补充说法。 | 94 flavor words: a bilingual base list aligned with professional lexicons, plus Chinese consumer expressions. |
| 资料范围标题 | 资料范围 | Scope of the material |
| 资料范围 assertions | 83,031 条风味描述记录：从公开评审文本中抽出的感官断言；83K 冻结检查点。 | 83,031 flavor-description records: sensory assertions extracted from public review text; the frozen 83K checkpoint. |
| 资料范围 coffees | 9,128 条咖啡评审记录：去重后的记录数；其中 8,142 条带至少一个风味词，进入参考风味分组。 | 9,128 coffee review records: deduplicated records; 8,142 of them carry at least one flavor word and enter the reference-profile grouping. |
| 资料范围 consumers | 4,042 位消费者用词来源：来自 GACTT 公开数据的聚合词频；不是 flavorwords 的使用者。 | 4,042 consumers behind the vocabulary: aggregate word frequencies from the public GACTT data; not users of flavorwords. |
| 资料范围 sources | 3 份研究参考来源：8 条说明上线，3 条待复核后再展示。 | 3 research reference sources: 8 notes shown, 3 held back until re-verified. |
| 资料范围脚注 | 版本 product-vector-v1，统计于 2026-09-12；去重口径与用途见方法说明。 | Version product-vector-v1, counted on 2026-09-12; deduplication and use are described under the method notes. |

### About · 风味描述如何形成 / How a flavor card is made（默认折叠）

| 位置 | 中文 | English |
|---|---|---|
| 摘要 | 从几次选择开始，逐步缩小描述的范围，最后由你确认。 | A few choices narrow the description step by step; you confirm the result. |
| 参考资料 / Reference material | 风味词与参考风味来自公开的咖啡评审文本、感官词汇表与消费者用词统计。每个词都对应到 12 类风味特征中的一类，这样不同来源的描述才能放在一起比较。 | The flavor words and reference profiles come from public coffee review text, sensory lexicons and consumer word counts. Every word maps to one of 12 flavor features, so descriptions from different sources can be compared side by side. |
| 提问方式 / How the questions work | 先问酸质和香气，再问甜感和口感，最后问苦感和整体印象。前两题给出一个基本方向；后面的回答如果与它不一致，就多问一题，或在出词后请你再看一眼；答案一致时少问。每个问题都有「不明显」一类的出口，不假设你一定喝到了什么。 | Acidity and aroma first, then sweetness and mouthfeel, then bitterness and the overall impression. The first two answers set a direction; if later answers disagree with it, one more question is asked, or you are asked to look again after the words appear; when answers agree, fewer questions are asked. Every question has a "not noticeable" way out, so nothing assumes what you must have tasted. |
| 描述的选择与确认 / Choosing and confirming the words | 系统先给出 8 个候选词，其中 3 个更可能，5 个作为补充；你从中选出 5 个，这 5 个词就是风味卡。如果你选的词与前面的回答方向差得很远，会再请你确认一次，然后按你确认的结果更新。 | 8 candidate words are offered, 3 more likely and 5 as alternatives; you pick 5, and those 5 are the card. If your picks point far from your earlier answers, you are asked once more, and the card is updated to what you confirm. |
| 结果的适用范围 / What the result covers | 风味卡记录的是你这次的描述，不是这杯咖啡的检测结果。参考说明来自公开资料与本项目的整理，用于帮助理解，不用于判断你喝得对不对。描述与参考的差异只作为提示，原因需要更多信息才能确定。 | The card records your description of this cup, not a measurement of the coffee. The reference notes come from public sources and this project's own organisation; they are there to help you understand, not to judge whether you tasted correctly. A difference between your description and the reference is only a hint; its cause needs more information. |

### About · 技术说明 / Technical notes（默认折叠）

| 位置 | 中文 | English |
|---|---|---|
| 摘要 | 一个投影矩阵、一组向量、余弦相似度；不训练模型。 | One projection matrix, a set of vectors, cosine similarity; no model is trained. |
| 向量与公式 / Vectors and formulas | 每类风味特征是向量的一个分量，共 12 个分量。V_pred = normalize(Σ K)：冲煮、烘焙、豆种与处理法各自的参考向量相加；V_user = normalize(Σ Q)：每个回答的增量向量相加；ΔV = V_user − V_pred 是两者的差；V_target = normalize(V_pred + α·ΔV)，α = 0.5，再确认后 α = 0.9。 | Each flavor feature is one component of a 12-component vector. V_pred = normalize(Σ K): the reference vectors of brew, roast, variety and processing added; V_user = normalize(Σ Q): the answer increments added; ΔV = V_user − V_pred is the difference between them; V_target = normalize(V_pred + α·ΔV) with α = 0.5, and α = 0.9 after a second confirmation. |
| 相干性检查 / Coherence check | 回答分组后投影到 16 组参考风味上，比较两组回答的相似度：≥ 0.8 视为一致，< 0.65 视为明显不一致。另外检查烘焙方向：浅烘的酸与花香、深烘的苦与厚重同时很强时，直接进入再确认。 | Answers are grouped and projected onto the 16 reference profiles; the similarity of two groups is compared: ≥ 0.8 counts as consistent, < 0.65 as clearly inconsistent. Roast direction is checked separately: strong light-roast acidity and florals together with strong dark-roast bitterness and weight go straight to a second confirmation. |
| 相似度的用途 / What similarity is used for | 余弦相似度只用于在 16 组参考风味与候选记录中找最接近的几项，再由你的选择决定；不给咖啡打分，也不输出概率。 | Cosine similarity only finds the closest few among the 16 reference profiles and candidate records; your picks decide from there. It does not score coffees and outputs no probability. |
| 实现选择 / Implementation choices | 没有训练模型，没有概率拟合；全部计算在手机本地完成。这是实现方式的说明，不是质量保证。 | No model is trained and no probability is fitted; everything runs on the phone. This describes how it is built, not a guarantee of quality. |

### About · 资料来源 / Sources（默认折叠）

| 位置 | 中文 | English |
|---|---|---|
| 摘要 | 3 份研究参考来源与一份消费者用词统计。链接与许可已列出；3 条说明待复核，未上线。 | 3 research reference sources and one consumer word count. Links and licences are listed; 3 notes are held back until re-verified. |
| World Coffee Research (WCR) — Sensory Lexicon / World Coffee Research (WCR) — Sensory Lexicon | 风味与香气属性的标准词汇与参照物；用于对齐 94 个风味词，以及浅、中、深烘的参考说明。<br>来源：https://worldcoffeeresearch.org/resources/sensory-lexicon<br>许可：CC BY-SA 4.0（2026-09-12 核对） | Standard vocabulary and references for flavor and aroma attributes; used to align the 94 flavor words and for the light, medium and dark roast reference notes.<br>Source: https://worldcoffeeresearch.org/resources/sensory-lexicon<br>Licence: CC BY-SA 4.0 (checked 2026-09-12) |
| UC Davis Coffee Center — brewing and sensory research / UC Davis Coffee Center — brewing and sensory research | 滴滤咖啡的萃取与感官研究；用于冷萃与法压的参考说明。两条关于萃取先后的说明待复核，暂不展示。<br>来源：DOI: 10.1016/j.foodchem.2020.126567 (Cotter et al., 2020, Food Chemistry; reference paper supplied by the owner)<br>许可：学术引用 / 合理使用（2026-09-12 核对） | Brewing and sensory research on drip coffee; used for the cold-brew and French-press reference notes. Two notes on extraction order are pending re-verification and are not shown.<br>Source: DOI: 10.1016/j.foodchem.2020.126567 (Cotter et al., 2020, Food Chemistry; reference paper supplied by the owner)<br>Licence: Academic citation / fair use (checked 2026-09-12) |
| Coffee Ad Astra (Jonathan Gagné) — The Physics of Filter Coffee / Coffee Ad Astra (Jonathan Gagné) — The Physics of Filter Coffee | 滤泡咖啡萃取的物理模型；用于通道效应与萃取率的参考说明。<br>来源：https://coffeeadastra.com/ ; The Physics of Filter Coffee, ISBN 978-0-578-95028-0<br>许可：个人研究引用，署名作者（2026-09-12 核对） | A physical model of filter-coffee extraction; used for the notes on channeling and extraction yield.<br>Source: https://coffeeadastra.com/ ; The Physics of Filter Coffee, ISBN 978-0-578-95028-0<br>Licence: Personal research citation with author attribution (checked 2026-09-12) |
| Great American Coffee Taste Test (GACTT) — consumer vocabulary / Great American Coffee Taste Test (GACTT) — consumer vocabulary | 4,042 位消费者盲测用词的聚合频次，不含原文；用于中文消费端词汇的对照。<br>来源：GACTT_CONSUMER_TERM_FREQUENCY.tsv<br>许可：聚合计数，不含原文 | Aggregate word frequencies from 4,042 consumers' blind-tasting notes, no original text; used to cross-check the Chinese consumer vocabulary.<br>Source: GACTT_CONSUMER_TERM_FREQUENCY.tsv<br>Licence: aggregate counts, no text |

### About · 资料来源列表（本项目如何使用这份资料）

| 来源 | 中文 | English | 许可 | 说明句 |
|---|---|---|---|---|
| World Coffee Research (WCR) | 风味属性的标准词汇与参照物 | standard vocabulary and references for flavor attributes | CC BY-SA 4.0（2026-09-12 核对） | 3 上线 / 1 待复核 |
| UC Davis Coffee Center | 滴滤萃取的分段研究与感官图谱 | fractionated drip-brew studies and sensory maps | 学术引用 / 合理使用（2026-09-12 核对） | 2 上线 / 2 待复核 |
| Coffee Ad Astra (Jonathan Gagné) | 滤泡萃取的物理模型 | a physical model of filter extraction | 个人研究引用，署名作者（2026-09-12 核对） | 3 上线 / 0 待复核 |
| Great American Coffee Taste Test (GACTT) | 4,042 位消费者的用词频次 | word frequencies from 4,042 consumers | 聚合计数，不含原文 | 0 上线 / 0 待复核 |


# flavorwords 前端文案总表（审核稿）

自动导出自 `product-vector-v1.json`（product-vector-v1）、`view.ts` / `about.ts`（经 esbuild 执行）与组件内固定文案。每一行都是用户会在屏幕上看到的字。修改后请告诉我改哪一行，我改源头再重新导出。

## 1. 首页与流程界面

### 首页 Hero（view.ts appShell）

| 位置 | 中文 | English |
|---|---|---|
| 口号 | Every taste has its own vocabulary. | Every taste has its own vocabulary. |
| 标题 | 风味，自有表达。 | Put this cup into words. |
| 段落 | 像柑橘，像可可，或是某种熟悉却一时叫不出名字的味道。flavorwords 帮你找到贴近感受的词，组成这一杯的风味卡。 | Some coffees are easy to taste, but harder to describe. Find the words for what you taste, and bring them together in your own flavor card. |
| 行动主张 | Put this cup into words. |  |
| 开始链接（与下方按钮同一动作） | 从这一口开始 | Start with this cup |
| 开始按钮 | 开始 | Start |
| About 按钮 aria | 关于 | About |
| 语言切换 | EN | 中 |
| 添加到桌面 · 图标 | 添加到桌面 | Add to home screen |
| 添加到桌面 · 标题 | 添加到主屏幕 | Add to Home Screen |
| 添加到桌面 · iOS Safari | 在 Safari 底部点分享，选择「添加到主屏幕」。 | Tap Share at the bottom of Safari, then choose “Add to Home Screen”. |
| 添加到桌面 · iOS 其他浏览器 | 用 Safari 打开这个页面，点分享，选择「添加到主屏幕」。 | Open this page in Safari, tap Share, then choose “Add to Home Screen”. |
| 添加到桌面 · 鸿蒙 华为浏览器 | 在华为浏览器点右下角菜单，选择「添加到桌面」。 | In Huawei Browser, open the bottom-right menu and choose “Add to desktop”. |
| 添加到桌面 · 微信内 | 请点右上角「···」，选择「在浏览器打开」，再添加到桌面。 | Tap “···” at the top right, choose “Open in browser”, then add it from there. |
| 添加到桌面 · 其他浏览器 | 在浏览器菜单里选择「安装应用」或「添加到主屏幕」。 | Choose “Install app” or “Add to Home Screen” in your browser menu. |
| 添加到桌面 · 关闭 | 知道了 | Got it |
| 离线标记 title | 离线可用 | Works offline |

### 语境卡（view.ts contextCatalog）

| 位置 | 中文 | English |
|---|---|---|
| c0_preparation 标题 | 怎么制作的？ | How was it made? |
| c0_preparation 选项 | 意式萃取 Espresso ｜ 美式 Americano ｜ 奶咖 Milk coffee ｜ 手冲 Pour-over ｜ 挂耳 Drip bag ｜ 摩卡壶 Moka pot ｜ 冷萃 Cold brew ｜ 虹吸壶 Siphon ｜ 冰滴 Cold drip ｜ 法压壶 French press ｜ 土耳其壶 Turkish ｜ 爱乐压 AeroPress | Espresso ｜ Americano ｜ Milk coffee ｜ Pour-over ｜ Drip bag ｜ Moka pot ｜ Cold brew ｜ Siphon ｜ Cold drip ｜ French press ｜ Turkish pot ｜ AeroPress |
| c1_roast 标题 | 烘焙度 | Roast level |
| c1_roast 选项 | 极浅烘 ｜ 浅烘 ｜ 中浅烘 ｜ 中烘 ｜ 中深烘 ｜ 深烘 ｜ 极深烘 | Very light ｜ Light ｜ Medium-light ｜ Medium ｜ Medium-dark ｜ Dark ｜ Very dark |
| c2_variety 标题 | 豆种 | Variety |
| c2_variety 单品 / 拼配 | 单品 SOE ｜ 拼配 Blend | Single origin ｜ Blend |
| c2_variety 选项 | 波本 Bourbon ｜ 卡斯蒂略 Castillo ｜ 卡杜艾 Catuai ｜ 卡杜拉 Caturra ｜ 埃塞原生种 Heirloom ｜ 瑰夏 Gesha ｜ 帕卡马拉 Pacamara ｜ 罗布斯塔 Robusta ｜ SL28 / SL34 ｜ 铁皮卡 Typica | Bourbon ｜ Castillo ｜ Catuai ｜ Caturra ｜ Ethiopian landrace ｜ Gesha ｜ Pacamara ｜ Robusta ｜ SL28 / SL34 ｜ Typica |
| c2_process 标题 | 咖啡豆的处理法 | How the beans were processed |
| c2_process 选项 | 日晒 ｜ 水洗 ｜ 蜜处理 ｜ 半水洗 ｜ 湿刨法 ｜ 厌氧发酵 ｜ 乳酸发酵 ｜ 酒桶发酵 ｜ 低因 | Natural ｜ Washed ｜ Honey ｜ Semi-washed ｜ Wet-hulled ｜ Anaerobic ｜ Lactic fermentation ｜ Barrel-aged ｜ Decaf |
| c2_origin 标题 | 咖啡豆的产地（可选） | Where the beans are from (optional) |
| c2_origin 提示 | 不清楚产地也可以继续。 | Not sure? You can skip this. |
| c2_origin 选项 | 埃塞俄比亚 ｜ 肯尼亚 ｜ 卢旺达 ｜ 坦桑尼亚 ｜ 中国云南 ｜ 印度 ｜ 印尼 ｜ 越南 ｜ 也门 ｜ 菲律宾 ｜ 巴西 ｜ 巴拿马 ｜ 牙买加 ｜ 墨西哥 ｜ 哥伦比亚 ｜ 危地马拉 ｜ 尼加拉瓜 ｜ 洪都拉斯 ｜ 哥斯达黎加 | Ethiopia ｜ Kenya ｜ Rwanda ｜ Tanzania ｜ Yunnan, China ｜ India ｜ Indonesia ｜ Vietnam ｜ Yemen ｜ Philippines ｜ Brazil ｜ Panama ｜ Jamaica ｜ Mexico ｜ Colombia ｜ Guatemala ｜ Nicaragua ｜ Honduras ｜ Costa Rica |

### 再确认 Q6（view.ts）

| 位置 | 中文 | English |
|---|---|---|
| 标题 | 哪些描述更贴近你的感受？ | Which of these are closer to what you tasted? |
| 提交按钮 | 更新风味卡 | Update my card |

### 组件内固定文案

#### 首页 App.vue

| 位置 | 中文 | English |
|---|---|---|
| 两个按钮 | 开始 ｜ 关于 | Start ｜ About |
| 几何图形（三套组合共用一种语言） | 首页：四格邮票带（色底 + 奶白形）；About：六格拼布；风味卡：按所选词特征色的一排小格（四分圆 / 圆 / 半圆 / 三角 / 菱形），形状都在格内 | home: a four-tile stamp band (coloured ground + cream shape); About: a six-tile quilt; card: a row of small tiles in the words' colours (quarter / circle / half / triangle / diamond), every shape inside its box |
| 大标题 | Every taste has its own vocabulary.（taste 五个字母各一种高亮色） | Every taste has its own vocabulary. (the five letters of taste, one bright colour each) |

#### 风味卡 FlavorCard（终卡）

| 位置 | 中文 | English |
|---|---|---|
| 三层 | 上：冲煮 / 烘焙 / 豆种 / 处理 / 产地（只列已填的）；中：风味词等大、一行多个（英文首字母大写），其下一行评价（维度 + 词，至多 3 项）；下：参考风味 · 分组名 ｜ flavorwords。卡片保持接近正方形 | top: Brew / Roast / Variety / Process / Origin (entered only); middle: the words at equal weight, several to a line (capitalised in English), then one line of evaluation pairs (dimension + word, at most 3); bottom: Reference · group ｜ flavorwords. The card stays close to square |

#### 语境卡 ContextSetupCard

| 位置 | 中文 | English |
|---|---|---|
| 小标签 | 这杯咖啡 | This cup |
| 单品 / 拼配切换后缀 | ≤ 3 | ≤ 3 |
| 下一步 / 跳过 / 已选 | 下一步 ｜ 跳过 ｜ 已选 | Next ｜ Skip ｜ chosen |
| 产地分组标题 | 非洲 ｜ 亚洲 ｜ 美洲 | Africa ｜ Asia ｜ Americas |

#### 题卡 QuizCard

| 位置 | 中文 | English |
|---|---|---|
| 小标签 | 这一口 | This cup |
| 选项与小字 | 每题至多 5 个选项（见 7.2）；选项下方一行小字承接答不上来的读者 | five options at most (see 7.2); a quiet line under the options for a reader who cannot answer |
| 进度条 aria | 答题进度：点已答的题可返回修改 ｜ 修改第 n 题 ｜ 回到第 n 题，其余答案不变 ｜ 回到风味描述，答案不变 | Progress: tap an answered question to change it ｜ Change question n ｜ Back to question n, other answers unchanged ｜ Back to the description, answers unchanged |
| 上次的选择 | 上次选的 | your last pick |

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
| 参考行前缀 | 参考风味 | Reference |
| 底部 icon aria | 首页 ｜ 重新体验 ｜ 分享（导出 1200×2500 PNG） | Home ｜ Start over ｜ Share (exports a 1200×2500 PNG) |
| 操作区 aria | 操作 | Actions |
| PNG 上的字（1200×2500 邮票：透明背景、齿孔边，上白下深蓝；不写「风味卡」，没有小标题；布局固定） | FLAVOR WORDS ｜ 五个图形 ｜ 风味词（最大；英文用 Fraunces 300，其余英文不变）｜ No. 序号 · 日期 ｜ flavorwords.com ｜ 评价各行 + 参考风味 ｜ 冲煮 / 烘焙 / 豆种 / 处理 / 产地 ｜ 补充描述（两句，不称「你」，与标语一起贴底）｜ Every taste has its own vocabulary.（一行） | FLAVOR WORDS ｜ five shapes ｜ the words (largest; Fraunces 300 in English, other English unchanged) ｜ No. serial · date ｜ flavorwords.com ｜ evaluation rows + Reference ｜ Brew / Roast / Variety / Process / Origin ｜ supplementary description (two sentences, never "your", anchored to the bottom with the slogan) ｜ Every taste has its own vocabulary. (one line) |

#### 上方堆叠 CollectedStack

| 位置 | 中文 | English |
|---|---|---|
| 勾选卡标题 | 候选风味描述 | Candidate descriptions |
| 收集中 aria | 收集中 | collecting |

#### 机器阅读层（index.html / public）

| 位置 | 中文 | English |
|---|---|---|
| 页面标题 / 描述 | flavorwords — Put this cup into words ｜ Every taste has its own vocabulary. 从酸质、香气与口感开始…… | same; JSON-LD WebApplication, noscript summary, llms.txt, robots, sitemap, humans |
| manifest | flavorwords — Put this cup into words ｜ Every taste has its own vocabulary. A few questions turn what you taste into a flavor card. Works offline. | same |

#### About 抽屉 AboutDrawer（五页）

| 位置 | 中文 | English |
|---|---|---|
| 关闭 aria / 滑动提示 | 关闭 ｜ 向下滑动 | Close ｜ Scroll |
| 展开 / 收起 | 展开 ｜ 收起 | Details ｜ Collapse |
| 第三页导语（无标题） | 十二类风味特征在全部评审记录里的累计权重（对数刻度）；深浅是来源评审族，字母下是各自占比。 | Twelve flavor features by cumulative weight across every review record (log scale); shades are the review panels, the share sits under each letter. |
| 第三页主干 | 8,142 条记录 → 整理为 16 组参考风味 | 8,142 records → organised into 16 reference profiles |
| 第四页标题 | 本项目整理的 16 组参考风味 | 16 reference profiles organised by this project |
| 第四页导语 | 大小按记录数，颜色是该组最强的风味特征；内圈是记录最多的 6 组。白线连到最接近的两组，C1–C6 是最接近的几对。 | Size by records, colour by the group's strongest feature; the inner ring holds the 6 largest. Curves join the two nearest groups, C1–C6 the closest pairs. |
| 第四页环与注释 | 记录最多的 6 组 ｜ 其余 10 组 ｜ 条记录 | the 6 largest ｜ the other 10 ｜ records |
| 来源页（独立一页，右下角 TOP） | 引用与来源 ｜ 本项目的使用 ｜ 链接与条款 ｜ 来源条款 ｜ ↑ TOP | Citations and sources ｜ Use in this project ｜ Link and terms ｜ Source terms ｜ ↑ TOP |
| 来源族名 | CoffeeReview 编辑评审 ｜ Cup of Excellence 评审 ｜ Q-grader 数据集 ｜ 罗布斯塔 Q-grader 评审 ｜ Project Origin 评审 ｜ Cenicafé 受训杯测师 ｜ 印度咖啡局 Fine Cup ｜ 也门 Sheba 拍卖评审 | CoffeeReview editorial reviews ｜ Cup of Excellence juries ｜ Q-grader dataset ｜ Robusta Q-grader panel ｜ Project Origin panel ｜ Cenicafé trained cuppers ｜ Coffee Board of India Fine Cup ｜ Sheba Yemen auction panel |

## 2. 卡片标题、说明标签与差异句（bundle.presentation）

| 位置 | 中文 | English |
|---|---|---|
| 第一次出卡标题 | 这杯咖啡的风味 | This cup's flavor |
| 终卡标题 | 风味卡 | Flavor card |
| 折叠层标题 | 关于这段描述 | About this description |
| 参考资料前缀 | 参考资料： | Reference:  |
| 说明标签 REFERENCE_BASIS | 初始参考 | Initial reference |
| 说明标签 CORPUS_MEASURED | 资料统计 | From the data |
| 说明标签 LITERATURE_CLAIM | 研究参考 | Research reference |
| 说明标签 COMPUTED_DELTA | 你的描述 | Your description |
| 说明标签 PRODUCT_NOTE | 提示 | Note |
| 差异句模板 pos | 相较于初始参考，你的描述中，{label}更突出。 | Compared with the initial reference profile, {label} is more pronounced in your description. |
| 差异句模板 neg | 相较于初始参考，你的描述中，{label}较弱。 | Compared with the initial reference profile, {label} is less pronounced in your description. |
| 纸味 / 陈味组的提示 | 这些描述常与储存或处理有关，值得再喝一口确认。这里不对这杯咖啡做质量判断。 | These descriptions are often linked to storage or processing; worth a second sip to confirm. No quality judgement is made here. |
| 勾选提示（describe） | 选出最贴近你感受的 5 个词。 | Pick the 5 words closest to what you tasted. |

上屏的说明状态：REFERENCE_BASIS, CORPUS_MEASURED, LITERATURE_CLAIM, COMPUTED_DELTA, PRODUCT_NOTE；待补链接或待复核的文献句不上屏。

## 3. 题库 Q0–Q5（bundle.question_bank）

| 题 | 位置 | 中文 | English |
|---|---|---|---|
| Q0 | 提问 | 喝到酸了吗？是哪一种？ | Does it taste sour or tangy? What kind? |
| Q0 | 选项 A | 柑橘 / 青苹果那种酸 | Bright and crisp, like citrus or green apple |
| Q0 | 选项 B | 乳酸 / 发酵果酸（像酸奶、水果黄酒） | Soft and tangy, like yoghurt or fermented fruit |
| Q0 | 选项 C | 酸感不明显 | I don't notice any sourness |
| Q0 | 选项 D | 酸苦，带点刺激 | Sour and bitter together, a little harsh |
| Q1 | 提问 | 闻起来最像什么？ | What does it smell like most? |
| Q1 | 选项 A | 花香、茶感、草本 | Flowers, tea or fresh herbs |
| Q1 | 选项 B | 坚果、烤面包、烤榛果 | Nuts, toast or roasted hazelnut |
| Q1 | 选项 C | 热带水果，带一点微醺酒香 | Tropical fruit with a boozy edge |
| Q1 | 选项 D | 闻不出明显的香气 | I can't pick out a clear aroma |
| Q2 | 提问 | 能喝出甜味吗？更像哪一种？ | Can you taste sweetness? Which kind? |
| Q2 | 选项 A | 清爽的花蜜 / 蔗糖甜 | Light and clean, like nectar or cane sugar |
| Q2 | 选项 B | 浓郁的焦糖 / 黑巧克力 | Rich, like caramel or dark chocolate |
| Q2 | 选项 C | 熟果、果酱那种浓稠的甜 | Thick and jammy, like ripe fruit |
| Q2 | 选项 D | 甜感不明显 | I don't notice much sweetness |
| Q3 | 提问 | 口感如何？ | How does it feel in your mouth? |
| Q3 | 选项 A | 清爽，像绿茶或果汁 | Light, like green tea or juice |
| Q3 | 选项 B | 顺滑，像牛奶或丝绒 | Smooth, like milk or velvet |
| Q3 | 选项 C | 厚重，像黑巧或糖浆 | Heavy, like dark chocolate or syrup |
| Q3 | 选项 D | 发涩，像喝了浓茶 | Drying, like strong black tea |
| Q4 | 提问 | 尾段苦吗？ | Is the aftertaste bitter? |
| Q4 | 选项 A | 微苦，像可可或坚果皮 | A little, like cocoa or nut skins |
| Q4 | 选项 B | 没有明显苦感 | Not really bitter |
| Q4 | 选项 C | 苦得明显，像浓缩或炭烧 | Clearly bitter, like espresso or charred toast |
| Q5 | 提问 | 整体更像哪种？ | Overall, how do the flavors come across? |
| Q5 | 选项 A | 味道混在一起，各种风味都有一点 | Blended together, a bit of everything |
| Q5 | 选项 B | 饱满圆润，一致性很高 | Full and rounded, all of a piece |
| Q5 | 选项 C | 能分清楚多种味道，层次明确 | In clear layers, easy to tell apart |
| Q5 | 选项 D | 感觉不错但说不上来 | Pleasant, but hard to put into words |

### 承接上一题的提问变体（bundle.question_flow.prompt_variants）

第二题起，提问按上一题的回答换一种说法；选项按这杯与已答内容重新排序，「不明显」类永远在最后。

| 题 | 条件 | 中文 | English |
|---|---|---|---|
| Q1 | 上一题 Q0 = A | 柑橘那种酸之后，闻起来最像什么？ | With that citrus-like sourness, what does it smell like most? |
| Q1 | 上一题 Q0 = B | 乳酸那种酸之后，闻起来最像什么？ | With that soft, yoghurt-like tang, what does it smell like most? |
| Q1 | 上一题 Q0 = C | 酸感不明显，那闻起来最像什么？ | Sourness aside, what does it smell like most? |
| Q1 | 上一题 Q0 = D | 酸苦之外，闻起来最像什么？ | Beyond the sour, bitter edge, what does it smell like most? |
| Q2 | 上一题 Q1 = A | 花香之后，能喝出甜味吗？更像哪一种？ | After the floral, tea-like aroma, can you taste sweetness? Which kind? |
| Q2 | 上一题 Q1 = B | 坚果烤香之后，甜味更像哪一种？ | After the nutty, toasty aroma, which kind of sweetness is it? |
| Q2 | 上一题 Q1 = C | 热带果香之后，甜味更像哪一种？ | After the tropical-fruit aroma, which kind of sweetness is it? |
| Q2 | 上一题 Q1 = D | 闻不出香气也没关系，能喝出甜味吗？ | No clear aroma is fine. Can you taste sweetness? |
| Q3 | 上一题 Q2 = A | 清爽的甜之后，口感如何？ | With that light sweetness, how does it feel in your mouth? |
| Q3 | 上一题 Q2 = B | 焦糖黑巧的甜之后，口感如何？ | With that caramel, dark-chocolate sweetness, how does it feel in your mouth? |
| Q3 | 上一题 Q2 = C | 果酱般的甜之后，口感如何？ | With that jammy sweetness, how does it feel in your mouth? |
| Q3 | 上一题 Q2 = D | 甜感不明显的话，口感如何？ | Sweetness aside, how does it feel in your mouth? |
| Q4 | 上一题 Q3 = A | 轻盈的口感，尾段苦吗？ | It feels light. Is the aftertaste bitter? |
| Q4 | 上一题 Q3 = B | 顺滑之后，尾段苦吗？ | It feels smooth. Is the aftertaste bitter? |
| Q4 | 上一题 Q3 = C | 厚重之后，尾段苦吗？ | It feels heavy. Is the aftertaste bitter? |
| Q4 | 上一题 Q3 = D | 发涩之外，尾段苦吗？ | It feels drying. Is the aftertaste bitter? |
| Q5 | 上一题 Q4 = A | 微苦收尾，这一口整体更像哪种？ | With a slightly bitter aftertaste, how do the flavors come across overall? |
| Q5 | 上一题 Q4 = B | 不苦的话，这一口整体更像哪种？ | With no real bitterness, how do the flavors come across overall? |
| Q5 | 上一题 Q4 = C | 苦得明显，这一口整体更像哪种？ | With a clearly bitter aftertaste, how do the flavors come across overall? |

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
| acidity | 酸质 | acidity | 葡萄柚 ｜ 血橙 ｜ 青柠 ｜ 柠檬 ｜ 甜橙 ｜ 佛手柑 ｜ 蜜桔 ｜ 砂糖橘 | grapefruit ｜ blood orange ｜ lime ｜ lemon ｜ sweet orange ｜ bergamot ｜ honey mandarin ｜ sugar mandarin |  | citrus ｜ juicy ｜ tart ｜ crisp ｜ citrusy ｜ tangy ｜ lemony |
| sweetness | 甜感 | sweetness | 蔗糖 ｜ 蜂蜜 ｜ 焦糖 ｜ 花蜜 ｜ 橘子糖 ｜ 黑糖 ｜ 枫糖 ｜ 牛轧糖 ｜ 白巧克力 ｜ 糖蜜 ｜ 香草 | cane sugar ｜ honey ｜ caramel ｜ nectar ｜ mandarin candy ｜ brown sugar ｜ maple syrup ｜ nougat ｜ white chocolate ｜ molasses ｜ vanilla | 冰糖雪梨 ｜ 太妃糖 ｜ 麦芽糖 ｜ 黑糖 ｜ 罗汉果甜 | rock-sugar pear ｜ toffee ｜ maltose ｜ dark brown sugar ｜ monk-fruit sweetness ｜ jam ｜ candy ｜ syrup ｜ jammy |
| body | 醇厚度 | body | 丝绒奶油 ｜ 慕斯 ｜ 奶油 | velvet cream ｜ mousse ｜ cream |  | silky |
| floral | 花香 | floral | 茉莉花 ｜ 玉兰花 ｜ 橙花 ｜ 咖啡花 ｜ 金银花 ｜ 山茶花 ｜ 玫瑰 ｜ 姜花 ｜ 洋甘菊 | jasmine ｜ magnolia ｜ orange blossom ｜ coffee blossom ｜ honeysuckle ｜ camellia ｜ rose ｜ ginger lily ｜ chamomile | 桂花 ｜ 栀子花 ｜ 咖啡花 ｜ 白兰花 ｜ 洋甘菊 | osmanthus ｜ gardenia ｜ coffee blossom ｜ white magnolia ｜ chamomile ｜ floral ｜ tea-like |
| fruity | 果香 | fruity | 水蜜桃 ｜ 黄桃 ｜ 黑加仑 ｜ 杏桃 ｜ 蔓越莓 ｜ 蓝莓 ｜ 草莓 ｜ 葡萄 ｜ 白葡萄 ｜ 蜜瓜 ｜ 凤梨 ｜ 荔枝 ｜ 秋月梨 ｜ 白桃 ｜ 车厘子 ｜ 树莓 ｜ 黑莓 ｜ 石榴 ｜ 李子 ｜ 苹果 ｜ 芒果 ｜ 香蕉 ｜ 椰子 ｜ 葡萄干 ｜ 西梅 | peach ｜ yellow peach ｜ blackcurrant ｜ apricot ｜ cranberry ｜ blueberry ｜ strawberry ｜ grape ｜ white grape ｜ melon ｜ pineapple ｜ lychee ｜ Akizuki pear ｜ white peach ｜ cherry ｜ raspberry ｜ blackberry ｜ pomegranate ｜ plum ｜ apple ｜ mango ｜ banana ｜ coconut ｜ raisin ｜ prune | 巨峰葡萄 ｜ 荔枝 ｜ 杨梅 ｜ 西梅 ｜ 青梅 ｜ 红心芭乐 | Kyoho grape ｜ lychee ｜ bayberry ｜ prune ｜ green plum ｜ pink guava ｜ berry ｜ berries ｜ stone fruit ｜ tropical ｜ melon |
| nutty_chocolate | 坚果巧克力 | nutty & chocolate | 烤榛果 ｜ 可可 ｜ 提拉米苏 ｜ 曲奇饼干 ｜ 牛奶巧克力 ｜ 榛果巧克力 ｜ 巧克力酱 ｜ 杏仁 ｜ 花生 ｜ 核桃 ｜ 吐司 ｜ 麦芽 | roasted hazelnut ｜ cocoa ｜ tiramisu ｜ butter cookie ｜ milk chocolate ｜ hazelnut chocolate ｜ chocolate sauce ｜ almond ｜ peanut ｜ walnut ｜ toast ｜ malt |  | chocolate |
| fermented_winey | 发酵与酒香 | fermented & winey | 朗姆酒 ｜ 红酒 ｜ 酒酿 | rum ｜ red wine ｜ jiuniang | 米酒 ｜ 酒酿 ｜ 酒酿圆子 ｜ 黄酒 ｜ 热带水果发酵酱 ｜ 水果黄酒 ｜ 威士忌桶 ｜ 雪莉桶 ｜ 野果发酵 ｜ 微醺酒香 ｜ 苹果酒感 ｜ 水果发酵酱 ｜ 朗姆酒香 | rice wine ｜ jiuniang (sweet fermented rice) ｜ jiuniang rice balls ｜ huangjiu ｜ tropical fruit ferment ｜ fruit huangjiu ｜ whisky barrel ｜ sherry cask ｜ funky ｜ wine ｜ cider ｜ fermented ｜ winey |
| bitter_roasted | 烘烤苦感 | roast & bitter | 黑巧克力 ｜ 烟熏可可 ｜ 炭烧 | dark chocolate ｜ smoky cocoa ｜ charred | 烤杏仁 ｜ 烘焙麦芽 ｜ 黑芝麻 ｜ 松露巧克力 | roasted almond ｜ roasted malt ｜ black sesame ｜ truffle chocolate ｜ smokey ｜ roasted ｜ dark roast ｜ ashy |
| spice | 香料 | spice | 肉桂 ｜ 丁香 ｜ 小豆蔻 ｜ 生姜 ｜ 八角 ｜ 肉豆蔻 | cinnamon ｜ clove ｜ cardamom ｜ ginger ｜ star anise ｜ nutmeg |  |  |
| herbal_green | 草本绿茶 | herbal & green | 茉莉绿茶 ｜ 高山乌龙 ｜ 柠檬草 ｜ 伯爵茶 ｜ 红茶 ｜ 薄荷 | jasmine green tea ｜ high-mountain oolong ｜ lemongrass ｜ Earl Grey tea ｜ black tea ｜ mint | 高山龙井 ｜ 武夷岩茶 ｜ 鸭屎香 ｜ 普洱茶韵 | high-mountain Longjing ｜ Wuyi rock tea ｜ Ya Shi Xiang (Dancong) ｜ Pu'er tea finish ｜ tea ｜ grass ｜ grassy ｜ herbal |
| woody_earthy | 木质泥土 | woody & earthy | 风干雪松 ｜ 泥炭 ｜ 松露 ｜ 杉木 ｜ 烟草 ｜ 柏木 ｜ 橡木 ｜ 檀香 ｜ 松木 ｜ 桦木 ｜ 干燥树皮 ｜ 沉香 | aged cedar ｜ peat ｜ truffle ｜ fir wood ｜ tobacco ｜ cypress ｜ oak ｜ sandalwood ｜ pine ｜ birch ｜ dry bark ｜ agarwood |  |  |
| defect | 瑕疵 | defect | 纸味 ｜ 陈味 ｜ 霉味 | papery ｜ stale ｜ musty |  |  |

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
| ginger | 生姜 | ginger |
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

## 7. 关于这段描述（折叠层里的句子）

标签为「（不上屏）」的行不出现在产品里：owner 自建的成因句是项目规则（在 About 的「初始参考如何形成」里解释），待复核的文献句撤下。

| 语境 | 标签 | 中文 | English | 出处 |
|---|---|---|---|---|
| 初始参考句模板 | 初始参考 | 根据{context}，初始参考侧重{dims}。 初始参考来自评审资料的统计，只是起点，不是这杯咖啡的测定。 | From {context}, the initial reference leans toward {dims}. It comes from the review data and is a starting point, not a measurement of this cup. | engine |
| C0_ESPRESSO | （不上屏：OWNER_STATEMENT） | 意式浓缩放大醇厚度与油脂，前段高挥发花果香被压缩。 | Espresso amplifies body and oils; the volatile floral and fruit top notes are compressed. | owner |
| C0_COLD_BREW | （不上屏：OWNER_STATEMENT） | 冷萃抑制低挥发酸，酸质与花香偏弱，甜感与醇厚更突出。 | Cold brew suppresses the low-volatility acids: less acidity and floral lift, more sweetness and body. | owner |
| C0_V60 | （不上屏：OWNER_STATEMENT） | 手冲常见的表现是花香与果酸更清晰，醇厚较轻。 | Pour-over tends to show florals and fruit acidity more clearly, with a lighter body. | owner |
| C0_FRENCH_PRESS | （不上屏：OWNER_STATEMENT） | 浸泡式萃取带入更多油脂与细粉，醇厚度上升，干净度下降。 | Immersion brewing carries more oils and fines: more body, less clarity. | owner |
| C1_LIGHT | （不上屏：OWNER_STATEMENT） | 浅烘保留更多绿原酸与高挥发香气，酸质与花果香突出。 | Light roasts keep more chlorogenic acids and volatile aromatics: acidity and floral-fruit notes lead. | owner |
| C1_MEDIUM_LIGHT | （不上屏：OWNER_STATEMENT） | 中浅烘保留花果酸质，同时开始形成焦糖化甜感。 | Medium-light roasts keep the floral-fruit acidity while caramelisation sweetness begins. | owner |
| C1_MEDIUM | （不上屏：OWNER_STATEMENT） | 中烘平衡酸质与美拉德产物，坚果与焦糖增强。 | Medium roasts balance acidity against Maillard products: nut and caramel rise. | owner |
| C1_MEDIUM_DARK | （不上屏：OWNER_STATEMENT） | 中深烘美拉德产物占比高，醇厚度、巧克力与苦感上升，酸质下降。 | Medium-dark roasts are Maillard-dominated: body, chocolate and bitterness rise, acidity falls. | owner |
| C1_DARK | （不上屏：OWNER_STATEMENT） | 深烘绿原酸大量降解，焦糖苦与烟熏占主导。 | Dark roasts degrade most chlorogenic acids: caramelised bitterness and smoke dominate. | owner |
| C1_VERY_DARK | （不上屏：OWNER_STATEMENT） | 极深烘以碳化与烟熏为主，品种与产地特征基本被覆盖。 | Very dark roasts are carbonised and smoky; origin and variety character is mostly covered. | owner |
| C2_process_WASHED | （不上屏：OWNER_STATEMENT） | 水洗去胶质快，内源有机酸突出：干净度高、柑橘、花香、高酸。 | Washed processing removes mucilage quickly; the bean's own organic acids stand out: clean, citrus, floral, high acidity. | owner |
| C2_process_NATURAL | （不上屏：OWNER_STATEMENT） | 日晒让果肉糖分在发酵中渗入豆内，还原糖与游离氨基酸升高：果酱、热带水果、高甜。 | Natural processing lets fruit sugars ferment into the seed: more reducing sugars and free amino acids — jam, tropical fruit, high sweetness. | owner |
| C2_process_ANAEROBIC | （不上屏：OWNER_STATEMENT） | 厌氧发酵常带来更多乳酸与酯类风味：酸奶感与酒香。 | Anaerobic fermentation tends to add lactic and ester notes: yoghurt and winey character. | owner |
| C2_process_HONEY | （不上屏：OWNER_STATEMENT） | 蜜处理保留部分果胶发酵，甜感与醇厚介于水洗与日晒之间。 | Honey processing keeps part of the mucilage: sweetness and body between washed and natural. | owner |
| C2_process_DECAF | （不上屏：OWNER_STATEMENT） | 脱因工艺去除部分前体物质，香气强度整体下降。 | Decaffeination removes some precursors; aroma intensity drops overall. | owner |
| C2_variety_GESHA | （不上屏：OWNER_STATEMENT） | 瑰夏常见茉莉、白花与柑橘酸质，醇厚偏轻。 | Gesha commonly shows jasmine, white florals and citrus acidity with a lighter body. | owner |
| C2_variety_BOURBON | （不上屏：OWNER_STATEMENT） | 波本甜感与平衡度好，焦糖与红果常见。 | Bourbon is sweet and balanced; caramel and red fruit are typical. | owner |
| C2_variety_SL28_SL34 | （不上屏：OWNER_STATEMENT） | SL28/SL34 以黑加仑与明亮柑橘酸质著称。 | SL28/SL34 are known for blackcurrant and bright citric acidity. | owner |
| C2_variety_ETHIOPIAN_LANDRACE | （不上屏：OWNER_STATEMENT） | 埃塞原生种以茉莉花、柑橘与蓝莓（日晒）为标志。 | Ethiopian landraces are marked by jasmine, citrus and, when natural, blueberry. | owner |
| C2_variety_TYPICA | （不上屏：OWNER_STATEMENT） | 铁皮卡干净、甜感柔和，醇厚适中。 | Typica is clean and gently sweet with moderate body. | owner |
| C2_variety_ROBUSTA | （不上屏：OWNER_STATEMENT） | 罗布斯塔前体糖分低、绿原酸与咖啡因高：苦感与醇厚重，花果弱。 | Robusta has low sugar precursors and high chlorogenic acid and caffeine: heavy bitterness and body, little floral-fruit. | owner |
| C0_V60__C1_LIGHT | （不上屏：OWNER_STATEMENT） | 浅烘保留了更多绿原酸与挥发性花果香，手冲又让这些花香与果酸更清晰。 | Light roast keeps more chlorogenic acids and volatile floral-fruit aromatics, and pour-over lets those florals and acids read clearly. | owner |
| C0_ESPRESSO__C1_MEDIUM_DARK | （不上屏：OWNER_STATEMENT） | 中深烘的美拉德产物在意式高压下被油脂放大：黑巧、焦糖与厚重口感主导，酸质退到后段。 | Medium-dark Maillard products are amplified by espresso pressure and oils: dark chocolate, caramel and weight lead; acidity retreats. | owner |
| C0_COLD_BREW__C1_LIGHT | （不上屏：OWNER_STATEMENT） | 冷萃压低了浅烘的低挥发酸，花香减弱、甜感与茶感更清晰。 | Cold brew flattens the light roast's low-volatility acids: less floral lift, clearer sweetness and tea-like body. | owner |
| C1_LIGHT__C2_process_WASHED | （不上屏：OWNER_STATEMENT） | 浅烘 + 水洗保留了柠檬酸与高极性酯类：柑橘、茉莉与干净的酸质。 | Light roast plus washed processing keeps citric acid and polar esters: citrus, jasmine and clean acidity. | owner |
| C1_LIGHT__C2_process_NATURAL | （不上屏：OWNER_STATEMENT） | 浅烘 + 日晒把发酵进豆内的果糖与酯类完整保留：蓝莓、果酱与高甜。 | Light roast plus natural processing keeps the fermented fruit sugars and esters: blueberry, jam and high sweetness. | owner |
| C1_MEDIUM_DARK__C2_process_ANAEROBIC | （不上屏：OWNER_STATEMENT） | 中深烘 + 厌氧常见的表现是黑巧与发酵感并存；若你尝到的酸质更高，与这个组合的常见表现不同。 | Medium-dark plus anaerobic usually reads as dark chocolate with fermentation; a brighter acidity differs from the usual pattern for this combination. | owner |
| C1_VERY_LIGHT | （不上屏：OWNER_STATEMENT） | 极浅烘几乎不动豆子的原始结构：绿原酸与挥发性花果香保留最完整，酸质最突出，甜感与醇厚尚未展开。 | A very light roast barely touches the bean's original structure: chlorogenic acids and volatile florals stay almost intact, acidity is at its most pronounced, sweetness and body have not opened yet. | owner |
| C0_POUR_OVER_V60 | 研究参考 | 粉床细粉迁移引发微观通道效应时，局部过萃会导致中段甜感中断，并在余韵中引入涩感与杂味。 | When fines migrate and open micro-channels in the bed, local over-extraction breaks the mid-palate sweetness and brings astringency and off-notes into the finish. | Coffee Ad Astra (Jonathan Gagné) |
| C0_POUR_OVER_V60__C1_LIGHT | 研究参考 | 浅烘手冲时，萃取率落在合适区间才有饱满的中段甜感；萃取率不足则酸而空，过高则涩。 | For light roasts on pour-over, mid-palate sweetness fills in only inside the right extraction-yield window; under-extraction reads sour and hollow, over-extraction astringent. | Coffee Ad Astra (Jonathan Gagné) |
| C0_ESPRESSO__C1_MEDIUM_DARK | 研究参考 | 中深烘意式在高压下通道效应更敏感：粉饼不均会同时出现欠萃的酸与过萃的苦。 | Medium-dark espresso is more sensitive to channeling under pressure: an uneven puck shows under-extracted sourness and over-extracted bitterness at once. | Coffee Ad Astra (Jonathan Gagné) |
| C0_POUR_OVER_V60 | （不上屏：LITERATURE_CLAIM_NEEDS_REVERIFICATION） | 快萃与较高水温优先溶解极性较高的有机酸分子，前段酸质与花果香先被释放。 | Fast extraction at higher water temperature dissolves the more polar organic acids first, so acidity and floral-fruit notes lead. | UC Davis Coffee Center |
| C0_ESPRESSO | （不上屏：LITERATURE_CLAIM_NEEDS_REVERIFICATION） | 研磨度过细会加速大分子绿原酸内酯的释放，从而增加尾段苦感；高压萃取同时带出更多油脂与醇厚度。 | Too fine a grind accelerates the release of large chlorogenic-acid lactones and adds late bitterness; pressure extraction also carries more oils and body. | UC Davis Coffee Center |
| C0_COLD_BREW | （不上屏：LITERATURE_CLAIM_NEEDS_REVERIFICATION） | 低温长时萃取下，挥发性酸与酸质通常更弱，感官图谱偏向甜感与圆润。 | Under long, cold extraction the volatile acids and acidity are usually weaker; the sensory map shifts toward sweetness and roundness. | UC Davis Coffee Center |
| C0_FRENCH_PRESS | （不上屏：LITERATURE_CLAIM_NEEDS_REVERIFICATION） | 浸泡式萃取与金属滤网让更多细粉与油脂进入杯中，醇厚度上升、干净度下降。 | Immersion brewing through a metal filter passes more fines and oils: more body, less clarity. | UC Davis Coffee Center |
| C2_variety_GESHA | （不上屏：LITERATURE_CLAIM_NEEDS_REVERIFICATION） | 瑰夏（Gesha）基因决定了其高挥发性单萜烯（如芳樟醇）的高表达上限，浅烘焙下呈现高锐白花与单醇果酸。 | The Gesha genotype sets a high ceiling for volatile monoterpenes such as linalool; at light roast it reads as sharp white florals and clean, single-note fruit acidity. | World Coffee Research |
| C1_LIGHT | 研究参考 | 浅烘保留品种的花香与果酸参照物（花香、柑橘酸、单醇甜感），焦糖化产物尚未主导。 | Light roasting keeps the variety's floral and fruit-acid references (florals, citric acidity, clean sweetness) before caramelisation products take over. | World Coffee Research |
| C1_MEDIUM | 研究参考 | 中烘时焦糖化与美拉德参照物（红糖、坚果、可可）与残余果酸达到平衡。 | At medium roast the caramelisation and Maillard references (brown sugar, nut, cocoa) balance the remaining fruit acidity. | World Coffee Research |
| C1_DARK | 研究参考 | 深烘下花香与果酸参照物被烘烤参照物（烟熏、焦糖苦、灰烬）覆盖。 | At dark roast the floral and fruit-acid references are covered by roast references (smoke, burnt caramel, ash). | World Coffee Research |

### 7.1 卡片说明的句式（card_notes，2026-09-18；2026-09-19 改写）

「关于这段描述」里三类说明的全部句式。每个句式中英各三种说法、位置一一对应；引擎用与语言无关的种子选同一个序号，所以同一张卡在两种语言里说的是同一件事、同一组数字。数字来自评审资料的出现比例（corpus_stats）。
2026-09-19（owner）：资料统计只出一条，取最能说明问题的那一个统计；只用平常话给结论（「比一般咖啡更常见 / 差不多 / 更少见」），不出现任何数字——2026-09-20（owner）：「738 款中每 10 款约 4 款…平均约 3 款」会让读者觉得信息被过度平均、怀疑过拟合；「更常 / 更少」需要至少 10 个点的差距。初始参考同样只说方向，不带数字。

| 句式 | 中文 | English |
|---|---|---|
| 初始参考：句子框架 · 1 | 评审记录里，和一般咖啡相比，{clauses}。 | In the review records, compared with coffee generally, {clauses}. |
| 初始参考：句子框架 · 2 | 从评审记录看，和一般咖啡相比，{clauses}。 | Going by the review records, and compared with coffee generally, {clauses}. |
| 初始参考：句子框架 · 3 | 和评审记录里的全部咖啡相比，{clauses}。 | Set against all the coffees in the review records, {clauses}. |
| 初始参考分句：更常 + 更少 | {option}的咖啡更常写到{up}、更少写到{down} | {option} coffees are described with {up} more often and with {down} less often |
| 初始参考分句：更常 | {option}的咖啡更常写到{up} | {option} coffees are described with {up} more often |
| 初始参考分句：更少 | {option}的咖啡更少写到{down} | {option} coffees are described with {down} less often |
| 频率 | 每 {base} 款约 {k} 款 | about {k} in {base} |
| 频率（同一句里第二次） | 约 {k} 款 | about {k} |
| 频率：不足 1 | 每 {base} 款不到 1 款 | fewer than 1 in {base} |
| 频率（第二次）：不足 1 | 不到 1 款 | fewer than 1 |
| 初始参考：与一般咖啡接近 · 1 | 你选的{options}在评审记录里很常见，风味和一般咖啡差别不大：初始参考接近一杯典型的咖啡，最常被写到的是{dims}。 | What you chose ({options}) is common in the review records and differs little from coffee generally: the initial reference is close to a typical cup, where {dims} come up most. |
| 初始参考：与一般咖啡接近 · 2 | {options}是评审记录里常见的组合，和所有咖啡相比没有明显偏向，最常被写到的是{dims}。 | {options} is a common combination in the review records with no clear lean against all coffees; {dims} come up most. |
| 初始参考：与一般咖啡接近 · 3 | 评审记录里，{options}的咖啡与一般咖啡很接近，初始参考因此偏向常见的{dims}。 | In the review records, {options} coffees sit close to coffee generally, so the initial reference leans toward the usual {dims}. |
| 初始参考：没有可用记录 · 1 | 这组选择在评审资料里没有足够的记录，这张卡主要依据你自己的回答。 | The review data has too few records for these choices, so this card rests mainly on your own answers. |
| 初始参考：没有可用记录 · 2 | 评审资料里没有足够的记录能对应这组选择，描述主要来自你的回答。 | There are not enough review records to match these choices; the description comes mainly from your answers. |
| 初始参考：没有可用记录 · 3 | 这组选择缺少可用的评审记录，初始参考很弱，描述以你的回答为主。 | These choices lack usable review records: the initial reference is weak and the description follows your answers. |
| 初始参考：未计入的选项 · 1 | {options}没有足够的评审记录，没有计入初始参考。 | The initial reference leaves out {options}, for which there are too few review records. |
| 初始参考：未计入的选项 · 2 | 评审资料里{options}的记录太少，初始参考没有用到。 | The review data has too few records for {options}, so the initial reference does not count it. |
| 初始参考：未计入的选项 · 3 | {options}缺少评审记录，初始参考里不含这一项。 | Not counted in the initial reference, for lack of review records: {options}. |
| 资料统计：支持确认的词 · 1 | 你确认的{words}属于{dim}，评审记录里{scope}的咖啡也比一般咖啡更常被这样描述。 | You confirmed {words} ({dim}). In the review records, {scope} coffees are described this way more often than coffee generally. |
| 资料统计：支持确认的词 · 2 | 评审记录里，{scope}的咖啡比一般咖啡更常写到{dim}；你确认的{words}就属于这一类。 | In the review records, {scope} coffees are described with {dim} more often than coffee generally. This covers {words}, which you confirmed. |
| 资料统计：支持确认的词 · 3 | {dim}在{scope}的咖啡里比一般咖啡更常见，这与你确认的{words}一致。 | {scope} coffees are described with {dim} more often than coffee generally, in line with {words}, which you confirmed. |
| 资料统计：与一般咖啡相当 · 1 | 你确认的{words}属于{dim}；在这一点上，评审记录里{scope}的咖啡和一般咖啡差不多。 | You confirmed {words} ({dim}). Here, in the review records, {scope} coffees are much like coffee generally. |
| 资料统计：与一般咖啡相当 · 2 | 评审记录里，{scope}的咖啡写到{dim}的情况和一般咖啡差不多；你确认的{words}属于这一类。 | In the review records, {scope} coffees are described with {dim} about as often as coffee generally. This covers {words}, which you confirmed. |
| 资料统计：与一般咖啡相当 · 3 | {dim}在{scope}的咖啡里和一般咖啡差不多常见；你确认的{words}属于这一类。 | {scope} coffees are described with {dim} about as often as coffee generally; this covers {words}, which you confirmed. |
| 资料统计：与这类咖啡的常态不同 · 1 | 你确认的{words}属于{dim}，评审记录里{scope}的咖啡比一般咖啡更少被这样描述：这部分更多来自你自己这一杯的感受。 | You confirmed {words} ({dim}). In the review records, {scope} coffees are described this way less often than coffee generally: this part comes more from your own cup. |
| 资料统计：与这类咖啡的常态不同 · 2 | 评审记录里，{scope}的咖啡比一般咖啡更少写到{dim}；你确认的{words}来自你这一杯的感受，而不是这类咖啡的常态。 | In the review records, {scope} coffees are described with {dim} less often than coffee generally. What you confirmed ({words}) comes from your cup, not from what is usual for this kind of coffee. |
| 资料统计：与这类咖啡的常态不同 · 3 | {dim}在{scope}的咖啡里比一般咖啡少见；你确认的{words}是你这一杯自己的特点。 | {scope} coffees are described with {dim} less often than coffee generally; what you confirmed ({words}) is this cup's own. |
| 你的描述：有升有降 · 1 | 和初始参考相比，你的回答让{raised}更突出，{lowered}更淡。 | Compared with the initial reference, your answers bring out {raised} and tone down {lowered}. |
| 你的描述：有升有降 · 2 | 你的回答把{raised}拉高了，{lowered}则比初始参考弱。 | Your answers raised {raised}, with {lowered} weaker than in the initial reference. |
| 你的描述：有升有降 · 3 | 相较于初始参考，这一杯在你的回答里更偏{raised}，{lowered}没有那么明显。 | Against the initial reference, this cup leans toward {raised} in your answers, with {lowered} less evident. |
| 你的描述：只有上升 · 1 | 和初始参考相比，你的回答让{raised}更突出。 | Compared with the initial reference, your answers bring out {raised}. |
| 你的描述：只有上升 · 2 | 你的回答把{raised}拉高了，其余与初始参考接近。 | Your answers raised {raised}; the rest stays close to the initial reference. |
| 你的描述：只有上升 · 3 | 相较于初始参考，这一杯在你的回答里更偏{raised}。 | Against the initial reference, this cup leans toward {raised} in your answers. |
| 你的描述：只有下降 · 1 | 和初始参考相比，你的回答里{lowered}更淡，其余接近。 | Compared with the initial reference, your answers tone down {lowered}; the rest is close. |
| 你的描述：只有下降 · 2 | 你的回答里{lowered}比初始参考弱，其余与它接近。 | Your answers put {lowered} below the initial reference; the rest stays close to it. |
| 你的描述：只有下降 · 3 | 相较于初始参考，这一杯的{lowered}在你的回答里没有那么明显。 | Against the initial reference, your answers show less of {lowered}. |
| 你的描述：接近初始参考 · 1 | 你的回答与初始参考接近，没有明显偏向。 | Your answers stay close to the initial reference, with no clear lean. |
| 你的描述：接近初始参考 · 2 | 你的回答和初始参考基本一致。 | Your answers and the initial reference largely agree. |
| 你的描述：接近初始参考 · 3 | 这一杯在你的回答里与初始参考相差不大。 | In your answers this cup differs little from the initial reference. |
| 你的描述：词的来源（两类） · 1 | 卡上的词里，{own}来自这一偏向，{shared}与初始参考一致。 | On the card, that lean accounts for {own}; the initial reference already pointed to {shared}. |
| 你的描述：词的来源（两类） · 2 | {own}是你的回答带来的，{shared}则在初始参考里就有。 | Your answers brought {own}; the initial reference already had {shared}. |
| 你的描述：词的来源（两类） · 3 | 其中{own}出自你的回答，{shared}与初始参考相符。 | Owed to your answers: {own}. Shared with the initial reference: {shared}. |
| 你的描述：词来自回答 · 1 | 卡上的词里，{own}来自这一偏向。 | On the card, that lean accounts for {own}. |
| 你的描述：词来自回答 · 2 | {own}是你的回答带来的。 | Your answers brought {own}. |
| 你的描述：词来自回答 · 3 | 其中{own}出自你的回答。 | Owed to your answers: {own}. |
| 你的描述：词与初始参考一致 · 1 | 卡上的词里，{shared}与初始参考一致。 | On the card, the initial reference already pointed to {shared}. |
| 你的描述：词与初始参考一致 · 2 | {shared}在初始参考里就有。 | The initial reference already had {shared}. |
| 你的描述：词与初始参考一致 · 3 | 其中{shared}与初始参考相符。 | Shared with the initial reference: {shared}. |
| 你的描述：第二次确认 · 1 | 第二次确认又强调了{dims}。 | The second look stressed {dims} further. |
| 你的描述：第二次确认 · 2 | 再看一眼时，你进一步选了{dims}。 | On the second look you went on to choose {dims}. |
| 你的描述：第二次确认 · 3 | 第二轮里你把{dims}又往前推了一步。 | In the second round you pushed {dims} a step further. |
| 导出卡补充描述：有升有降 | 比同类咖啡的参考风味更偏{raised}，{lowered}更淡。 | Compared with the reference for this kind of coffee: more {raised}; less {lowered}. |
| 导出卡补充描述：只有上升 | 比同类咖啡的参考风味更偏{raised}。 | Compared with the reference for this kind of coffee: more {raised}. |
| 导出卡补充描述：只有下降 | {lowered}比同类咖啡的参考风味更淡。 | Compared with the reference for this kind of coffee: less {lowered}. |
| 导出卡补充描述：接近参考 | 与同类咖啡的参考风味接近。 | Close to the reference for this kind of coffee. |
| 导出卡补充描述：词的来源（两类） | {own}来自这一偏向，{shared}则与参考风味一致。 | That lean accounts for {own}; in line with the reference: {shared}. |
| 导出卡补充描述：词来自这一偏向 | {own}来自这一偏向。 | That lean accounts for {own}. |
| 导出卡补充描述：词与参考一致 | {shared}与参考风味一致。 | In line with the reference: {shared}. |
| 资料统计：同烘焙度内的香气 / 余韵对照 · 1 | 你觉得{what}明显；评审记录里，{scope}的咖啡在同样烘焙度的咖啡中{what}也更常得到高分。 | You found the {what} clear; in the review records {scope} coffees are scored high for {what} more often than other coffees of the same roast. |
| 资料统计：同烘焙度内的香气 / 余韵对照 · 2 | 评审记录里，{scope}的咖啡比同样烘焙度的咖啡更常因{what}得到高分，与你的回答一致。 | In the review records, {scope} coffees are scored high for {what} more often than other coffees of the same roast, in line with your answer. |
| 资料统计：同烘焙度内的香气 / 余韵对照 · 3 | {what}是{scope}的咖啡在评审里常得高分的一项，你的回答也是如此。 | {what} is something {scope} coffees are often scored high for in the reviews, and your answer agrees. |
| 对照里的「香气」 | 香气 | aroma |
| 对照里的「余韵」 | 余韵 | aftertaste |
| 对照里的「意式」 | 意式 | espresso |

### 7.2 动态题库（dynamic_bank，R3-D40 / R3-D44）

应用现在运行的题目。每题至多显示 5 个选项：语料只剪枝（留下这类咖啡最常见的 4 个），不排序；第五个选项写清楚「不突出」；选项下方一行小字承接答不上来的读者。同一个选项的几种说法用「 ‖ 」分开，由会话种子选定、中英文取同一个序号；标签里的 {examples} 由该类咖啡语料里最常见的两三个词填入。源文件：`db/data/product-vector-v1/DYNAMIC_QUESTION_BANK.tsv`。

| 项 | 中文 | English |
|---|---|---|
| **核心 1 · 酸与水果** · 题面 | 喝到酸了吗？更像哪一类水果的酸？ | Does it taste sour or tangy? Which fruit is it closest to? |
| A1 | 柑橘：{examples}那种　〔承接语：柑橘那种酸之后，〕 | Citrus: like {examples}  [lead-in: After that citrus acidity, ] |
| A2 | 莓果：{examples}那种　〔承接语：莓果那种酸之后，〕 | Berries: like {examples}  [lead-in: After that berry-like acidity, ] |
| A3 | 核果：{examples}那种　〔承接语：核果那种酸之后，〕 | Stone fruit: like {examples}  [lead-in: After that stone-fruit acidity, ] |
| A4 | 苹果、梨、葡萄那种清爽的酸甜　〔承接语：苹果、葡萄那种清爽的酸之后，〕 | Apple, pear or grape: crisp and lightly sweet  [lead-in: After that crisp apple-and-grape acidity, ] |
| A5 | 热带水果：{examples}那种　〔承接语：热带水果那种酸甜之后，〕 | Tropical fruit: like {examples}  [lead-in: After that tropical fruit, ] |
| A6 | 果干：葡萄干、西梅那种带甜的酸　〔承接语：果干那种带甜的酸之后，〕 | Dried fruit: like raisin or prune, sweet and sour  [lead-in: After that dried-fruit tang, ] |
| A7 | 发酵的酸：像酸奶、红酒、酒酿　〔承接语：发酵的酸之后，〕 | Fermented: like yoghurt, red wine or rice wine  [lead-in: After that fermented acidity, ] |
| A8 | 尖酸，有点刺激　〔承接语：尖酸之后，〕 | Sharp and sour, a little harsh  [lead-in: After that sharp sourness, ] |
| A0（第五个选项） | 酸不突出，整体圆润 ‖ 几乎喝不出酸，整体很柔和 ‖ 酸融在整体里，不单独显出来　〔承接语：酸不突出的话，〕 | Acidity doesn't stand out; the cup feels round ‖ Hardly any acidity; the cup is soft overall ‖ The acidity sits inside the whole and never comes forward  [lead-in: With the acidity in the background, ] |
| A-（下方小字） | 这一项很难形容 ‖ 这一项我说不上来 ‖ 我恐怕很难准确回答 | This one is hard to describe ‖ I can't put this one into words ‖ I'm afraid I can't answer this accurately |
| **核心 2 · 香气主调** · 题面 | 除了酸，闻起来、喝起来最像哪一类？（承接上一题时：……，闻起来、喝起来最像哪一类？） | Apart from that, what does it smell and taste most like? (after a lead-in: … what does it smell and taste most like?) |
| B1 | 花：{examples}　〔承接语：花香之后，〕 | Flowers: {examples}  [lead-in: After the floral notes, ] |
| B2 | 茶：红茶、绿茶、乌龙　〔承接语：茶感之后，〕 | Tea: black, green or oolong  [lead-in: After the tea notes, ] |
| B3 | 草本：薄荷、柠檬草　〔承接语：草本的香气之后，〕 | Herbs: mint, lemongrass  [lead-in: After the herbal notes, ] |
| B4 | 坚果：{examples}　〔承接语：坚果的香气之后，〕 | Nuts: {examples}  [lead-in: After the nutty notes, ] |
| B5 | 巧克力、可可　〔承接语：巧克力的香气之后，〕 | Chocolate, cocoa  [lead-in: After the chocolate notes, ] |
| B6 | 烤面包、谷物、麦芽　〔承接语：烤面包、谷物的香气之后，〕 | Toast, grain, malt  [lead-in: After the toasty, grainy notes, ] |
| B7 | 香料：肉桂、丁香、八角　〔承接语：香料的香气之后，〕 | Spice: cinnamon, clove, star anise  [lead-in: After the spice, ] |
| B8 | 木头：雪松、柏木、橡木　〔承接语：木头的香气之后，〕 | Wood: cedar, cypress, oak  [lead-in: After the woody notes, ] |
| B9 | 烟熏、炭烧、烟草　〔承接语：烟熏的香气之后，〕 | Smoke, char, tobacco  [lead-in: After the smoky notes, ] |
| B10（常驻） | 水果：果香最突出　〔承接语：果香最突出的话，〕 | Fruit: fruit is what stands out  [lead-in: With fruit standing out, ] |
| B0（下方小字） | 香气是一个整体，没有哪一类特别突出 ‖ 各种香气融在一起，没有主调 ‖ 闻起来很完整，挑不出最突出的一类　〔承接语：香气没有主调的话，〕 | The aroma comes as a whole; nothing stands out ‖ The aromas blend together with no main note ‖ It smells complete; no single kind leads  [lead-in: With no single aroma leading, ] |
| **核心 3 · 甜** · 题面 | 能喝出甜吗？更像哪一种甜？（承接上一题时：……，能喝出甜吗？更像哪一种甜？） | Can you taste sweetness? What kind? (after a lead-in: … can you taste sweetness? What kind?) |
| C1 | 蜂蜜、花蜜　〔承接语：蜂蜜那种甜之后，〕 | Honey, nectar  [lead-in: After that honeyed sweetness, ] |
| C2（浅烘默认显示） | 蔗糖、冰糖那种清甜　〔承接语：清爽的甜之后，〕 | Clean sweetness, like cane or rock sugar  [lead-in: After that clean sweetness, ] |
| C3 | 焦糖、红糖　〔承接语：焦糖那种甜之后，〕 | Caramel, brown sugar  [lead-in: After that caramel sweetness, ] |
| C4 | 黑糖、糖蜜：浓，带一点苦　〔承接语：黑糖、糖蜜那种浓甜之后，〕 | Dark sugar, molasses: deep, slightly bitter  [lead-in: After that deep, dark sweetness, ] |
| C5 | 香草、奶油那种甜　〔承接语：香草、奶油那种甜之后，〕 | Vanilla, creamy sweetness  [lead-in: After that creamy sweetness, ] |
| C6 | 熟透的水果、果酱　〔承接语：熟果那种甜之后，〕 | Ripe fruit, jam  [lead-in: After that ripe-fruit sweetness, ] |
| C7 | 果干：葡萄干、蜜枣　〔承接语：果干那种甜之后，〕 | Dried fruit: raisin, dates  [lead-in: After that dried-fruit sweetness, ] |
| C0（第五个选项） | 甜不突出，融在整体里 ‖ 有一点甜，但不单独显出来 ‖ 甜感很轻，和别的味道连在一起　〔承接语：甜不突出的话，〕 | Sweetness doesn't stand out; it sits in the whole ‖ A little sweet, but it never shows on its own ‖ Very light sweetness, joined to the other flavors  [lead-in: With little sweetness, ] |
| C-（下方小字） | 这一项很难形容 ‖ 这一项我说不上来 ‖ 我恐怕很难准确回答 | This one is hard to describe ‖ I can't put this one into words ‖ I'm afraid I can't answer this accurately |
| **核心 4 · 口感（按冲煮方式给窗口，不按语料）** · 题面 | 口感怎么样？（承接上一题时：……，口感怎么样？） | How does it feel in the mouth? (after a lead-in: … how does it feel in the mouth?) |
| D6 | 偏稀，像兑了水 | Thin, watery |
| D1 | 清爽，像茶或果汁 | Light, like tea or juice |
| D2 | 顺滑，像牛奶 | Smooth, like milk |
| D3 | 厚而滑，像奶油、丝绒 | Thick and silky, like cream |
| D4 | 厚重挂口，像糖浆 | Heavy and coating, like syrup |
| D5 | 发涩发干，像浓茶 | Drying and astringent, like strong tea |
| D0（第五个选项） | 厚薄适中，没有特别的感觉 ‖ 不厚也不薄，很平常 ‖ 口感居中，没有特别之处 | Medium weight; nothing in particular ‖ Neither thick nor thin; ordinary ‖ Middle of the road; nothing in particular |
| D-（下方小字） | 这一项很难形容 ‖ 这一项我说不上来 ‖ 我恐怕很难准确回答 | This one is hard to describe ‖ I can't put this one into words ‖ I'm afraid I can't answer this accurately |
| **第二级 · 更像哪一个** · 题面 | 更像哪一个？（承接上一题时：……，{short}里，更像哪一个？） | Which one is it closest to? (after a lead-in: … Among {short}, which one is it closest to?) |
| S-（下方小字） | 这一项很难形容 ‖ 这一项我说不上来 ‖ 我恐怕很难准确回答 | This one is hard to describe ‖ I can't put this one into words ‖ I'm afraid I can't answer this accurately |
| **追问 · 香气有多明显** · 题面 | 凑近闻一闻，香气有多明显？ | Smell the cup: how clear is the aroma? |
| E1a | 扑鼻，端起来就闻得到 | Strong: I notice it as soon as I lift the cup |
| E1b | 清楚，凑近能闻到 | Clear when I bring it close |
| E1c | 很淡，要仔细闻 | Faint: I have to look for it |
| E1d | 几乎闻不到 | Hardly any |
| E1-（下方小字） | 我恐怕很难准确回答 ‖ 这一项我说不上来 ‖ 这一项很难形容 | I'm afraid I can't answer this accurately ‖ I can't put this one into words ‖ This one is hard to describe |
| **追问 · 咽下去之后的余韵** · 题面 | 咽下去之后，嘴里的味道留了多久？ | After you swallow, how long does the taste stay? |
| E2a | 很快就感觉不到了 | It fades almost at once |
| E2b | 稍微有一些感觉，但不明显 | There is a little, but it is not distinct |
| E2c | 有较明确的余韵 | There is a fairly distinct aftertaste |
| E2d | 余韵明显并带有回甘 | A clear aftertaste that turns sweet |
| E2e | 余韵以苦或涩为主 | The aftertaste is mostly bitter or drying |
| E2-（下方小字） | 我恐怕很难准确回答 ‖ 这一项我说不上来 ‖ 这一项很难形容 | I'm afraid I can't answer this accurately ‖ I can't put this one into words ‖ This one is hard to describe |
| **追问 · 苦感** · 题面 | 尾段苦吗？ | Is the aftertaste bitter? |
| E3a | 没有明显苦感 | No noticeable bitterness |
| E3b | 微苦，像可可或坚果皮 | Slight, like cocoa or nut skins |
| E3c | 有苦味但柔和，像黑巧克力 | Present but soft, like dark chocolate |
| E3d | 苦得比较明显，像烟熏可可或烤焦的吐司边 | Pronounced, like smoky cocoa or the burnt edge of toast |
| E3e | 非常重的苦味，像烧焦的木炭 | Very heavy bitterness, like burnt charcoal |
| E3-（下方小字） | 我恐怕很难准确回答 ‖ 这一项我说不上来 ‖ 这一项很难形容 | I'm afraid I can't answer this accurately ‖ I can't put this one into words ‖ This one is hard to describe |
| **追问 · 整体印象（答案矛盾时）** · 题面 | 这一口整体更像哪种？ | Overall, how do the flavors come across? |
| E4a | 味道混在一起，各种风味都有一点 | The flavors blend together, a little of everything |
| E4b | 饱满圆润，一致性很高 | Full and round, all of a piece |
| E4c | 能分清楚多种味道，层次明确 | I can tell several flavors apart, in clear layers |
| E4d | 感觉不错，但很难形容 ‖ 感觉不错但说不上来 | I like it, but it is hard to describe ‖ I like it, but I can't put it into words |
| 第二级 · A1 的词（显示语料支持最多的 5 个） | 柠檬、青柠、甜橙、葡萄柚、佛手柑、血橙、蜜桔、砂糖橘 | lemon, lime, sweet orange, grapefruit, bergamot, blood orange, honey mandarin, sugar mandarin |
| 第二级 · A2 的词（显示语料支持最多的 5 个） | 树莓、草莓、蓝莓、黑加仑、黑莓、石榴、蔓越莓 | raspberry, strawberry, blueberry, blackcurrant, blackberry, pomegranate, cranberry |
| 第二级 · A3 的词（显示语料支持最多的 5 个） | 车厘子、李子、水蜜桃、白桃、黄桃、杏桃 | cherry, plum, peach, white peach, yellow peach, apricot |
| 第二级 · A4 的词（显示语料支持最多的 5 个） | 葡萄、苹果、秋月梨、白葡萄 | grape, apple, Akizuki pear, white grape |
| 第二级 · A5 的词（显示语料支持最多的 5 个） | 芒果、凤梨、香蕉、椰子、荔枝、蜜瓜 | mango, pineapple, banana, coconut, lychee, melon |
| 第二级 · A6 的词（显示语料支持最多的 5 个） | 葡萄干、西梅 | raisin, prune |
| 第二级 · B1 的词（显示语料支持最多的 5 个） | 茉莉花、玫瑰、橙花、洋甘菊、玉兰花、咖啡花、金银花、山茶花、姜花 | jasmine, rose, orange blossom, chamomile, magnolia, coffee blossom, honeysuckle, camellia, ginger lily |
| 第二级 · B2 的词（显示语料支持最多的 5 个） | 红茶、茉莉绿茶、高山乌龙、伯爵茶 | black tea, jasmine green tea, high-mountain oolong, Earl Grey tea |
| 第二级 · B3 的词（显示语料支持最多的 5 个） | 薄荷、柠檬草 | mint, lemongrass |
| 第二级 · B4 的词（显示语料支持最多的 5 个） | 杏仁、烤榛果、核桃、花生 | almond, roasted hazelnut, walnut, peanut |
| 第二级 · B5 的词（显示语料支持最多的 5 个） | 可可、牛奶巧克力、榛果巧克力、巧克力酱 | cocoa, milk chocolate, hazelnut chocolate, chocolate sauce |
| 第二级 · B6 的词（显示语料支持最多的 5 个） | 吐司、麦芽、曲奇饼干、提拉米苏 | toast, malt, butter cookie, tiramisu |
| 第二级 · B8 的词（显示语料支持最多的 5 个） | 风干雪松、杉木、柏木、橡木、檀香、松木、桦木、干燥树皮、沉香 | aged cedar, fir wood, cypress, oak, sandalwood, pine, birch, dry bark, agarwood |
| 第二级 · B9 的词（显示语料支持最多的 5 个） | 烟草、泥炭、松露 | tobacco, peat, truffle |

## 8. About（about.ts，经执行导出）

| 位置 | 中文 | English |
|---|---|---|
| 页面小标题 | 从品味，到表达 | From tasting to words |
| Eyebrow | 关于 FLAVORWORDS | About FLAVORWORDS |
| 标题 | 从品味，到表达 | From tasting to words |
| 导言 1 | 有时是一点花香，有时是像水果一样的酸，或是喝完之后留下的甜。你留意到的细节，构成了对这一杯咖啡的印象，却未必能立刻找到合适的词。 | Sometimes it is a touch of florals, an acidity like fruit, or the sweetness a cup leaves behind. The details you notice make up your impression of the coffee, yet the right word does not always come at once. |
| 导言 2 | flavorwords 将专业咖啡评审、感官词汇与日常品饮用语放在一起整理，帮助你从熟悉的味道联想，找到更具体的描述。 | flavorwords brings professional coffee reviews, sensory lexicons and everyday tasting language together, so you can move from familiar tastes to a more specific description. |
| 导言 3 | 从酸质、香气到甜感与口感，通过几次提问和选择，把这一杯的感受组成自己的风味卡。专业资料提供参照，最后由你确认。 | From acidity and aroma to sweetness and mouthfeel, a few questions and choices turn what you tasted into your own flavor card. Professional material provides the reference; you confirm the result. |
| 设计页 eyebrow | 设计思路 | Design notes |
| 设计页标题 | 为品味而设计 | Design for taste |
| 设计页段 1 | flavorwords 将双语词汇、风味分组与匹配逻辑，整合进逐步展开的提问与选词过程。你不必翻查一整张风味词表，可以随着问题和候选描述，逐步辨认这一杯的特点。 | flavorwords folds a bilingual vocabulary, flavor groups and matching logic into a few questions and word choices, so you recognise this cup without reading a whole flavor wheel. |
| 署名行 | 研究、设计与开发：潘岱 · Dai Pan | Research, design and development: Dai Pan · 潘岱 |
| 贡献 94 | 94 个双语风味词：对照专业感官词汇整理，并补充中文品饮表达。 | 94 bilingual flavor words: aligned with professional lexicons, with Chinese tasting expressions added. |
| 贡献 12 | 12 类风味特征：每个风味词都归到其中一类；提问、出词和风味卡都按这些类取词。 | 12 flavor features: every flavor word belongs to one; questions, suggested words and the card all draw from them. |
| 贡献 16 | 16 组参考风味：本项目从评审资料整理的分组，用来给出第一版描述。 | 16 reference profiles: groups this project organised from the review material to give a first description. |
| 资料范围标题 | 资料范围 | Scope of the material |
| 资料范围 assertions | 83,031 条风味描述记录：从公开评审文本中抽出的感官描述。 | 83,031 flavor-description records: sensory descriptions extracted from public review text. |
| 资料范围 coffees | 9,128 条咖啡评审记录：去重后的记录数；其中 8,142 条带至少一个风味词，进入参考风味分组。 | 9,128 coffee review records: deduplicated records; 8,142 of them carry at least one flavor word and enter the reference-profile grouping. |
| 资料范围 consumers | 4,042 位GACTT 消费者研究参与者：盲测用词的聚合频次，用于中文消费端词汇的对照；口径为研究参与者。 | 4,042 GACTT consumer-study participants: aggregate word frequencies from their blind-tasting notes, used to cross-check the Chinese consumer vocabulary; counted as study participants. |
| 资料范围 sources | 2 份已采用的研究参考：6 条研究说明来自这些来源；来源条款与本项目的使用方式列在下方。 | 2 research references in use: 6 research notes come from these sources; each source's terms and this project's use are listed below. |
| 资料范围脚注 | 版本 product-vector-v1，统计于 2026-09-12。 | Version product-vector-v1, counted on 2026-09-12. |

### About · 词汇与风味分组 / Vocabulary and flavor groups（默认折叠）

| 位置 | 中文 | English |
|---|---|---|
| 摘要 | 将不同来源的风味描述进行双语对照与特征分组，把专业词汇和熟悉的品饮表达整理成可供比较的候选词，帮助你找到更贴近感受的说法。 | Descriptions from many sources, aligned in two languages and grouped by feature, become candidate words you can compare. |
| 词表 / Word list | 风味词对照公开的感官词汇表整理，中英并列；中文一侧补充了大陆品饮时常用的说法（如酒酿、桂花、冰糖雪梨）。资料中出现过但意思不够明确的词，只用于识别输入，不作为默认推荐词。 | The flavor words are aligned with public sensory lexicons and given side by side in Chinese and English; the Chinese side adds expressions common in mainland tasting talk. Words that appear in the material but stay vague are used only to recognise input, never as default suggestions. |
| 风味特征 / Flavor features | 每个风味词归到 12 类风味特征中的一类：酸质、甜感、醇厚度、花香、果香、坚果巧克力、发酵与酒香、烘烤苦感、香料、草本绿茶、木质泥土、瑕疵。不同来源的描述由此可以放在一起比较；提问、出词和风味卡都按这些类取词。 | Every flavor word belongs to one of 12 features: acidity, sweetness, body, floral, fruity, nutty & chocolate, fermented & winey, roast & bitter, spice, herbal & green, woody & earthy, defect. Descriptions from different sources can then be compared side by side; questions, suggested words and the card all draw from these. |
| 参考风味 / Reference profiles | 16 组参考风味是本项目从评审资料中整理的分组，每组以两个主要感官参照命名，用来给出第一版描述。它们是整理的结果，不是咖啡的全部分类。 | The 16 reference profiles are groups this project organised from the review material, each named by two sensory references, used to give a first description. They are a result of that organisation, not a taxonomy of all coffee. |

### About · 动态问答模型 / Dynamic question model（默认折叠）

| 位置 | 中文 | English |
|---|---|---|
| 摘要 | 先从酸质与香气建立方向；之后每一题都承接上一题的回答，选项按这杯与你的回答重新排序；需要进一步辨认时，补充一次提问或确认。 | Acidity and aroma set the direction; each later question picks up the previous answer and re-ranks its options by this cup and your answers; one more question or confirmation settles what is still unclear. |
| 提问顺序 / Order | 前两题（酸质、香气）给出一个基本方向；后面的每一题都承接上一题的回答来问，选项按这杯的信息与你到目前为止的回答重新排序，「不明显」一类的出口永远在最后。回答与方向不一致时多问一题，或在出词后请你再看一眼；一致时少问。 | The first two answers (acidity, aroma) set a direction; every later question is phrased from the previous answer and its options are re-ranked by the cup's information and your answers so far, with the "not noticeable" exits always last. If answers disagree with the direction, one more question is asked, or you are asked to look again after the words appear; when they agree, fewer questions are asked. |
| 描述的选择与确认 / Choosing and confirming the words | 系统先给出 8 个候选词：3 个主要建议，5 个备选；你从中选出 5 个，这 5 个词就是风味卡，卡片的分组名也按你选出的词确定。如果你选的词与前面的回答方向差得很远，会再请你看一眼，然后按你确认的结果更新。 | 8 candidate words are offered: 3 main suggestions and 5 alternatives; you pick 5, those 5 are the card, and the card's group name follows the words you picked. If your picks point far from your earlier answers, you are asked to look once more, and the card is updated to what you confirm. |

### About · 资料与方法 / Data and method（默认折叠）

| 位置 | 中文 | English |
|---|---|---|
| 摘要 | 查看词汇来源、风味分组与匹配方式，了解参考描述如何形成，以及结果的适用范围。 | Where the words come from, how grouping and matching work, and what the result covers. |
| 资料范围 / Scope of the material | 83,031 条风味描述记录：从公开评审文本中抽出的感官描述。<br><br>9,128 条咖啡评审记录：去重后的记录数；其中 8,142 条带至少一个风味词，进入参考风味分组。<br><br>4,042 位 GACTT 消费者研究参与者：盲测用词的聚合频次，用于中文消费端词汇的对照；口径为研究参与者。<br><br>2 份已采用的研究参考：6 条研究说明来自这些来源；来源条款与本项目的使用方式列在下方。<br><br>版本 product‑vector‑v1，统计于 2026‑09‑12。 | 83,031 flavor-description records: sensory descriptions extracted from public review text.<br><br>9,128 coffee review records: deduplicated records; 8,142 of them carry at least one flavor word and enter the reference-profile grouping.<br><br>4,042 GACTT consumer-study participants: aggregate word frequencies from their blind-tasting notes, used to cross-check the Chinese consumer vocabulary; counted as study participants.<br><br>2 research references in use: 6 research notes come from these sources; each source's terms and this project's use are listed below.<br><br>Version product‑vector‑v1, counted on 2026‑09‑12. |
| 初始参考如何形成 / How the initial reference is formed | 冲煮方式、烘焙度、豆种与处理法各有一个从评审资料统计得到的参考向量，相加后就是这杯咖啡的初始参考。评审记录不足的选项（如蜜处理、湿刨法、乳酸发酵、酒桶发酵、冷萃）目前没有参考向量，选择它们不会改变初始参考。产地可选，只在花香、果香等少数特征上加一点偏置。初始参考只是起点，你的回答与选词决定最后的风味卡。 | Brew method, roast level, variety and processing each have a reference vector counted from the review material; added together they form this cup's initial reference. Options with too few reviews (honey, wet-hulled, lactic, barrel-aged, cold brew) have no reference vector yet, so choosing them leaves the initial reference unchanged. Origin is optional and adds only a small bias on a few features. The initial reference is a starting point; your answers and picks decide the final card. |
| 结果的适用范围 / What the result covers | 风味卡呈现你本次选择的描述。冲煮与豆子信息用于提供初始参考，相关研究用于补充说明；这些内容不构成对杯中成分或风味成因的测定。 | The card presents the description you chose this time. Brew and bean information provides the initial reference, and related research adds notes; none of this measures the cup's composition or the causes of its flavor. |
| 技术说明 / Technical notes | 每类风味特征是向量的一个分量，共 12 个分量。V_pred = normalize(Σ K)：语境的参考向量相加；V_user = normalize(Σ Q)：每个回答的增量向量相加；ΔV = V_user − V_pred；V_target = normalize(V_pred + α·ΔV)，α = 0.5，再确认后 α = 0.9。回答分组后投影到 16 组参考风味上比较相似度：≥ 0.8 视为一致，< 0.65 视为明显不一致；烘焙方向单独检查。余弦相似度只用来找最接近的几组，再由你的选择决定；不给咖啡打分，也不输出概率。全部计算在手机本地完成，没有训练模型。 | Each flavor feature is one component of a 12-component vector. V_pred = normalize(Σ K): the context reference vectors added; V_user = normalize(Σ Q): the answer increments added; ΔV = V_user − V_pred; V_target = normalize(V_pred + α·ΔV) with α = 0.5, and α = 0.9 after a second confirmation. Answer groups are projected onto the 16 reference profiles and compared: ≥ 0.8 counts as consistent, < 0.65 as clearly inconsistent; roast direction is checked separately. Cosine similarity only finds the closest few groups; your picks decide from there. No scores, no probabilities; everything runs on the phone and no model is trained. |
| 来源 / Sources | World Coffee Research (WCR) — Sensory Lexicon<br>风味与香气属性的标准词汇与参照物；用于对齐 94 个风味词，以及浅、中、深烘的研究说明。<br>来源：https://worldcoffeeresearch.org/resources/sensory-lexicon<br>条款：官方页面：可免费下载、打印供个人使用；正式许可条款待核对（2026-09-12 查看）<br>本项目的使用：查阅属性名称与参照物定义，用于词表对齐；不转载词汇表原文<br><br>Coffee Ad Astra (Jonathan Gagné) — The Physics of Filter Coffee<br>滤泡咖啡萃取的物理模型；用于通道效应与萃取率的研究说明。<br>来源：https://coffeeadastra.com/ ; The Physics of Filter Coffee, ISBN 978-0-578-95028-0<br>条款：作者公开博客与自出版书籍；署名引用，不转载原文<br>本项目的使用：转述萃取物理的解释，用于通道效应与萃取率两类说明<br><br>Great American Coffee Taste Test (GACTT) — consumer study<br>4,042 位参与者盲测用词的聚合频次，不含原文；用于中文消费端词汇的对照。<br>来源：GACTT_CONSUMER_TERM_FREQUENCY.tsv<br>条款：公开数据集<br>本项目的使用：只使用聚合计数，不保存原文 | World Coffee Research (WCR) — Sensory Lexicon<br>Standard vocabulary and references for flavor and aroma attributes; used to align the 94 flavor words and for the light, medium and dark roast research notes.<br>Source: https://worldcoffeeresearch.org/resources/sensory-lexicon<br>Terms: Official page: free download and printing for personal use; formal licence terms to be confirmed (checked 2026-09-12)<br>Use in this project: Attribute names and reference definitions consulted for word-list alignment; no lexicon text reproduced<br><br>Coffee Ad Astra (Jonathan Gagné) — The Physics of Filter Coffee<br>A physical model of filter-coffee extraction; used for the research notes on channeling and extraction yield.<br>Source: https://coffeeadastra.com/ ; The Physics of Filter Coffee, ISBN 978-0-578-95028-0<br>Terms: Author's public blog and self-published book; cited with attribution, no text reproduced<br>Use in this project: Extraction-physics explanations paraphrased for the notes on channeling and extraction yield<br><br>Great American Coffee Taste Test (GACTT) — consumer study<br>Aggregate word frequencies from 4,042 participants' blind-tasting notes, no original text; used to cross-check the Chinese consumer vocabulary.<br>Source: GACTT_CONSUMER_TERM_FREQUENCY.tsv<br>Terms: Public dataset<br>Use in this project: Aggregate counts only; no original text kept |

### About · 资料来源列表（本项目如何使用这份资料）

| 来源 | 中文 | English | 来源条款 | 本项目的使用 | 上线说明句 |
|---|---|---|---|---|---|
| World Coffee Research (WCR) | 风味属性的标准词汇与参照物 | standard vocabulary and references for flavor attributes | 官方页面：可免费下载、打印供个人使用；正式许可条款待核对（2026-09-12 查看） | 查阅属性名称与参照物定义，用于词表对齐；不转载词汇表原文 | 3 |
| Coffee Ad Astra (Jonathan Gagné) | 滤泡萃取的物理模型 | a physical model of filter extraction | 作者公开博客与自出版书籍；署名引用，不转载原文 | 转述萃取物理的解释，用于通道效应与萃取率两类说明 | 3 |
| Great American Coffee Taste Test (GACTT) | 4,042 位参与者的用词频次 | word frequencies from 4,042 participants | 公开数据集 | 只使用聚合计数，不保存原文 | 0 |


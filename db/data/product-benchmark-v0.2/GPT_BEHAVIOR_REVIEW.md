# 独立 GPT 产品行为与状态复核

日期：2026-09-05。复核身份：独立 GPT 子代理。
状态：`GPT_REVIEW_ONLY_NOT_OWNER_APPROVAL`。

本记录是代码与合成状态的独立检查，不是 owner 决定、真实用户测试、外部专家审核或模型训练。没有运行 Claude 或 DeepSeek，没有填写任何人的产品接受度决定。本代理没有修改实现或提交 commit；实现修复及最终验收由主任务处理。

## 范围与方法

读取了以下实现及用户提供的本轮合同：

- `packages/flavor-data/src/research/index.ts`：评分、输出层级、候选工作集、题目选择与 Q5。
- `packages/flavor-data/src/research/session.ts`：内存会话、导出 allowlist 与校验。
- `app/routes/research.tsx`：A/B 任务流、Q5 接受／退出、结果页、计时及本地下载。
- `db/scripts/generate-product-inference-v02.py` 与生成的 runtime catalog。
- `packages/flavor-data/src/research/benchmark.ts`：合成案例构造及其触达范围。
- `app/root.tsx`：研究路由外壳与全局页面依赖。

实际使用 Node 与仓库已有 TypeScript 对模块作内存转译并执行，未启动浏览器或新增验证脚本文件。UI 路径问题由界面事件处理代码追踪，并用同一 engine／export 模块复现状态后果。因此本记录不替代主任务的浏览器端到端测试或手机验证。

遍历从 A、B 两种初始状态开始；C0 固定为 catalog 第一项，C1 固定为 medium。对每个实际 `nextStep`，枚举全部非空多选子集和 `UNSURE`、`NONE_OF_THESE`、`SKIP`。对恢复题分别检查不接受时拒绝作答，并在接受的分支中继续执行，直到引擎停止。未把手工注入的任意题序混入合法路径数。

结果为 **3,382 个遍历状态，192 个 Q5 offer 状态**。它们是合成执行路径计数，包含回答历史不同但数值可能相同的状态；不是参与者人数、咖啡样本数、独立观察数或用户接受率，也没有遍历全部 C0×C1 组合。

本次遍历中：

- 未选项的 support 与 boundedNegative 均保持原值；没有发现隐藏的未选即反证。
- `UNSURE` 与 `SKIP` 均无分值增减；`NONE_OF_THESE` 的数值反证仅作用于本题展示选项所代表的概念。
- 对当前 frontier 投影后，没有发现再次询问先前完整相同分区的后续题。该检查排除 mandatory family-direction 父分组，不能证明所有语言层面都毫无重复。
- 未发现 rights-ineligible 或 unresolved 候选进入可见输出，也未发现同一 redundancy group 重复展示。
- 输出层级未超过 3+2+3；Q5 offer 均发生在已有四题、headline 少于三个且无 conflict/open-set 的状态；没有接受恢复时作答会被拒绝。

A/B 赋值、B 的 fruit/flower 分支、session 字段、浏览器内存存储及计时边界另行作了代码检查。没有测量真实人的理解、实际设备响应或页面后台停留对用时的影响。

## 主要发现 1：接受 Q5 后提前返回曾导致无法导出

严重度：会阻断任务完成。范围：正常 UI 可到达。

复现路径：

1. 用奇数研究编号进入 A 版，完成 C0/C1。
2. Q1 `direction_A`、Q2 `floral_tea_reference`、Q3 `roast_smoke_reference`、Q4 `browned_sweet_reference` 全部回答“不确定”。
3. 结果页提供恢复题 `fermentation_character`，点击“再回答一题，让结果更具体”。
4. 在 Q5 页还未作答就点击“先看当前结果”，然后完成后续反馈并导出。

初次复现时 `q5Accepted=true`、`q5Offered=true`、`extraQuestionClicked=true`，但 `totalQuestionCount=4`。`exportSession` 实际抛出 `Q5 acceptance mismatch`。结果页又用 `!session.q5Accepted` 隐藏恢复按钮，因而不能返回作答。

主任务已选择把“接受”定义为点击意图，是否答完由 `totalQuestionCount === 5` 派生，并调整 schema 和结果页恢复入口。写本记录时已读取到这两处实现更新：接受允许四题记录，恢复入口不再因 accepted 而隐藏。该修复的浏览器退出／重入／导出路径仍需由主任务端到端验收，不应把代码检查写成真实用户完成验证。

owner 后续需确认分析协议将 Q5 接受率与 Q5 完成率分开，并决定接受后退出如何归入任务负担。这里没有替 owner 填写接受度结论。

## 主要发现 2：弱 NONE 数值与保守展示否决是两层不同政策

严重度：需要显式治理与说明的行为边界，不应伪装成已验证的科学阈值。

复现路径：A 版 Q1 只选 `fruit`；自动下一题为 `acidity_character`，回答 `NONE_OF_THESE`。

实际输出：

| 概念 | support | boundedNegative | 净感官支持 |
| --- | ---: | ---: | ---: |
| Orange | 3 | -1.25 | 1.75 |
| Lemon | 3 | -1.25 | 1.75 |
| Blueberry | 3 | -1.25 | 1.75 |

这些概念仍保留分值，但 `evaluate` 返回 `ABSTAINED_CONFLICT`，`nextStep` 不再提供题目。此外，只要某个候选的 `boundedNegative < 0`，当前展示筛选就会暂缓它，即使净支持仍为正。

因此，`boundedNone=-1.25` 本身不是实际展示行为的全部说明；还有独立的保守展示否决条件。这不是未选项被当作反证，也不是全局负面标签：反证范围仍来自本题展示列表，但列表内被争议的候选会被暂缓展示。

主任务决定将此明确标为保守研究政策：数值保留，争议候选暂缓展示；所有有支持且 rights-eligible 候选均受争议时停止并 abstain。该政策仍是最高优先级 owner 复核项，本记录不批准它，也不声称 -1.25 或否决阈值已经经过用户验证。

owner 需要判断这样的暂缓是否过于保守，以及哪些前后回答应触发 conflict。若后续改变规则，应另行保存政策版本与回放结果，而非改写本次合成执行记录。

## 追加的记录一致性发现

### 结果页取消 open-set 后理由未恢复

范围：正常 UI 可到达；按页面处理器还原后已实际调用导出模块验证。

进入结果页，勾选“我想描述的感觉在这些方向之外”，再取消勾选。原实现取消时沿用 `session.earlyStopReason`，所以导出可以同时出现：

```text
openSet = false
earlyStopReason = PARTICIPANT_REPORTED_OPEN_SET
```

建议取消时恢复此前实际停止理由，或明确保存 open-set 的最终值与切换历史，避免单个最终理由与最终状态互相冲突。此项已报主任务；本记录不声称已完成修复验收。

### 导出 schema 当时没有验证事件能否回放

范围：schema／内存会话层复现；没有发现正常 UI 自己产生该伪造记录的路径。

先构造 A 版连续两次 `UNSURE` 的合法 session，再修改第二个 event 的 `questionId` 为 `not-a-catalog-question`、`semanticKey` 为 `invented-semantic`、`optionIdsShown` 为 `['made-up-option']`，并把 `allOptionsSelected` 改为 true。初次检查时 `sessionExportSchema.safeParse(...).success` 仍为 true。

另外，修改 `session.questions[1]` 的题目和语义 ID、保持 `session.state.answers` 不变，`exportSession` 仍导出该不存在的题目。手动修改已导出记录的 headline count 与 resultState 也不触发回放一致性检查。

这说明当时的校验保证了字段形状和部分计数关系，还没有保证 catalog 身份、展示选项、完整题序、派生结果与事件一致。建议按 catalog 和引擎回放，或明确标注该 schema 只作结构检查；不要把这项人工构造的负面测试误写成实际用户数据已被篡改。此项已报主任务，本记录不替代后续校验测试。

## 可复核执行命令

下列命令在仓库根目录执行，使用现有 Node、TypeScript 和 catalog，所有转译都在内存进行。它复核上述 3,382／192 数量、数值中性、rights、重复完整分区和 Q5 护栏；**不覆盖 UI 的点击顺序、计时或导出问题**。

```bash
node --input-type=module <<'JS'
import fs from 'node:fs';
import ts from 'typescript';
import assert from 'node:assert/strict';

const catalog = JSON.parse(fs.readFileSync(
  'db/data/product-inference-v0.2/PRODUCT_RUNTIME_CATALOG.json', 'utf8',
));
const source = fs.readFileSync(
  'packages/flavor-data/src/research/index.ts', 'utf8',
).replace(/^import catalog[^;]+;/, `const catalog = ${JSON.stringify(catalog)};`);
const js = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const e = await import(
  'data:text/javascript;base64,' + Buffer.from(js).toString('base64')
);
const partition = (q, frontier) => q.options
  .map(o => o.conceptIds.filter(id => frontier.includes(id)).sort().join(','))
  .filter(Boolean).sort().join(';');
const queue = ['A', 'B'].map(v => e.createResearchState(
  v, catalog.preparations[0].id, 'medium',
));
let states = 0;
let offers = 0;
while (queue.length) {
  const state = queue.pop();
  states++;
  const next = e.nextStep(state);
  const result = e.evaluate(state);
  assert(state.answers.length <= 5);
  const visible = [...result.headline, ...result.expandedMain, ...result.exploration];
  assert(visible.every(c => c.rightsEligible && !c.unresolved));
  assert.equal(new Set(visible.map(c => c.redundancyGroup)).size, visible.length);
  assert(result.headline.length <= 3 && result.expandedMain.length <= 2
    && result.exploration.length <= 3);
  if (!next.question) continue;
  if (next.recovery) {
    offers++;
    assert.equal(state.answers.length, 4);
    assert(result.headline.length < 3);
    assert(!state.openSet && result.resultState !== 'ABSTAINED_CONFLICT');
    assert.throws(() => e.answerCurrentQuestion(state, [], 'UNSURE'));
  }
  const frontier = e.candidateFrontier(state);
  for (const answer of state.answers) {
    const prior = e.questionById(answer.questionId, state.variant);
    if (prior.semanticKey !== 'family-direction') {
      assert.notEqual(partition(prior, frontier), partition(next.question, frontier));
    }
  }
  const ids = next.question.options.map(o => o.id);
  const choices = Array.from({ length: (1 << ids.length) - 1 }, (_, i) => ({
    selected: ids.filter((_, j) => (i + 1) & (1 << j)), response: 'SELECTED',
  }));
  choices.push(...['UNSURE', 'NONE_OF_THESE', 'SKIP'].map(response => ({
    selected: [], response,
  })));
  for (const choice of choices) {
    const later = e.answerCurrentQuestion(state, choice.selected, choice.response, true);
    const represented = new Set(next.question.options
      .filter(o => choice.selected.includes(o.id)).flatMap(o => o.conceptIds));
    const shown = new Set(next.question.options.flatMap(o => o.conceptIds));
    const before = e.rankCandidates(state);
    const after = new Map(e.rankCandidates(later).map(c => [c.id, c]));
    for (const c of before) {
      const n = after.get(c.id);
      assert.equal(n.support - c.support,
        choice.response === 'SELECTED' && represented.has(c.id)
          ? catalog.policy.positive : 0);
      assert.equal(n.boundedNegative - c.boundedNegative,
        choice.response === 'NONE_OF_THESE' && shown.has(c.id)
          ? catalog.policy.boundedNone : 0);
    }
    queue.push(later);
  }
}
console.log(JSON.stringify({
  states, q5OfferStates: offers, rightsLeaks: 0, repeatedLivePartitions: 0,
  neutralAdjustmentFailures: 0, q5GuardFailures: 0,
}));
JS
```

本次实际输出：

```json
{"states":3382,"q5OfferStates":192,"rightsLeaks":0,"repeatedLivePartitions":0,"neutralAdjustmentFailures":0,"q5GuardFailures":0}
```

导出层负面检查使用相同的内存转译方式载入 `session.ts`，将其 `./index` 导入指向上述转译模块，将 `zod` 指向已安装依赖，再执行 `exportSession` 和 `sessionExportSchema.safeParse`。各发现段保留了输入操作、关键状态和实际错误／结果，便于把它们转成正式回归测试。版本修改后输出可能变化；不要为了保留本记录的历史数字而阻止合理修复。

## 尚未完成的验证

本轮没有完成 owner 接受度审核、真实用户 A/B 比较、浏览器网络请求观察、跨屏幕布局测试、后台计时实验或设备辅助技术测试。对 bounded NONE 的保守展示政策、参照熟悉度和问题负担，仍需 owner 审核和真实用户研究。主任务的独立 unit／e2e 结果应单独记录，不能把本次 GPT 状态遍历改称为这些验证已经完成。

import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import ts from "typescript";

const root = fileURLToPath(new URL("../", import.meta.url));
const output = path.join(root, "db/data/product-benchmark-v0.2");
await mkdir(output, { recursive: true });
// Transpile the same pure TypeScript engine used by the research route. The
// data URL is a local in-memory module, not a second inference implementation.
const catalog = await readFile(
  path.join(
    root,
    "db/data/product-inference-v0.2/PRODUCT_RUNTIME_CATALOG.json",
  ),
  "utf8",
);
const engine = (
  await readFile(
    path.join(root, "packages/flavor-data/src/research/index.ts"),
    "utf8",
  )
).replace(/import catalog from [^;]+;/, `const catalog = ${catalog};`);
const compile = (source) =>
  "data:text/javascript;base64," +
  Buffer.from(
    ts.transpileModule(source, {
      compilerOptions: {
        module: ts.ModuleKind.ESNext,
        target: ts.ScriptTarget.ES2022,
      },
    }).outputText,
  ).toString("base64");
const engineUrl = compile(engine);
const casesSource = (
  await readFile(
    path.join(root, "packages/flavor-data/src/research/benchmark.ts"),
    "utf8",
  )
).replace('from "./index"', `from "${engineUrl}"`);
const { productTaskCases, benchmarkResult } = await import(
  compile(casesSource)
);
const cases = productTaskCases();
const quote = (v) => {
  const s = String(v ?? "");
  return /[\t\n\r"]/.test(s) ? '"' + s.replaceAll('"', '""') + '"' : s;
};
async function table(name, fields, rows) {
  await writeFile(
    path.join(output, name),
    [fields, ...rows.map((r) => fields.map((f) => r[f] ?? ""))]
      .map((r) => r.map(quote).join("\t"))
      .join("\n") + "\n",
  );
}
const records = cases.map((c) => ({
  case_id: c.id,
  category: c.category,
  purpose: c.purpose,
  harness_reachable: c.harnessReachable,
  fixture_kind: c.harnessReachable
    ? "PARTICIPANT_FLOW_FIXTURE"
    : "ENGINE_POLICY_FIXTURE_NOT_USER_SESSION",
  input_json: JSON.stringify(c.state),
  candidate_override_json: c.candidates.some((x) => x.reviewOnly)
    ? JSON.stringify(c.candidates)
    : "",
  expected_error: c.expectedError,
  result_json: JSON.stringify(benchmarkResult(c)),
  result_origin: "UNCALIBRATED_DETERMINISTIC_POLICY_OUTPUT_NOT_HUMAN_LABEL",
}));
await table("PRODUCT_TASK_CASE.tsv", Object.keys(records[0]), records);
const label = (id) =>
  JSON.parse(catalog).candidates.find((c) => c.id === id)?.label ?? id;
const packet = [
  "# Product-task review packet v0.2",
  "",
  "These are proposed deterministic outputs, not human-approved answers. Use the owner or agent TSV template to record decisions. Engine policy fixtures are not claimed to be live participant flows.",
  "",
];
for (const item of cases) {
  const result = benchmarkResult(item);
  packet.push(
    `## ${item.id} · ${item.category}`,
    "",
    item.purpose,
    "",
    `Fixture: ${item.harnessReachable ? "participant flow" : "engine policy"}. Variant ${item.state.variant}. Questions: ${item.state.answers.length}.`,
    "",
  );
  for (const [index, answer] of item.state.answers.entries())
    packet.push(
      `${index + 1}. ${answer.questionId}: ${answer.responseState} ${answer.selectedOptionIds.join(", ")}`,
    );
  packet.push(
    "",
    `Headline: ${result.headline.map(label).join("、") || "none"}.`,
    "",
    `Expanded main: ${result.expandedMain.map(label).join("、") || "none"}.`,
    "",
    `Explore: ${result.exploration.map(label).join("、") || "none"}.`,
    "",
    `State: ${result.resultState}. Q5 offer: ${result.extraQuestionAppropriate}.`,
    "",
  );
  for (const explanation of result.explanations)
    packet.push(`- ${label(explanation.conceptId)}: ${explanation.text}`);
  packet.push("", "Owner decision: blank, pending review.", "");
}
await writeFile(
  path.join(output, "PRODUCT_TASK_REVIEW_PACKET.md"),
  packet.join("\n"),
);
const ownerFields = [
  "case_id",
  "headline_acceptable",
  "expanded_main_acceptable",
  "exploration_acceptable",
  "candidate_to_remove",
  "candidate_to_add",
  "extra_question_appropriate",
  "abstention_appropriate",
  "explanation_understandable",
  "reason",
  "reviewer",
  "review_date",
  "final_owner_decision",
];
await table(
  "PRODUCT_TASK_OWNER_REVIEW_TEMPLATE.tsv",
  ownerFields,
  cases.map((c) => ({ case_id: c.id })),
);
const reviewFields = [
  "review_item_id",
  "case_id",
  "intended_reviewer",
  "reviewer_agent",
  "decision",
  "reason",
  "confidence",
  "identified_risk",
  "suggested_revision",
  "model_version",
  "review_timestamp",
  "final_owner_decision",
];
await table(
  "PRODUCT_TASK_AGENT_REVIEW_TEMPLATE.tsv",
  reviewFields,
  ["Claude", "DeepSeek", "GPT"].flatMap((reviewer) =>
    cases.map((c) => ({
      review_item_id: `${reviewer}-${c.id}`,
      case_id: c.id,
      intended_reviewer: reviewer,
    })),
  ),
);
// Imported reviews are separately maintained; generation never overwrites them.
try {
  await readFile(path.join(output, "PRODUCT_TASK_REVIEW_IMPORT.tsv"));
} catch {
  await table("PRODUCT_TASK_REVIEW_IMPORT.tsv", reviewFields, []);
}
await writeFile(
  path.join(output, "PRODUCT_BENCHMARK_MANIFEST.json"),
  JSON.stringify(
    {
      version: "product-benchmark-v0.2",
      case_count: cases.length,
      harness_reachable_case_count: cases.filter((c) => c.harnessReachable)
        .length,
      owner_decision_count: 0,
      human_final_decision_count: 0,
      agent_majority_auto_approval: false,
      final_human_decision_required: true,
      model_training_authorized: false,
      generated_at: "2026-09-05T00:00:00Z",
      status: "PRODUCT_BENCHMARK_REVIEW_REQUIRED",
    },
    null,
    2,
  ) + "\n",
);
console.log(
  JSON.stringify({
    case_count: cases.length,
    results: records
      .map((r) => ({ id: r.case_id, ...JSON.parse(r.result_json) }))
      .map(({ explanations, ...r }) => r),
  }),
);

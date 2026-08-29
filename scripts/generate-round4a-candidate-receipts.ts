import { writeFileSync } from "node:fs";
import { resolve } from "node:path";
import {
  rankCandidateSet,
  type CandidateInput,
  type SensoryAnswer,
  type TypedEdge,
} from "../packages/flavor-data/src/index";

const answer = (
  questionId: SensoryAnswer["questionId"],
  ...descriptorIds: string[]
): SensoryAnswer => ({
  questionId,
  descriptorIds,
  answerVersion: "round4a-q-v1",
});

const professional = (left: string, right: string): TypedEdge => ({
  left,
  right,
  layer: "G_professional",
  edgeType: "PROFESSIONAL_COASSERTION_EDGE",
  weight: 1,
  effectiveRecordCount: 8,
  sourceFamilyCount: 2,
  yearCount: 3,
  evidenceTier: "P2",
  rightsRegime: "REFERENCE_ONLY",
  reviewState: "GOVERNED_REFERENCE_FIXTURE",
});

const fixtures: Array<[string, CandidateInput]> = [
  [
    "floral_citrus_tea",
    {
      C0: "filter",
      C1: 3,
      answers: [
        answer("Q1", "jasmine"),
        answer("Q2", "lemon"),
        answer("Q3", "green-tea"),
        answer("Q4", "honey"),
      ],
      professionalEdges: [
        professional("jasmine", "lemon"),
        professional("lemon", "green-tea"),
      ],
    },
  ],
  [
    "fruit_chocolate_spice",
    {
      C0: "espresso",
      C1: 5,
      answers: [
        answer("Q1", "red-berries"),
        answer("Q2", "dark-chocolate"),
        answer("Q3", "cinnamon"),
        answer("Q4", "caramel"),
      ],
      professionalEdges: [
        professional("red-berries", "cinnamon"),
        professional("dark-chocolate", "cinnamon"),
      ],
    },
  ],
  [
    "rare_direct_answer",
    {
      C0: "espresso",
      C1: 7,
      answers: [
        answer("Q1", "bellflower"),
        answer("Q2"),
        answer("Q3"),
        answer("Q4"),
      ],
    },
  ],
  ["insufficient_evidence", { C0: "unknown", C1: 4, answers: [] }],
];

const fields = [
  "run_id",
  "rule_version",
  "objective",
  "input_context_json",
  "candidate_pool_json",
  "candidate",
  "rank",
  "role",
  "individual_score",
  "professional_coherence_contribution",
  "ontology_contribution",
  "context_contribution",
  "answer_contribution",
  "source_contribution",
  "community_contribution",
  "direct_evidence_coverage",
  "unsupported_outlier_penalty",
  "redundancy_penalty",
  "final_score",
  "uncertainty_reason",
  "override_applied",
  "abstained",
] as const;

function clean(value: unknown): string {
  return String(value ?? "")
    .replaceAll("\t", " ")
    .replaceAll("\n", " ");
}

const rows: Array<Record<(typeof fields)[number], unknown>> = [];
for (const [runId, input] of fixtures) {
  const receipt = rankCandidateSet(input);
  const pool = JSON.stringify(
    receipt.candidatePool.map((candidate) => ({
      candidate: candidate.descriptorId,
      individual_score: candidate.individualRelevance,
    })),
  );
  const selected =
    receipt.selected.length > 0
      ? receipt.selected
      : [
          {
            descriptorId: "ABSTAIN",
            rank: 0,
            role: "SECONDARY" as const,
            individualRelevance: 0,
            professionalCoherenceContribution: 0,
            ontologyContribution: 0,
            contextContribution: 0,
            answerContribution: 0,
            sourceContribution: 0,
            communityContribution: 0,
            directEvidenceCoverage: 0,
            unsupportedOutlierPenalty: 0,
            redundancyPenalty: 0,
            total: 0,
            uncertaintyReason:
              receipt.abstentionReason ?? "Insufficient evidence.",
            overrideApplied: false,
          },
        ];
  for (const candidate of selected) {
    rows.push({
      run_id: runId,
      rule_version: receipt.ruleVersion,
      objective: receipt.objective,
      input_context_json: JSON.stringify(input),
      candidate_pool_json: pool,
      candidate: candidate.descriptorId,
      rank: candidate.rank,
      role: candidate.role,
      individual_score: candidate.individualRelevance,
      professional_coherence_contribution:
        candidate.professionalCoherenceContribution,
      ontology_contribution: candidate.ontologyContribution,
      context_contribution: candidate.contextContribution,
      answer_contribution: candidate.answerContribution,
      source_contribution: candidate.sourceContribution,
      community_contribution: candidate.communityContribution,
      direct_evidence_coverage: candidate.directEvidenceCoverage,
      unsupported_outlier_penalty: candidate.unsupportedOutlierPenalty,
      redundancy_penalty: candidate.redundancyPenalty,
      final_score: candidate.total,
      uncertainty_reason: candidate.uncertaintyReason,
      override_applied: candidate.overrideApplied,
      abstained: receipt.abstained,
    });
  }
}

const output = [
  fields.join("\t"),
  ...rows.map((row) => fields.map((field) => clean(row[field])).join("\t")),
].join("\n");
writeFileSync(
  resolve("db/data/round4a/CANDIDATE_SET_SCORE_RECEIPT.tsv"),
  `${output}\n`,
  "utf8",
);

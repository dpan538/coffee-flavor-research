import { descriptors } from "./descriptors";
import type { Descriptor } from "./schema";

export const C1_LEVELS = [1, 2, 3, 4, 5, 6, 7] as const;
export const PRIMARY_CANDIDATE_COUNT = 5;
export const SECONDARY_CANDIDATE_COUNT = 3;
export const CANDIDATE_SET_SIZE = 8;
export const CANDIDATE_RULE_VERSION = "round4a-objective-m-deterministic-v1";

export type PreparationContext =
  | "espresso"
  | "filter"
  | "immersion"
  | "cupping"
  | "unknown";
export type RoastLevel = (typeof C1_LEVELS)[number];
export type GraphLayer =
  | "G_professional"
  | "G_ontology"
  | "G_context"
  | "G_community";

export interface TypedEdge {
  left: string;
  right: string;
  layer: GraphLayer;
  edgeType:
    | "PROFESSIONAL_COASSERTION_EDGE"
    | "REVIEWED_ONTOLOGY_EDGE"
    | "CONTEXT_EDGE"
    | "COMMUNITY_LANGUAGE_EDGE";
  weight: number;
  effectiveRecordCount: number;
  sourceFamilyCount: number;
  yearCount: number;
  evidenceTier: "P1" | "P2" | "PROJECT_CURATED" | "AUXILIARY";
  rightsRegime: "REFERENCE_ONLY" | "PROJECT_EXPERIMENT_ALLOWED";
  reviewState: string;
}

export interface SensoryAnswer {
  questionId: "Q1" | "Q2" | "Q3" | "Q4" | "Q5";
  descriptorIds: string[];
  answerVersion: string;
}

export interface CandidateInput {
  C0: PreparationContext;
  C1: RoastLevel;
  answers: SensoryAnswer[];
  professionalDirectIds?: string[];
  professionalEdges?: TypedEdge[];
  communityEdges?: TypedEdge[];
}

export interface CandidateScore {
  descriptorId: string;
  canonicalTarget: string;
  individualRelevance: number;
  contextContribution: number;
  answerContribution: number;
  sourceContribution: number;
  professionalCoherenceContribution: number;
  ontologyContribution: number;
  communityContribution: number;
  directEvidenceCoverage: number;
  unsupportedOutlierPenalty: number;
  redundancyPenalty: number;
  total: number;
  evidenceLabel:
    | "stronger evidence"
    | "moderate evidence"
    | "weaker evidence"
    | "secondary reference"
    | "insufficient evidence";
  uncertaintyReason: string;
  overrideApplied: boolean;
}

export interface CandidateMember extends CandidateScore {
  rank: number;
  role: "PRIMARY" | "SECONDARY";
  connectionsToSelected: string[];
}

export interface CandidateSetReceipt {
  ruleVersion: string;
  objective: "M(S|x)";
  input: CandidateInput;
  candidatePool: CandidateScore[];
  selected: CandidateMember[];
  primaryCount: number;
  secondaryCount: number;
  abstained: boolean;
  abstentionReason: string | null;
  connectedComponents: number;
  largestComponentShare: number;
  isolatedCandidateCount: number;
  bridgeCandidateCount: number;
  overrideReceipts: Array<{
    descriptorId: string;
    reason:
      | "EXPLICIT_Q_EVIDENCE_OVERRIDES_WEAK_CONTEXT_PRIOR"
      | "STRONG_DIRECT_EVIDENCE_EXCLUDED_BY_FIXED_SET";
  }>;
  outlierReceipts: Array<{
    descriptorId: string;
    penalty: number;
    reason: "NO_PAIR_ONTOLOGY_CONTEXT_Q_OR_DIRECT_SOURCE_SUPPORT";
  }>;
  negativeEdgesStored: false;
  probabilityClaims: false;
  graphLayersKeptSeparate: true;
}

const CONTEXT_IDS: Record<PreparationContext, string[]> = {
  filter: [
    "jasmine",
    "rose",
    "orange-blossom",
    "lemon",
    "orange",
    "green-tea",
    "honey",
    "red-berries",
  ],
  espresso: [
    "dark-chocolate",
    "caramel",
    "brown-sugar",
    "hazelnut",
    "almond",
    "cinnamon",
    "smoky",
    "red-berries",
  ],
  immersion: [
    "honey",
    "caramel",
    "dried-fruit",
    "earthy",
    "cedar",
    "dark-chocolate",
    "fermented",
    "winey",
  ],
  cupping: [
    "jasmine",
    "lemon",
    "orange",
    "blueberry",
    "red-berries",
    "honey",
    "green-tea",
    "winey",
  ],
  unknown: [],
};

const LIGHT_ROAST_IDS = new Set([
  "jasmine",
  "rose",
  "orange-blossom",
  "lemon",
  "orange",
  "blueberry",
  "red-berries",
  "green-tea",
]);
const DARK_ROAST_IDS = new Set([
  "dark-chocolate",
  "caramel",
  "brown-sugar",
  "almond",
  "hazelnut",
  "cinnamon",
  "tobacco",
  "smoky",
]);

// Reviewed/project-curated typed relations are deliberately sparse. Category
// identity alone is not treated as proof that every member co-occurs.
export const ontologyEdges: TypedEdge[] = [
  edge("jasmine", "green-tea"),
  edge("jasmine", "orange-blossom"),
  edge("lemon", "orange"),
  edge("lemon", "green-tea"),
  edge("orange", "honey"),
  edge("blueberry", "red-berries"),
  edge("red-berries", "winey"),
  edge("dried-fruit", "winey"),
  edge("honey", "caramel"),
  edge("caramel", "brown-sugar"),
  edge("brown-sugar", "dark-chocolate"),
  edge("almond", "hazelnut"),
  edge("hazelnut", "dark-chocolate"),
  edge("dark-chocolate", "cinnamon"),
  edge("dark-chocolate", "smoky"),
  edge("cinnamon", "tobacco"),
  edge("cedar", "earthy"),
  edge("earthy", "fermented"),
  edge("fermented", "winey"),
];

function edge(left: string, right: string): TypedEdge {
  return {
    left,
    right,
    layer: "G_ontology",
    edgeType: "REVIEWED_ONTOLOGY_EDGE",
    weight: 0.7,
    effectiveRecordCount: 0,
    sourceFamilyCount: 0,
    yearCount: 0,
    evidenceTier: "PROJECT_CURATED",
    rightsRegime: "REFERENCE_ONLY",
    reviewState: "PROJECT_CURATED_DRAFT",
  };
}

function pairKey(left: string, right: string): string {
  return [left, right].sort().join("|");
}

function validProfessionalEdge(edgeValue: TypedEdge): boolean {
  return (
    edgeValue.layer === "G_professional" &&
    edgeValue.edgeType === "PROFESSIONAL_COASSERTION_EDGE" &&
    edgeValue.effectiveRecordCount > 0 &&
    edgeValue.sourceFamilyCount > 0 &&
    edgeValue.yearCount > 0 &&
    (edgeValue.evidenceTier === "P1" || edgeValue.evidenceTier === "P2")
  );
}

export function communityEdgeCountsAsProfessional(
  edgeValue: TypedEdge,
): boolean {
  return validProfessionalEdge(edgeValue);
}

function shrunkenProfessionalWeight(edgeValue: TypedEdge): number {
  if (!validProfessionalEdge(edgeValue)) return 0;
  const support = edgeValue.effectiveRecordCount;
  const shrinkage = support / (support + 3);
  const diversity = Math.min(
    1,
    (edgeValue.sourceFamilyCount + edgeValue.yearCount) / 4,
  );
  return Math.max(0, edgeValue.weight) * shrinkage * (0.5 + diversity / 2);
}

function contextContribution(
  descriptor: Descriptor,
  input: CandidateInput,
): number {
  let score = CONTEXT_IDS[input.C0].includes(descriptor.id) ? 1.1 : 0;
  if (input.C1 <= 3 && LIGHT_ROAST_IDS.has(descriptor.id)) score += 0.7;
  if (input.C1 >= 5 && DARK_ROAST_IDS.has(descriptor.id)) score += 0.7;
  if (input.C1 === 4) score += 0.15;
  return score;
}

function answerContribution(
  descriptor: Descriptor,
  input: CandidateInput,
): number {
  const direct = input.answers.filter((answer) =>
    answer.descriptorIds.includes(descriptor.id),
  ).length;
  if (direct > 0) return 4 * direct;
  const answeredCategories = new Set(
    input.answers.flatMap((answer) =>
      answer.descriptorIds
        .map(
          (id) =>
            descriptors.find((candidate) => candidate.id === id)?.categoryId,
        )
        .filter((value): value is string => Boolean(value)),
    ),
  );
  return answeredCategories.has(descriptor.categoryId) ? 0.65 : 0;
}

function canonicalTarget(descriptor: Descriptor): string {
  return descriptor.id;
}

function evidenceLabel(score: number): CandidateScore["evidenceLabel"] {
  if (score >= 5) return "stronger evidence";
  if (score >= 2.4) return "moderate evidence";
  if (score >= 1.25) return "weaker evidence";
  if (score >= 0.85) return "secondary reference";
  return "insufficient evidence";
}

function baseScore(
  descriptor: Descriptor,
  input: CandidateInput,
): CandidateScore {
  const context = contextContribution(descriptor, input);
  const answer = answerContribution(descriptor, input);
  const directProfessional =
    input.professionalDirectIds?.includes(descriptor.id) ?? false;
  const source = directProfessional
    ? 2.5
    : descriptor.sourceIds.length > 0
      ? 0.2
      : 0;
  const total = context + answer + source;
  const weakContextOverride = answer >= 4 && context < 0.7;
  return {
    descriptorId: descriptor.id,
    canonicalTarget: canonicalTarget(descriptor),
    individualRelevance: total,
    contextContribution: context,
    answerContribution: answer,
    sourceContribution: source,
    professionalCoherenceContribution: 0,
    ontologyContribution: 0,
    communityContribution: 0,
    directEvidenceCoverage: answer > 0 || directProfessional ? 1 : 0,
    unsupportedOutlierPenalty: 0,
    redundancyPenalty: 0,
    total,
    evidenceLabel: evidenceLabel(total),
    uncertaintyReason: directProfessional
      ? "Direct professional reference support; strict model eligibility remains separate."
      : answer > 0
        ? "Direct answer support; candidate is not a calibrated probability."
        : context > 0
          ? "Context prior only; explicit answers may override it."
          : "Limited direct evidence.",
    overrideApplied: weakContextOverride,
  };
}

function graphIndex(edges: TypedEdge[]): Map<string, TypedEdge[]> {
  const index = new Map<string, TypedEdge[]>();
  for (const edgeValue of edges) {
    const key = pairKey(edgeValue.left, edgeValue.right);
    index.set(key, [...(index.get(key) ?? []), edgeValue]);
  }
  return index;
}

function selectionDelta(
  candidate: CandidateScore,
  selected: CandidateScore[],
  input: CandidateInput,
  professional: Map<string, TypedEdge[]>,
  ontology: Map<string, TypedEdge[]>,
  community: Map<string, TypedEdge[]>,
): CandidateScore {
  let professionalContribution = 0;
  let ontologyContribution = 0;
  let communityContribution = 0;
  const connected: string[] = [];
  for (const existing of selected) {
    const key = pairKey(candidate.descriptorId, existing.descriptorId);
    const professionalWeight = (professional.get(key) ?? []).reduce(
      (sum, edgeValue) => sum + shrunkenProfessionalWeight(edgeValue),
      0,
    );
    const ontologyWeight = (ontology.get(key) ?? []).reduce(
      (sum, edgeValue) => sum + Math.max(0, edgeValue.weight),
      0,
    );
    // Auxiliary community language can aid retrieval/explanation, but its
    // lower-authority contribution is capped and never becomes P1/P2.
    const communityWeight = Math.min(
      0.2,
      (community.get(key) ?? [])
        .filter((edgeValue) => edgeValue.layer === "G_community")
        .reduce((sum, edgeValue) => sum + Math.max(0, edgeValue.weight), 0) *
        0.1,
    );
    professionalContribution += professionalWeight;
    ontologyContribution += ontologyWeight;
    communityContribution += communityWeight;
    if (professionalWeight + ontologyWeight + communityWeight > 0)
      connected.push(existing.descriptorId);
  }

  const redundant = selected.some(
    (existing) => existing.canonicalTarget === candidate.canonicalTarget,
  );
  const redundancyPenalty = redundant ? 100 : 0;
  const hasDirect = candidate.directEvidenceCoverage > 0;
  const hasContext = candidate.contextContribution >= 0.7;
  const hasConnection = connected.length > 0;
  const unsupported =
    selected.length > 0 && !hasDirect && !hasContext && !hasConnection;
  const outlierPenalty = unsupported ? 2.25 : 0;
  const total =
    candidate.individualRelevance +
    professionalContribution * 1.2 +
    ontologyContribution * 0.7 +
    communityContribution * 0.2 +
    candidate.contextContribution * 0.15 +
    candidate.directEvidenceCoverage * 0.4 -
    outlierPenalty -
    redundancyPenalty;
  return {
    ...candidate,
    professionalCoherenceContribution: professionalContribution,
    ontologyContribution,
    communityContribution,
    unsupportedOutlierPenalty: outlierPenalty,
    redundancyPenalty,
    total,
    evidenceLabel: evidenceLabel(total),
  };
}

function connectionsFor(
  descriptorId: string,
  selected: CandidateScore[],
  indexes: Array<Map<string, TypedEdge[]>>,
): string[] {
  return selected
    .filter(
      (candidate) =>
        candidate.descriptorId !== descriptorId &&
        indexes.some((index) =>
          index.has(pairKey(descriptorId, candidate.descriptorId)),
        ),
    )
    .map((candidate) => candidate.descriptorId);
}

function componentMetrics(
  members: CandidateMember[],
): Pick<
  CandidateSetReceipt,
  | "connectedComponents"
  | "largestComponentShare"
  | "isolatedCandidateCount"
  | "bridgeCandidateCount"
> {
  if (members.length === 0) {
    return {
      connectedComponents: 0,
      largestComponentShare: 0,
      isolatedCandidateCount: 0,
      bridgeCandidateCount: 0,
    };
  }
  const adjacency = new Map(
    members.map((member) => [
      member.descriptorId,
      new Set(member.connectionsToSelected),
    ]),
  );
  const seen = new Set<string>();
  const sizes: number[] = [];
  for (const member of members) {
    if (seen.has(member.descriptorId)) continue;
    const queue = [member.descriptorId];
    let size = 0;
    while (queue.length > 0) {
      const current = queue.pop()!;
      if (seen.has(current)) continue;
      seen.add(current);
      size += 1;
      queue.push(...(adjacency.get(current) ?? []));
    }
    sizes.push(size);
  }
  return {
    connectedComponents: sizes.length,
    largestComponentShare: Math.max(...sizes) / members.length,
    isolatedCandidateCount: members.filter(
      (member) =>
        member.connectionsToSelected.length === 0 &&
        member.directEvidenceCoverage === 0 &&
        member.contextContribution === 0,
    ).length,
    bridgeCandidateCount: members.filter(
      (member) => member.connectionsToSelected.length >= 2,
    ).length,
  };
}

export function rankCandidateSet(input: CandidateInput): CandidateSetReceipt {
  if (!input.C0 || !C1_LEVELS.includes(input.C1)) {
    throw new Error("C0 and one of seven C1 levels are required");
  }
  const professionalEdges = (input.professionalEdges ?? []).filter(
    validProfessionalEdge,
  );
  const communityEdges = (input.communityEdges ?? []).filter(
    (edgeValue) =>
      edgeValue.layer === "G_community" &&
      edgeValue.edgeType === "COMMUNITY_LANGUAGE_EDGE",
  );
  const professional = graphIndex(professionalEdges);
  const ontology = graphIndex(ontologyEdges);
  const community = graphIndex(communityEdges);
  const allIndexes = [professional, ontology, community];
  const pool = descriptors
    .map((descriptor) => baseScore(descriptor, input))
    .sort(
      (left, right) =>
        right.total - left.total ||
        left.descriptorId.localeCompare(right.descriptorId),
    )
    .slice(0, 20);

  const selected: CandidateScore[] = [];
  while (selected.length < CANDIDATE_SET_SIZE) {
    const remaining = pool
      .filter(
        (candidate) =>
          !selected.some(
            (existing) => existing.descriptorId === candidate.descriptorId,
          ),
      )
      .map((candidate) =>
        selectionDelta(
          candidate,
          selected,
          input,
          professional,
          ontology,
          community,
        ),
      )
      .filter((candidate) => candidate.redundancyPenalty === 0)
      .filter(
        (candidate) =>
          candidate.total >= 0.85 || candidate.directEvidenceCoverage > 0,
      )
      .filter((candidate) => {
        const connectedToPrimary =
          connectionsFor(
            candidate.descriptorId,
            selected.slice(0, PRIMARY_CANDIDATE_COUNT),
            allIndexes,
          ).length > 0;
        if (selected.length < PRIMARY_CANDIDATE_COUNT) {
          return (
            candidate.individualRelevance >= 2.4 ||
            candidate.directEvidenceCoverage > 0 ||
            connectedToPrimary
          );
        }
        return candidate.directEvidenceCoverage > 0 || connectedToPrimary;
      })
      .sort(
        (left, right) =>
          right.total - left.total ||
          left.descriptorId.localeCompare(right.descriptorId),
      );
    if (remaining.length === 0) break;
    const next = remaining[0];
    if (!next) break;
    selected.push(next);
  }

  const members: CandidateMember[] = selected.map((candidate, index) => ({
    ...candidate,
    rank: index + 1,
    role: index < PRIMARY_CANDIDATE_COUNT ? "PRIMARY" : "SECONDARY",
    connectionsToSelected: connectionsFor(
      candidate.descriptorId,
      selected,
      allIndexes,
    ),
  }));
  const metrics = componentMetrics(members);
  return {
    ruleVersion: CANDIDATE_RULE_VERSION,
    objective: "M(S|x)",
    input,
    candidatePool: pool,
    selected: members,
    primaryCount: members.filter((member) => member.role === "PRIMARY").length,
    secondaryCount: members.filter((member) => member.role === "SECONDARY")
      .length,
    abstained: members.length < CANDIDATE_SET_SIZE,
    abstentionReason:
      members.length < CANDIDATE_SET_SIZE
        ? "Insufficient evidence for eight non-redundant candidates; no unsupported filler was added."
        : null,
    ...metrics,
    overrideReceipts: [
      ...members
        .filter((member) => member.overrideApplied)
        .map((member) => ({
          descriptorId: member.descriptorId,
          reason: "EXPLICIT_Q_EVIDENCE_OVERRIDES_WEAK_CONTEXT_PRIOR" as const,
        })),
      ...pool
        .filter(
          (candidate) =>
            candidate.directEvidenceCoverage > 0 &&
            !members.some(
              (member) => member.descriptorId === candidate.descriptorId,
            ),
        )
        .map((candidate) => ({
          descriptorId: candidate.descriptorId,
          reason: "STRONG_DIRECT_EVIDENCE_EXCLUDED_BY_FIXED_SET" as const,
        })),
    ],
    outlierReceipts: pool
      .filter(
        (candidate) =>
          !members.some(
            (member) => member.descriptorId === candidate.descriptorId,
          ),
      )
      .map((candidate) =>
        selectionDelta(
          candidate,
          selected,
          input,
          professional,
          ontology,
          community,
        ),
      )
      .filter((candidate) => candidate.unsupportedOutlierPenalty > 0)
      .map((candidate) => ({
        descriptorId: candidate.descriptorId,
        penalty: candidate.unsupportedOutlierPenalty,
        reason: "NO_PAIR_ONTOLOGY_CONTEXT_Q_OR_DIRECT_SOURCE_SUPPORT" as const,
      })),
    negativeEdgesStored: false,
    probabilityClaims: false,
    graphLayersKeptSeparate: true,
  };
}

export function requiresExceptionalQ5(
  input: Omit<CandidateInput, "answers"> & { answers: SensoryAnswer[] },
): boolean {
  const firstFour = input.answers.filter(
    (answer) => answer.questionId !== "Q5",
  );
  if (firstFour.length < 4) return false;
  const provisional = rankCandidateSet({ ...input, answers: firstFour });
  return (
    provisional.abstained ||
    provisional.selected.filter(
      (candidate) => candidate.evidenceLabel === "stronger evidence",
    ).length < 3
  );
}

export function questionPlan(
  input: CandidateInput,
): Array<SensoryAnswer["questionId"]> {
  const plan: Array<SensoryAnswer["questionId"]> = ["Q1", "Q2", "Q3", "Q4"];
  if (requiresExceptionalQ5(input)) plan.push("Q5");
  return plan;
}

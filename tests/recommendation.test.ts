import { describe, expect, it } from "vitest";
import {
  communityEdgeCountsAsProfessional,
  ontologyEdges,
  questionPlan,
  rankCandidateSet,
  type CandidateInput,
  type TypedEdge,
} from "flavor-data";

const answer = (
  questionId: "Q1" | "Q2" | "Q3" | "Q4" | "Q5",
  ...descriptorIds: string[]
) => ({
  questionId,
  descriptorIds,
  answerVersion: "round4a-q-v1",
});

const professional = (left: string, right: string, support = 8): TypedEdge => ({
  left,
  right,
  layer: "G_professional",
  edgeType: "PROFESSIONAL_COASSERTION_EDGE",
  weight: 1,
  effectiveRecordCount: support,
  sourceFamilyCount: 2,
  yearCount: 3,
  evidenceTier: "P2",
  rightsRegime: "REFERENCE_ONLY",
  reviewState: "GOVERNED_REFERENCE",
});

const base: CandidateInput = {
  C0: "filter",
  C1: 3,
  answers: [
    answer("Q1", "jasmine"),
    answer("Q2", "lemon"),
    answer("Q3", "green-tea"),
    answer("Q4", "honey"),
  ],
};

describe("coherence-aware deterministic candidate set", () => {
  it("adds positive professional support to a floral-citrus-tea set", () => {
    const receipt = rankCandidateSet({
      ...base,
      professionalEdges: [
        professional("jasmine", "lemon"),
        professional("lemon", "green-tea"),
      ],
    });
    expect(
      receipt.selected.find((row) => row.descriptorId === "lemon")
        ?.professionalCoherenceContribution,
    ).toBeGreaterThan(0);
  });

  it("allows a supported fruit-chocolate-spice multi-cluster profile", () => {
    const receipt = rankCandidateSet({
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
    });
    expect(receipt.selected.map((row) => row.descriptorId)).toEqual(
      expect.arrayContaining(["red-berries", "dark-chocolate", "cinnamon"]),
    );
    expect(receipt.connectedComponents).toBeGreaterThanOrEqual(1);
  });

  it("keeps rare direct Q evidence despite weak graph degree and records the override", () => {
    const receipt = rankCandidateSet({
      C0: "espresso",
      C1: 7,
      answers: [
        answer("Q1", "bellflower"),
        answer("Q2"),
        answer("Q3"),
        answer("Q4"),
      ],
    });
    expect(receipt.selected.map((row) => row.descriptorId)).toContain(
      "bellflower",
    );
    expect(receipt.overrideReceipts.map((row) => row.descriptorId)).toContain(
      "bellflower",
    );
  });

  it("requires every secondary candidate to connect to a primary or carry direct evidence", () => {
    const receipt = rankCandidateSet({
      ...base,
      professionalEdges: [
        professional("jasmine", "lemon"),
        professional("dark-chocolate", "cinnamon"),
      ],
      professionalDirectIds: ["dark-chocolate", "cinnamon"],
    });
    const secondary = receipt.selected.filter(
      (row) => row.role === "SECONDARY",
    );
    const primaryIds = new Set(
      receipt.selected
        .filter((row) => row.role === "PRIMARY")
        .map((row) => row.descriptorId),
    );
    expect(secondary).toHaveLength(3);
    expect(
      secondary.every(
        (row) =>
          row.connectionsToSelected.some((id) => primaryIds.has(id)) ||
          row.directEvidenceCoverage > 0,
      ),
    ).toBe(true);
    expect(receipt.connectedComponents).toBeGreaterThanOrEqual(1);
  });

  it("lets explicit answers override weak C0/C1 priors", () => {
    const receipt = rankCandidateSet({ ...base, C0: "espresso", C1: 7 });
    const jasmine = receipt.selected.find(
      (candidate) => candidate.descriptorId === "jasmine",
    );
    expect(jasmine).toBeDefined();
    expect(jasmine?.overrideApplied).toBe(true);
  });

  it("penalizes unsupported isolation and never treats missing pairs as negative edges", () => {
    const receipt = rankCandidateSet({
      C0: "unknown",
      C1: 4,
      answers: [answer("Q1", "jasmine")],
      professionalEdges: [],
    });
    expect(
      receipt.candidatePool.every(
        (row) => row.professionalCoherenceContribution === 0,
      ),
    ).toBe(true);
    expect(receipt.outlierReceipts.length).toBeGreaterThan(0);
    expect(receipt.outlierReceipts.every((row) => row.penalty > 0)).toBe(true);
    expect(receipt.negativeEdgesStored).toBe(false);
  });

  it("does not let community edges become professional evidence", () => {
    const community: TypedEdge = {
      ...professional("jasmine", "lemon"),
      layer: "G_community",
      edgeType: "COMMUNITY_LANGUAGE_EDGE",
      evidenceTier: "AUXILIARY",
      effectiveRecordCount: 20,
    };
    expect(communityEdgeCountsAsProfessional(community)).toBe(false);
  });

  it("keeps graph layers typed instead of collapsing adjacency", () => {
    expect(new Set(ontologyEdges.map((edge) => edge.layer))).toEqual(
      new Set(["G_ontology"]),
    );
    const receipt = rankCandidateSet({ ...base, communityEdges: [] });
    expect(receipt.graphLayersKeptSeparate).toBe(true);
    expect(receipt.probabilityClaims).toBe(false);
  });

  it("provides exactly five primary and three secondary candidates when evidence supports eight", () => {
    const receipt = rankCandidateSet(base);
    expect(receipt.abstained).toBe(false);
    expect(receipt.selected).toHaveLength(8);
    expect(receipt.primaryCount).toBe(5);
    expect(receipt.secondaryCount).toBe(3);
    expect(
      new Set(receipt.selected.map((row) => row.canonicalTarget)).size,
    ).toBe(8);
  });

  it("abstains rather than adding an unsupported eighth candidate", () => {
    const receipt = rankCandidateSet({ C0: "unknown", C1: 4, answers: [] });
    expect(receipt.abstained).toBe(true);
    expect(receipt.selected.length).toBeLessThan(8);
    expect(receipt.abstentionReason).toContain("no unsupported filler");
  });

  it("records an override when a fixed set excludes strong direct evidence", () => {
    const receipt = rankCandidateSet({
      C0: "filter",
      C1: 3,
      answers: [],
      professionalDirectIds: [
        "jasmine",
        "rose",
        "orange-blossom",
        "lemon",
        "orange",
        "green-tea",
        "honey",
        "red-berries",
        "blueberry",
      ],
    });
    expect(
      receipt.overrideReceipts.some(
        (row) => row.reason === "STRONG_DIRECT_EVIDENCE_EXCLUDED_BY_FIXED_SET",
      ),
    ).toBe(true);
  });

  it("asks Q5 only in exceptional conditions after Q1-Q4", () => {
    expect(
      questionPlan({
        C0: "unknown",
        C1: 4,
        answers: [answer("Q1"), answer("Q2"), answer("Q3"), answer("Q4")],
      }),
    ).toContain("Q5");
    expect(questionPlan(base)).not.toContain("Q5");
  });
});

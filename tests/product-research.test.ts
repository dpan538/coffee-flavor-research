import { readFileSync, readdirSync } from "node:fs";
import { createHash } from "node:crypto";
import { describe, expect, it } from "vitest";
import {
  answerCurrentQuestion,
  appendAnswer,
  assignVariant,
  candidateFrontier,
  createResearchState,
  eligibleQuestions,
  evaluate,
  nextStep,
  questionById,
  rankCandidates,
  researchCatalog,
  type ResearchState,
  type ResponseState,
} from "../packages/flavor-data/src/research";
import {
  productTaskCases,
  benchmarkResult,
} from "../packages/flavor-data/src/research/benchmark";
import {
  createSession,
  exportSession,
  sessionExportSchema,
  type QuestionEvent,
} from "../packages/flavor-data/src/research/session";

const add = (
  s: ResearchState,
  id: string,
  selected: string[],
  responseState: ResponseState = "SELECTED",
) =>
  appendAnswer(s, {
    questionId: id,
    selectedOptionIds: selected,
    responseState,
    optionIdsShown: questionById(id, s.variant).options.map((o) => o.id),
  });
const base = () => createResearchState("A");

describe("governed research policy v0.2", () => {
  it("preserves 8 families, 7 levels, 56 cells and 20 governed concepts", () => {
    expect(researchCatalog.preparations).toHaveLength(8);
    expect(researchCatalog.roasts).toHaveLength(7);
    expect(
      researchCatalog.preparations.length * researchCatalog.roasts.length,
    ).toBe(56);
    expect(researchCatalog.candidates).toHaveLength(20);
    expect(() => createResearchState("A", null, "UNSURE")).toThrow();
    expect(() => createResearchState("A", null, null)).not.toThrow();
  });
  it("assigns one deterministic variant from an identity-free study code", () => {
    for (let n = 1; n <= 100; n++) {
      const id = `R3O-${String(n).padStart(3, "0")}`;
      expect(assignVariant(id)).toBe(assignVariant(id));
    }
    expect(
      new Set([assignVariant("R3O-001"), assignVariant("R3O-002")]).size,
    ).toBe(2);
    expect(() => assignVariant("a person's name")).toThrow();
    expect(() => add(base(), "direction_B", ["fruit_flower"])).toThrow();
  });
  it("requires Q1 but permits an explicit typed escape; empty answers are not none", () => {
    expect(evaluate(base()).resultState).toBe("NEEDS_MANDATORY_Q1");
    expect(() => add(base(), "fruit_region", ["citrus"])).toThrow();
    expect(() => answerCurrentQuestion(base(), [], "SELECTED")).toThrow();
    expect(
      answerCurrentQuestion(base(), [], "SKIP").answers[0]?.responseState,
    ).toBe("SKIP");
  });
  it("changes only selected concepts for multi-select, leaving unselected ones neutral", () => {
    const before = rankCandidates(base());
    const state = answerCurrentQuestion(
      base(),
      ["fruit", "floral_tea"],
      "SELECTED",
    );
    const selected = new Set(
      questionById("direction_A", "A")
        .options.filter((o) => ["fruit", "floral_tea"].includes(o.id))
        .flatMap((o) => o.conceptIds),
    );
    for (const c of rankCandidates(state)) {
      expect(c.score - before.find((x) => x.id === c.id)!.score).toBeCloseTo(
        selected.has(c.id) ? 3 : 0,
      );
      expect(c.boundedNegative).toBe(0);
    }
  });
  it.each(["UNSURE", "SKIP"] as const)(
    "%s preserves scores exactly",
    (state) => {
      const s = answerCurrentQuestion(base(), ["fruit"], "SELECTED");
      expect(rankCandidates(add(s, "fruit_region", [], state))).toEqual(
        rankCandidates(s),
      );
    },
  );
  it("bounds NONE_OF_THESE to shown concepts and stores all three states distinctly", () => {
    const first = answerCurrentQuestion(base(), [], "UNSURE");
    const closed = new Set(
      questionById("fruit_region", "A").options.flatMap((o) => o.conceptIds),
    );
    const before = rankCandidates(first);
    const none = add(first, "fruit_region", [], "NONE_OF_THESE");
    for (const c of rankCandidates(none))
      expect(c.score - before.find((b) => b.id === c.id)!.score).toBeCloseTo(
        closed.has(c.id) ? -1.25 : 0,
      );
    expect(
      ["UNSURE", "NONE_OF_THESE", "SKIP"].map(
        (state) =>
          add(first, "fruit_region", [], state as ResponseState).answers[1]
            ?.responseState,
      ),
    ).toEqual(["UNSURE", "NONE_OF_THESE", "SKIP"]);
  });
  it("rejects contradictory transport states and selection IDs not shown", () => {
    expect(() => answerCurrentQuestion(base(), ["fruit"], "SKIP")).toThrow();
    expect(() =>
      answerCurrentQuestion(base(), ["fruit", "fruit"], "SELECTED"),
    ).toThrow();
    expect(() =>
      answerCurrentQuestion(base(), ["not-an-option"], "SELECTED"),
    ).toThrow();
  });
  it("does not call unlimited multi-select a conflict", () => {
    const state = answerCurrentQuestion(
      base(),
      questionById("direction_A", "A").options.map((o) => o.id),
      "SELECTED",
    );
    expect(evaluate(state).resultState).not.toBe("ABSTAINED_CONFLICT");
    expect(evaluate(state).headline).toHaveLength(3);
  });
  it("suppresses semantically duplicate axes despite different IDs and wording", () => {
    const s = add(
      answerCurrentQuestion(base(), ["fruit"], "SELECTED"),
      "fruit_region",
      ["berry"],
    );
    expect(() => add(s, "acidity_character", ["berry_like"])).toThrow();
    expect(
      eligibleQuestions(s).some((x) => x.question.id === "acidity_character"),
    ).toBe(false);
  });
  it("makes B branch specific and never exposes A in a B session", () => {
    const s = answerCurrentQuestion(
      createResearchState("B"),
      ["fruit_flower"],
      "SELECTED",
    );
    expect(nextStep(s).question?.id).toBe("fruit_flower_branch");
    expect(
      eligibleQuestions(s).every((x) => x.question.variants.includes("B")),
    ).toBe(true);
  });
  it("only chooses nonzero, governed separation that can alter visible output", () => {
    for (const c of productTaskCases())
      for (const option of eligibleQuestions(c.state)) {
        expect(option.separation).toBeGreaterThan(0);
        expect(option.question.governed).toBe(true);
        const results = option.question.options
          .map((o) => evaluate(add(c.state, option.question.id, [o.id])))
          .map((r) =>
            JSON.stringify([
              r.headline.map((x) => x.id),
              r.expandedMain.map((x) => x.id),
              r.exploration.map((x) => x.id),
            ]),
          );
        expect(new Set(results).size).toBeGreaterThan(1);
      }
  });
  it("requires a fourth completed answer, eligible split and explicit acceptance for Q5", () => {
    const s = productTaskCases().find((c) => c.id === "PT008")!.state;
    expect(s.answers).toHaveLength(4);
    expect(nextStep(s).recovery).toBe(true);
    expect(() => answerCurrentQuestion(s, [], "SKIP")).toThrow();
    const fifth = answerCurrentQuestion(s, [], "SKIP", true);
    expect(fifth.answers).toHaveLength(5);
    expect(nextStep(fifth).question).toBeNull();
    expect(() => answerCurrentQuestion(fifth, [], "SKIP", true)).toThrow();
    expect(nextStep({ ...s, openSet: true }).recovery).toBe(false);
    expect(nextStep({ ...s, answers: s.answers.slice(0, 3) }).recovery).toBe(
      false,
    );
  });
  it("stops ordinary paths early when enough supported headlines exist", () => {
    const c = productTaskCases()[0]!;
    expect(c.state.answers).toHaveLength(2);
    expect(nextStep(c.state).question).toBeNull();
  });
  it("keeps C1 neutral at every level and when unsure, independently of C0", () => {
    const s = {
      ...answerCurrentQuestion(base(), ["sweet_nut_cocoa"], "SELECTED"),
      c0: researchCatalog.preparations[0]!.id,
    };
    for (const c1 of [...researchCatalog.roasts.map((r) => r.id), null])
      expect(rankCandidates({ ...s, c1 })).toEqual(rankCandidates(s));
    expect(rankCandidates(s).some((c) => c.context < 0 && c.support > 0)).toBe(
      true,
    );
    expect(
      evaluate(s).headline.some((c) => c.context < 0 && c.support > 0),
    ).toBe(true);
  });
  it("excludes blocked, unresolved and review-only candidates from headlines", () => {
    const s = answerCurrentQuestion(
      base(),
      questionById("direction_A", "A").options.map((o) => o.id),
      "SELECTED",
    );
    const r = evaluate(s);
    expect(
      [...r.headline, ...r.expandedMain, ...r.exploration].every(
        (c) => c.rightsEligible,
      ),
    ).toBe(true);
    const blocked = evaluate(
      s,
      researchCatalog.candidates.map((c) => ({ ...c, rightsEligible: false })),
    );
    expect(blocked.headline).toHaveLength(0);
    expect(blocked.resultState).toBe("ABSTAINED_RIGHTS_BLOCKED");
    const review = evaluate(
      s,
      researchCatalog.candidates.map((c) => ({
        ...c,
        reviewOnly: true,
        directSupport: 0,
        governedSupport: 0,
      })),
    );
    expect(review.headline).toHaveLength(0);
    expect(review.exploration.length).toBeGreaterThan(0);
    expect(
      evaluate(
        s,
        researchCatalog.candidates.map((c) => ({ ...c, unresolved: true })),
      ).headline,
    ).toHaveLength(0);
  });
  it("retains partial, complete abstention, open-set and conflict paths without force-fill", () => {
    const cases = productTaskCases();
    expect(cases).toHaveLength(28);
    for (const c of cases) {
      const r = benchmarkResult(c);
      expect(r.headline.length).toBeLessThanOrEqual(3);
      expect(r.expandedMain.length).toBeLessThanOrEqual(2);
      expect(r.exploration.length).toBeLessThanOrEqual(3);
      const all = [...r.headline, ...r.expandedMain, ...r.exploration];
      expect(new Set(all).size).toBe(all.length);
      expect(
        new Set(
          all.map(
            (id) => c.candidates.find((x) => x.id === id)!.redundancyGroup,
          ),
        ).size,
      ).toBe(all.length);
    }
    expect(benchmarkResult(cases[4]!).headline).toHaveLength(1);
    expect(benchmarkResult(cases[9]!).resultState).toBe("ABSTAINED_OPEN_SET");
    expect(benchmarkResult(cases[10]!).resultState).toBe("ABSTAINED_CONFLICT");
  });
});

describe("local research export", () => {
  function fixture() {
    const s = createSession(
      "R3O-001",
      "a31f28f2-b7c8-4304-bd97-80414499f3df",
      "novice",
      100,
    );
    s.state.c0 = researchCatalog.preparations[0]!.id;
    const before = candidateFrontier(s.state);
    const step = nextStep(s.state);
    s.state = answerCurrentQuestion(s.state, ["fruit"], "SELECTED");
    const after = candidateFrontier(s.state);
    const event: QuestionEvent = {
      questionId: step.question!.id,
      semanticKey: step.question!.semanticKey,
      optionIdsShown: step.question!.options.map((o) => o.id),
      selectedOptionIds: ["fruit"],
      responseState: "SELECTED",
      responseTimeMs: 300,
      candidateIdsBefore: before,
      candidateIdsAfter: after,
      candidateCountBefore: before.length,
      candidateCountAfter: after.length,
      selectedOptionCount: 1,
      allOptionsSelected: false,
      remainingEligibleAxes: eligibleQuestions(s.state).map(
        (x) => x.question.id,
      ),
      selectionReason: step.reason,
    };
    s.questions = [event];
    return exportSession(
      s,
      3,
      {
        firstQuestionComprehension: "clear",
        partialOutputAcceptance: "accept",
        reuseIntent: "maybe",
        completedWithoutHelp: true,
        difficulty: "none",
      },
      1000,
    );
  }
  it("exports typed counts, timings, variant and no personal-identity fields", () => {
    const record = fixture();
    expect(record.totalQuestionCount).toBe(1);
    expect(record.c1Unsure).toBe(true);
    expect(record.completionTimeMs).toBe(900);
    const jsonSchema = JSON.parse(
      readFileSync(
        new URL(
          "../db/data/product-inference-v0.2/PRODUCT_RESEARCH_EVENT_SCHEMA.json",
          import.meta.url,
        ),
        "utf8",
      ),
    );
    expect(jsonSchema.required.sort()).toEqual(Object.keys(record).sort());
    expect(jsonSchema.properties.questions.items.required.sort()).toEqual(
      Object.keys(record.questions[0]!).sort(),
    );
    expect(jsonSchema.additionalProperties).toBe(false);
    expect(() =>
      sessionExportSchema.parse({ ...record, name: "personal name" }),
    ).toThrow();
    expect(() =>
      sessionExportSchema.parse({
        ...record,
        participantResearchId: "personal name",
      }),
    ).toThrow();
    expect(() =>
      sessionExportSchema.parse({ ...record, languageVariant: "B" }),
    ).toThrow();
    expect(() =>
      sessionExportSchema.parse({
        ...record,
        totalQuestionCount: 5,
        q5Accepted: true,
      }),
    ).toThrow();
    expect(() =>
      sessionExportSchema.parse({ ...record, c1Unsure: false }),
    ).toThrow();
  });
  it("rejects unrecognized identity and endpoint fields in the retained contract", () => {
    for (const key of ["personalName", "remoteEndpoint"])
      expect(
        sessionExportSchema.safeParse({ ...fixture(), [key]: "disallowed" })
          .success,
      ).toBe(false);
  });
  it("rejects tampered event IDs, counters, output and replay states", () => {
    const record = fixture();
    const event = record.questions[0]!;
    expect(
      sessionExportSchema.safeParse({
        ...record,
        questions: [{ ...event, questionId: "unknown" }],
      }).success,
    ).toBe(false);
    expect(
      sessionExportSchema.safeParse({
        ...record,
        questions: [{ ...event, allOptionsSelected: true }],
      }).success,
    ).toBe(false);
    expect(
      sessionExportSchema.safeParse({
        ...record,
        questions: [
          {
            ...event,
            candidateIdsAfter: ["untracked"],
            candidateCountAfter: 1,
          },
        ],
      }).success,
    ).toBe(false);
    expect(
      sessionExportSchema.safeParse({ ...record, headlineResultCount: 3 })
        .success,
    ).toBe(false);
    expect(
      sessionExportSchema.safeParse({
        ...record,
        earlyStopReason: "PARTICIPANT_REPORTED_OPEN_SET",
      }).success,
    ).toBe(false);
  });
});

describe("public checkpoint package", () => {
  it("checksum-covers all four artifact directories", () => {
    for (const folder of [
      "user-research-round1",
      "product-inference-v0.2",
      "product-benchmark-v0.2",
      "product-gap-mining-v0.2",
    ]) {
      const root = new URL(`../db/data/${folder}/`, import.meta.url);
      const lines = readFileSync(new URL("SHA256SUMS", root), "utf8")
        .trim()
        .split("\n");
      expect(lines.map((r) => r.slice(66)).sort()).toEqual(
        readdirSync(root)
          .filter((f) => f !== "SHA256SUMS")
          .sort(),
      );
      for (const line of lines)
        expect(
          createHash("sha256")
            .update(readFileSync(new URL(line.slice(66), root)))
            .digest("hex"),
        ).toBe(line.slice(0, 64));
    }
  });
});

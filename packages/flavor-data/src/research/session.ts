import { z } from "zod";
import {
  assignVariant,
  answerCurrentQuestion,
  candidateFrontier,
  createResearchState,
  eligibleQuestions,
  evaluate,
  nextStep,
  researchCatalog,
  type ResearchState,
} from "./index";

const ms = z.number().int().nonnegative();
const ids = z.array(z.string());
const questionEventSchema = z
  .object({
    questionId: z.string(),
    semanticKey: z.string(),
    optionIdsShown: ids,
    selectedOptionIds: ids,
    responseState: z.enum(["SELECTED", "UNSURE", "NONE_OF_THESE", "SKIP"]),
    responseTimeMs: ms,
    candidateIdsBefore: ids,
    candidateIdsAfter: ids,
    candidateCountBefore: ms,
    candidateCountAfter: ms,
    selectedOptionCount: ms,
    allOptionsSelected: z.boolean(),
    remainingEligibleAxes: ids,
    selectionReason: z.string(),
  })
  .strict();
export type QuestionEvent = z.infer<typeof questionEventSchema>;

export const postTaskSchema = z
  .object({
    firstQuestionComprehension: z.enum(["clear", "partial", "unclear"]),
    partialOutputAcceptance: z.enum([
      "accept",
      "unsure",
      "reject",
      "not_applicable",
    ]),
    reuseIntent: z.enum(["yes", "maybe", "no"]),
    completedWithoutHelp: z.boolean(),
    difficulty: z.enum(["none", "context", "wording", "choices", "results"]),
  })
  .strict();
export type PostTask = z.infer<typeof postTaskSchema>;
export type Stratum = "novice" | "regular" | "experienced";
export type Paraphrase = "correct" | "partial" | "incorrect" | "not_assessed";

export const sessionExportSchema = z
  .object({
    version: z.literal("product-inference-v0.2"),
    sessionId: z.uuid(),
    participantResearchId: z.string().regex(/^R3O-\d{3}$/),
    coffeeExposureStratum: z.enum(["novice", "regular", "experienced"]),
    languageVariant: z.enum(["A", "B"]),
    c0Selection: z
      .string()
      .refine((id) => researchCatalog.preparations.some((p) => p.id === id)),
    c0SelectionTimeMs: ms,
    c1Selection: z
      .string()
      .nullable()
      .refine(
        (id) => id === null || researchCatalog.roasts.some((r) => r.id === id),
      ),
    c1Unsure: z.boolean(),
    c1SelectionTimeMs: ms,
    questions: z.array(questionEventSchema).min(1).max(5),
    totalQuestionCount: ms,
    averageSelectedCount: z.number().nonnegative(),
    q5Offered: z.boolean(),
    q5Accepted: z.boolean(),
    headlineResultCount: ms.max(3),
    expandedMainCount: ms.max(2),
    explorationCount: ms.max(3),
    expandClicked: z.boolean(),
    extraQuestionClicked: z.boolean(),
    resultHelpfulness: z.number().int().min(1).max(5),
    valuePropositionParaphraseResult: z.enum([
      "correct",
      "partial",
      "incorrect",
      "not_assessed",
    ]),
    completionTimeMs: ms,
    earlyStopReason: z.string(),
    q5TriggerReason: z.string(),
    openSet: z.boolean(),
    resultState: z.string(),
    postTask: postTaskSchema,
  })
  .strict()
  .superRefine((session, ctx) => {
    const invalid = (message: string) =>
      ctx.addIssue({ code: "custom", message });
    if (
      /^R3O-\d{3}$/.test(session.participantResearchId) &&
      assignVariant(session.participantResearchId) !== session.languageVariant
    )
      invalid("Variant assignment changed");
    if (session.c1Unsure !== (session.c1Selection === null))
      invalid("C1 unsure must be a null selection");
    if (session.questions.length !== session.totalQuestionCount)
      invalid("Question count mismatch");
    if (
      session.q5Accepted &&
      (!session.q5Offered ||
        session.totalQuestionCount < 4 ||
        !session.extraQuestionClicked)
    )
      invalid("Q5 acceptance mismatch");
    if (session.totalQuestionCount === 5 && !session.q5Accepted)
      invalid("Fifth question requires opt-in");
    if (session.extraQuestionClicked !== session.q5Accepted)
      invalid("Recovery click and acceptance disagree");
    if (
      new Set(session.questions.map((q) => q.semanticKey)).size !==
      session.questions.length
    )
      invalid("Repeated semantic question");
    if (
      session.questions[0]?.questionId !==
      `direction_${session.languageVariant}`
    )
      invalid("Q1 missing");
    const average =
      session.questions.reduce((n, q) => n + q.selectedOptionCount, 0) /
      session.questions.length;
    if (Math.abs(average - session.averageSelectedCount) > 1e-8)
      invalid("Average selection count mismatch");
    for (const q of session.questions) {
      if (
        q.selectedOptionCount !== q.selectedOptionIds.length ||
        q.candidateCountBefore !== q.candidateIdsBefore.length ||
        q.candidateCountAfter !== q.candidateIdsAfter.length
      )
        invalid("Event count mismatch");
      if (q.selectedOptionIds.some((id) => !q.optionIdsShown.includes(id)))
        invalid("Selection outside shown set");
      if (q.responseState !== "SELECTED" && q.selectedOptionCount !== 0)
        invalid("No-answer state contains selections");
      if (q.responseState === "SELECTED" && q.selectedOptionCount === 0)
        invalid("Empty selection is not NONE_OF_THESE");
    }
    const same = (a: unknown, b: unknown) =>
      JSON.stringify(a) === JSON.stringify(b);
    try {
      let replay = createResearchState(
        session.languageVariant,
        session.c0Selection,
        session.c1Selection,
      );
      let offered = false;
      for (const event of session.questions) {
        const step = nextStep(replay);
        const question = step.question;
        if (
          !question ||
          question.id !== event.questionId ||
          question.semanticKey !== event.semanticKey
        ) {
          invalid("Recorded question does not match deterministic flow");
          return;
        }
        if (
          !same(
            question.options.map((o) => o.id),
            event.optionIdsShown,
          ) ||
          event.selectionReason !== step.reason
        )
          invalid("Question presentation or reason mismatch");
        if (!same(candidateFrontier(replay), event.candidateIdsBefore))
          invalid("Candidate state before does not replay");
        if (
          event.allOptionsSelected !==
          (event.selectedOptionIds.length === question.options.length)
        )
          invalid("All-options-selected flag mismatch");
        replay = answerCurrentQuestion(
          replay,
          event.selectedOptionIds,
          event.responseState,
          session.q5Accepted,
        );
        if (!same(candidateFrontier(replay), event.candidateIdsAfter))
          invalid("Candidate state after does not replay");
        if (
          !same(
            eligibleQuestions(replay).map((q) => q.question.id),
            event.remainingEligibleAxes,
          )
        )
          invalid("Remaining question axes do not replay");
        offered ||= nextStep(replay).recovery;
      }
      if (session.q5Offered !== offered) invalid("Q5 offer does not replay");
      const expectedTrigger = offered
        ? "Q5_FEWER_THAN_THREE_HEADLINES_AND_MATERIAL_SEPARATION"
        : "";
      if (session.q5TriggerReason !== expectedTrigger)
        invalid("Q5 trigger mismatch");
      replay.openSet = session.openSet;
      const result = evaluate(replay);
      if (
        result.resultState !== session.resultState ||
        result.headline.length !== session.headlineResultCount ||
        result.expandedMain.length !== session.expandedMainCount ||
        result.exploration.length !== session.explorationCount
      )
        invalid("Visible results do not replay");
      if (
        !session.openSet &&
        session.earlyStopReason === "PARTICIPANT_REPORTED_OPEN_SET"
      )
        invalid("Stale open-set stop reason");
    } catch {
      invalid("Session cannot be replayed under the recorded policy");
    }
  });

export type SessionExport = z.infer<typeof sessionExportSchema>;
export type Session = {
  state: ResearchState;
  participantResearchId: string;
  sessionId: string;
  coffeeExposureStratum: Stratum;
  startedAt: number;
  c0SelectionTimeMs: number;
  c1SelectionTimeMs: number;
  questions: QuestionEvent[];
  q5Offered: boolean;
  q5Accepted: boolean;
  q5TriggerReason: string;
  earlyStopReason: string;
  expandClicked: boolean;
  extraQuestionClicked: boolean;
  valuePropositionParaphraseResult: Paraphrase;
};

export function createSession(
  id: string,
  sessionId: string,
  stratum: Stratum,
  startedAt: number,
): Session {
  return {
    state: createResearchState(assignVariant(id)),
    participantResearchId: id,
    sessionId,
    coffeeExposureStratum: stratum,
    startedAt,
    c0SelectionTimeMs: 0,
    c1SelectionTimeMs: 0,
    questions: [],
    q5Offered: false,
    q5Accepted: false,
    q5TriggerReason: "",
    earlyStopReason: "",
    expandClicked: false,
    extraQuestionClicked: false,
    valuePropositionParaphraseResult: "not_assessed",
  };
}

export function exportSession(
  session: Session,
  helpfulness: number,
  postTask: PostTask,
  endedAt: number,
): SessionExport {
  const recorded = session.questions.map(
    ({ questionId, optionIdsShown, selectedOptionIds, responseState }) => ({
      questionId,
      optionIdsShown,
      selectedOptionIds,
      responseState,
    }),
  );
  const answers = session.state.answers.map(
    ({ questionId, optionIdsShown, selectedOptionIds, responseState }) => ({
      questionId,
      optionIdsShown,
      selectedOptionIds,
      responseState,
    }),
  );
  if (JSON.stringify(recorded) !== JSON.stringify(answers))
    throw new Error("Recorded events and inference answers disagree");
  const result = evaluate(session.state);
  // Explicit allowlist: additions to in-memory session state never leak into exports.
  return sessionExportSchema.parse({
    version: "product-inference-v0.2",
    sessionId: session.sessionId,
    participantResearchId: session.participantResearchId,
    coffeeExposureStratum: session.coffeeExposureStratum,
    languageVariant: session.state.variant,
    c0Selection: session.state.c0,
    c0SelectionTimeMs: session.c0SelectionTimeMs,
    c1Selection: session.state.c1,
    c1Unsure: session.state.c1 === null,
    c1SelectionTimeMs: session.c1SelectionTimeMs,
    questions: session.questions,
    totalQuestionCount: session.questions.length,
    averageSelectedCount:
      session.questions.reduce((sum, q) => sum + q.selectedOptionCount, 0) /
      session.questions.length,
    q5Offered: session.q5Offered,
    q5Accepted: session.q5Accepted,
    headlineResultCount: result.headline.length,
    expandedMainCount: result.expandedMain.length,
    explorationCount: result.exploration.length,
    expandClicked: session.expandClicked,
    extraQuestionClicked: session.extraQuestionClicked,
    resultHelpfulness: helpfulness,
    valuePropositionParaphraseResult: session.valuePropositionParaphraseResult,
    completionTimeMs: Math.max(0, Math.round(endedAt - session.startedAt)),
    earlyStopReason: session.earlyStopReason,
    q5TriggerReason: session.q5TriggerReason,
    openSet: session.state.openSet,
    resultState: result.resultState,
    postTask,
  });
}

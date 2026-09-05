import catalog from "../../../../db/data/product-inference-v0.2/PRODUCT_RUNTIME_CATALOG.json" with { type: "json" };

export type Variant = "A" | "B";
export type ResponseState = "SELECTED" | "UNSURE" | "NONE_OF_THESE" | "SKIP";
export type Candidate = (typeof catalog.candidates)[number];
export type Question = (typeof catalog.questions)[number];
export type Answer = {
  questionId: string;
  optionIdsShown: string[];
  selectedOptionIds: string[];
  responseState: ResponseState;
};
export type ResearchState = {
  variant: Variant;
  c0: string | null;
  c1: string | null;
  answers: Answer[];
  openSet: boolean;
};
export type RankedCandidate = Candidate & {
  support: number;
  boundedNegative: number;
  context: number;
  score: number;
};

export const researchCatalog = catalog;
export const policy = catalog.policy;
export const noAnswerLabels = {
  UNSURE: "不确定",
  NONE_OF_THESE: "都不像",
  SKIP: "跳过",
} as const;

export function assignVariant(researchId: string): Variant {
  if (!/^R3O-\d{3}$/.test(researchId))
    throw new Error("请使用 R3O-001 这样的研究编号");
  // The study codes are allocated sequentially before exposure. This balances
  // A/B by parity without collecting names or randomizing on every render.
  return Number(researchId.slice(-3)) % 2 === 0 ? "B" : "A";
}

export function createResearchState(
  variant: Variant,
  c0: string | null = null,
  c1: string | null = null,
): ResearchState {
  if (c0 !== null && !catalog.preparations.some((p) => p.id === c0))
    throw new Error("Unknown C0");
  if (c1 !== null && !catalog.roasts.some((r) => r.id === c1))
    throw new Error("Unknown C1");
  return { variant, c0, c1, answers: [], openSet: false };
}

export function questionById(id: string, variant: Variant): Question {
  const question = catalog.questions.find(
    (q) => q.id === id && q.variants.includes(variant),
  );
  if (!question)
    throw new Error("Question is outside this session's language variant");
  return question;
}

export function appendAnswer(
  state: ResearchState,
  answer: Answer,
): ResearchState {
  const question = questionById(answer.questionId, state.variant);
  if (state.answers.length >= policy.recoveryMax)
    throw new Error("Five-question maximum");
  if (!state.answers.length && question.id !== `direction_${state.variant}`)
    throw new Error("Q1 is mandatory");
  if (
    state.answers.some(
      (a) =>
        questionById(a.questionId, state.variant).semanticKey ===
        question.semanticKey,
    )
  ) {
    throw new Error("This semantic distinction has already been answered");
  }
  const shown = question.options.map((o) => o.id);
  if (
    shown.length !== answer.optionIdsShown.length ||
    new Set(answer.optionIdsShown).size !== shown.length ||
    !shown.every((id) => answer.optionIdsShown.includes(id))
  ) {
    throw new Error("Shown options must exactly match the presented question");
  }
  if (
    new Set(answer.selectedOptionIds).size !==
      answer.selectedOptionIds.length ||
    answer.selectedOptionIds.some((id) => !shown.includes(id))
  ) {
    throw new Error(
      "Selected options must be unique members of the displayed list",
    );
  }
  if (
    answer.responseState === "SELECTED"
      ? answer.selectedOptionIds.length === 0
      : answer.selectedOptionIds.length !== 0
  ) {
    throw new Error("A typed no-answer state cannot contain selected options");
  }
  if (
    !["SELECTED", "UNSURE", "NONE_OF_THESE", "SKIP"].includes(
      answer.responseState,
    )
  )
    throw new Error("Unknown response state");
  return {
    ...state,
    answers: [
      ...state.answers,
      {
        ...answer,
        selectedOptionIds: [...answer.selectedOptionIds],
        optionIdsShown: [...answer.optionIdsShown],
      },
    ],
  };
}

export function rankCandidates(
  state: ResearchState,
  candidates: Candidate[] = catalog.candidates,
): RankedCandidate[] {
  return candidates
    .map((candidate) => {
      let support = 0;
      let boundedNegative = 0;
      for (const answer of state.answers) {
        const question = questionById(answer.questionId, state.variant);
        const represented = (ids: string[]) =>
          question.options.some(
            (o) => ids.includes(o.id) && o.conceptIds.includes(candidate.id),
          );
        if (
          answer.responseState === "SELECTED" &&
          represented(answer.selectedOptionIds)
        )
          support += policy.positive;
        if (
          answer.responseState === "NONE_OF_THESE" &&
          represented(answer.optionIdsShown)
        )
          boundedNegative += policy.boundedNone;
      }
      // Roast, including an unsure/null roast, never changes this source-local C0 prior.
      const context =
        catalog.c0Priors.find(
          (p) => p.preparation === state.c0 && p.conceptId === candidate.id,
        )?.adjustment ?? 0;
      return {
        ...candidate,
        support,
        boundedNegative,
        context,
        score: candidate.baseScore + support + boundedNegative + context,
      };
    })
    .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id, "en"));
}

export function evaluate(
  state: ResearchState,
  candidates: Candidate[] = catalog.candidates,
) {
  const ranked = rankCandidates(state, candidates);
  const positive = ranked.filter((c) => c.support > 0);
  const rights = positive.filter((c) => c.rightsEligible && !c.unresolved);
  const conflict =
    rights.length > 0 && rights.every((c) => c.boundedNegative < 0);
  const resultState = !state.answers.length
    ? "NEEDS_MANDATORY_Q1"
    : state.openSet
      ? "ABSTAINED_OPEN_SET"
      : conflict
        ? "ABSTAINED_CONFLICT"
        : positive.length && !rights.length
          ? "ABSTAINED_RIGHTS_BLOCKED"
          : "EVALUATED";
  const headline: RankedCandidate[] = [];
  const expandedMain: RankedCandidate[] = [];
  const exploration: RankedCandidate[] = [];
  const groups = new Set<string>();
  if (resultState === "EVALUATED") {
    // Contradicted candidates remain in the scored state but are withheld from
    // visible assertions. A weak closed-list response is never a global label.
    const eligible = rights.filter(
      (c) => c.support + c.boundedNegative > 0 && c.boundedNegative === 0,
    );
    for (const c of eligible.filter(
      (c) =>
        !c.reviewOnly &&
        c.directSupport >= policy.mainDirectSupportMin &&
        c.governedSupport > 0,
    )) {
      if (groups.has(c.redundancyGroup)) continue;
      if (headline.length < policy.headlineMax) headline.push(c);
      else if (expandedMain.length < policy.expandedMainMax)
        expandedMain.push(c);
      else continue;
      groups.add(c.redundancyGroup);
    }
    for (const c of eligible) {
      if (
        groups.has(c.redundancyGroup) ||
        exploration.length >= policy.explorationMax
      )
        continue;
      exploration.push(c);
      groups.add(c.redundancyGroup);
    }
  }
  return {
    ranked,
    headline,
    expandedMain,
    exploration,
    resultState:
      resultState !== "EVALUATED"
        ? resultState
        : headline.length
          ? "SUPPORTED_PARTIAL_OUTPUT"
          : exploration.length
            ? "EXPLORATION_ONLY"
            : "ABSTAINED_INSUFFICIENT_EVIDENCE",
  };
}

export function candidateFrontier(state: ResearchState): string[] {
  const ranked = rankCandidates(state).filter(
    (c) => c.rightsEligible && !c.unresolved,
  );
  const positive = ranked.filter(
    (c) => c.support > 0 && c.boundedNegative === 0,
  );
  // This is an evidence-supported working set, not deletion of unselected
  // concepts. Neutral candidates retain their original score components.
  return (positive.length ? positive : ranked).map((c) => c.id).sort();
}

function signature(state: ResearchState): string {
  const r = evaluate(state);
  return [r.headline, r.expandedMain, r.exploration]
    .map((tier) => tier.map((c) => c.id).join(","))
    .join(";");
}

export function eligibleQuestions(state: ResearchState) {
  if (state.answers.length === 0) return [];
  if (
    state.openSet ||
    evaluate(state).resultState === "ABSTAINED_CONFLICT" ||
    state.answers.length >= policy.recoveryMax
  )
    return [];
  const frontier = new Set(candidateFrontier(state));
  const used = new Set(
    state.answers.map(
      (a) => questionById(a.questionId, state.variant).semanticKey,
    ),
  );
  const current = signature(state);
  return catalog.questions
    .filter(
      (q) =>
        q.variants.includes(state.variant) &&
        q.governed &&
        !used.has(q.semanticKey) &&
        q.semanticKey !== "family-direction",
    )
    .flatMap((question) => {
      if (
        question.id === "fruit_flower_branch" &&
        !(
          state.answers.length === 1 &&
          state.answers[0]?.selectedOptionIds.includes("fruit_flower")
        )
      )
        return [];
      const sizes = question.options
        .map((o) => o.conceptIds.filter((id) => frontier.has(id)).length)
        .filter((size) => size > 0);
      if (sizes.length < 2) return [];
      const total = sizes.reduce((a, b) => a + b, 0);
      const separation =
        1 - sizes.reduce((sum, n) => sum + (n / total) ** 2, 0);
      if (separation <= 0) return [];
      const hypothetical = question.options
        .filter((o) => o.conceptIds.some((id) => frontier.has(id)))
        .map((o) =>
          signature(
            appendAnswer(state, {
              questionId: question.id,
              optionIdsShown: question.options.map((x) => x.id),
              selectedOptionIds: [o.id],
              responseState: "SELECTED",
            }),
          ),
        );
      if (
        new Set(hypothetical).size < 2 ||
        !hypothetical.some((s) => s !== current)
      )
        return [];
      return [
        {
          question,
          separation,
          reason:
            question.id === "fruit_flower_branch"
              ? "B_BRANCH_SEPARATES_FRUIT_FLOWER_TEA"
              : `GOVERNED_UNUSED_AXIS;LIVE_PARTITIONS=${sizes.length};VISIBLE_OUTPUT_CAN_CHANGE`,
        },
      ];
    })
    .sort(
      (a, b) =>
        Number(b.question.id === "fruit_flower_branch") -
          Number(a.question.id === "fruit_flower_branch") ||
        b.separation - a.separation ||
        a.question.id.localeCompare(b.question.id, "en"),
    );
}

export function nextStep(state: ResearchState) {
  if (!state.answers.length)
    return {
      question: questionById(`direction_${state.variant}`, state.variant),
      reason: "MANDATORY_Q1",
      recovery: false,
    };
  const result = evaluate(state);
  if (state.openSet || result.resultState === "ABSTAINED_CONFLICT")
    return { question: null, reason: result.resultState, recovery: false };
  if (state.answers.length >= policy.recoveryMax)
    return { question: null, reason: "FIVE_QUESTION_LIMIT", recovery: false };
  const next = eligibleQuestions(state)[0];
  if (!next)
    return {
      question: null,
      reason: "NO_MATERIAL_UNUSED_AXIS",
      recovery: false,
    };
  if (state.answers.length === policy.ordinaryMax) {
    return result.headline.length < 3
      ? {
          question: next.question,
          reason: "Q5_FEWER_THAN_THREE_HEADLINES_AND_MATERIAL_SEPARATION",
          recovery: true,
        }
      : { question: null, reason: "ORDINARY_QUESTION_LIMIT", recovery: false };
  }
  if (state.answers.length >= 2 && result.headline.length >= 3)
    return {
      question: null,
      reason: "THREE_SUPPORTED_HEADLINES",
      recovery: false,
    };
  return { question: next.question, reason: next.reason, recovery: false };
}

export function answerCurrentQuestion(
  state: ResearchState,
  selectedOptionIds: string[],
  responseState: ResponseState,
  acceptRecovery = false,
): ResearchState {
  const step = nextStep(state);
  if (!step.question || (step.recovery && !acceptRecovery))
    throw new Error(
      "No authorized next question; recovery requires explicit acceptance",
    );
  return appendAnswer(state, {
    questionId: step.question.id,
    optionIdsShown: step.question.options.map((o) => o.id),
    selectedOptionIds,
    responseState,
  });
}

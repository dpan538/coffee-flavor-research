import {
  appendAnswer,
  answerCurrentQuestion,
  createResearchState,
  evaluate,
  nextStep,
  questionById,
  researchCatalog,
  type Candidate,
  type ResearchState,
  type ResponseState,
  type Variant,
} from "./index";

export type BenchmarkCase = {
  id: string;
  category: string;
  purpose: string;
  state: ResearchState;
  candidates: Candidate[];
  harnessReachable: boolean;
  expectedError: string;
};
const c0 = researchCatalog.preparations;
function answer(
  state: ResearchState,
  id: string,
  selected: string[] = [],
  responseState: ResponseState = "SELECTED",
) {
  const q = questionById(id, state.variant);
  return appendAnswer(state, {
    questionId: id,
    optionIdsShown: q.options.map((o) => o.id),
    selectedOptionIds: selected,
    responseState,
  });
}

export function productTaskCases(): BenchmarkCase[] {
  const cases: BenchmarkCase[] = [];
  function add(
    category: string,
    purpose: string,
    state: ResearchState,
    harnessReachable = false,
    candidates: Candidate[] = researchCatalog.candidates,
    expectedError = "",
  ) {
    cases.push({
      id: `PT${String(cases.length + 1).padStart(3, "0")}`,
      category,
      purpose,
      state,
      candidates,
      harnessReachable,
      expectedError,
    });
  }
  function ordinary(
    variant: Variant,
    first: string[],
    later: "all" | "unsure" | "first" = "first",
  ) {
    let state = answerCurrentQuestion(
      createResearchState(variant),
      first,
      first.length ? "SELECTED" : "UNSURE",
    );
    while (state.answers.length < 4) {
      const next = nextStep(state);
      if (!next.question || next.recovery) break;
      state = answerCurrentQuestion(
        state,
        later === "unsure"
          ? []
          : later === "all"
            ? next.question.options.map((o) => o.id)
            : [next.question.options[0]!.id],
        later === "unsure" ? "UNSURE" : "SELECTED",
      );
    }
    return state;
  }
  const initial = createResearchState("A");
  const broadFruit = answer(initial, "direction_A", ["fruit"]);
  const allA = researchCatalog.questions
    .find((q) => q.id === "direction_A")!
    .options.map((o) => o.id);
  add(
    "clear_headline",
    "Concrete sweet/nut/cocoa direction followed by a separating question",
    ordinary("A", ["sweet_nut_cocoa"], "all"),
    true,
  );
  add(
    "clear_headline",
    "Multiple broad directions retain supported headline and expanded candidates",
    ordinary("A", ["fruit", "sweet_nut_cocoa"], "all"),
    true,
  );
  add(
    "variant_b",
    "Progressive fruit/flower branch follows the assigned broad first question",
    ordinary("B", ["fruit_flower"], "all"),
    true,
  );
  add(
    "partial_output",
    "Fruit/citrus aliases occupy one redundancy group",
    answer(broadFruit, "fruit_region", ["citrus"]),
  );
  add(
    "partial_output",
    "A single tea reference can produce fewer than three headlines",
    answer(
      answer(initial, "direction_A", [], "UNSURE"),
      "floral_tea_reference",
      ["tea"],
    ),
  );
  add(
    "exploration_only",
    "Review-only relations cannot independently produce headlines",
    answer(initial, "direction_A", ["fruit"]),
    false,
    researchCatalog.candidates.map((c) => ({
      ...c,
      reviewOnly: true,
      directSupport: 0,
      governedSupport: 0,
    })),
  );
  const uncertain = ordinary("A", [], "unsure");
  add(
    "low_information",
    "Four unsure answers preserve neutral scores and empty output",
    uncertain,
    true,
  );
  add(
    "extra_question",
    "An unused separating fifth question may be offered after four neutral answers",
    uncertain,
    true,
  );
  const fifth = answerCurrentQuestion(
    uncertain,
    [nextStep(uncertain).question!.options[0]!.id],
    "SELECTED",
    true,
  );
  add(
    "extra_question_accepted",
    "Explicit recovery acceptance permits exactly one additional question",
    fifth,
    true,
  );
  add(
    "open_set",
    "An explicit outside-vocabulary flag withholds claims and further recovery",
    { ...broadFruit, openSet: true },
  );
  add(
    "conflicting_answer",
    "The later closed-none answer disputes every currently supported fruit reference",
    answer(broadFruit, "fruit_region", [], "NONE_OF_THESE"),
  );
  add(
    "unsure",
    "Mandatory Q1 has a typed unsure response without sensory adjustment",
    answer(initial, "direction_A", [], "UNSURE"),
    true,
  );
  add(
    "unsure_after_support",
    "Unsure does not erase earlier positive support",
    answer(broadFruit, "fruit_region", [], "UNSURE"),
  );
  add(
    "none_of_these",
    "A closed fruit list weakly affects only displayed fruit concepts",
    answer(
      answer(initial, "direction_A", ["fruit", "floral_tea"]),
      "fruit_region",
      [],
      "NONE_OF_THESE",
    ),
  );
  add(
    "skip",
    "Skip is explicitly stored and leaves earlier scores unchanged",
    answer(broadFruit, "fruit_region", [], "SKIP"),
  );
  let skipped = answer(initial, "direction_A", [], "SKIP");
  while (skipped.answers.length < 4 && nextStep(skipped).question)
    skipped = answerCurrentQuestion(skipped, [], "SKIP");
  add(
    "skip_low_information",
    "Four skip responses remain distinguishable from unsure",
    skipped,
    true,
  );
  add(
    "c0_weak_prior_override",
    "Explicit sweet support survives a weak negative C0 adjustment",
    {
      ...answer(initial, "direction_A", ["sweet_nut_cocoa"]),
      c0: c0[0]!.id,
      c1: "medium",
    },
    true,
  );
  add("c0_missing", "Missing C0 remains a neutral policy fixture", broadFruit);
  add("c1_neutral", "A very light roast adds no roast evidence", {
    ...broadFruit,
    c1: "extremely_light",
  });
  add(
    "c1_neutral",
    "A very dark roast cannot be reverse-inferred from flavor",
    { ...broadFruit, c1: "extremely_dark" },
  );
  add("c1_unsure", "Roast unsure is null and never an eighth level", {
    ...broadFruit,
    c0: c0[0]!.id,
    c1: null,
  });
  add(
    "redundancy",
    "Selecting both fruit examples does not duplicate aliases or citrus concepts",
    answer(broadFruit, "fruit_region", ["citrus", "berry"]),
  );
  add(
    "rights_blocked",
    "Only rights-blocked orange-blossom support must abstain",
    answer(
      answer(initial, "direction_A", [], "UNSURE"),
      "floral_tea_reference",
      ["citrus_blossom"],
    ),
  );
  add(
    "rights_mixed",
    "Blocked concepts remain hidden when eligible concepts also have support",
    answer(initial, "direction_A", allA),
    true,
  );
  add(
    "all_options_selected",
    "Selecting every displayed option is recorded and is not a conflict",
    ordinary("A", allA, "all"),
    true,
  );
  add("q1_mandatory", "No sensory response must not yield output", initial);
  add(
    "redundant_semantic_rejected",
    "Fruit_region and acidity_character share a semantic distinction",
    answer(broadFruit, "fruit_region", ["berry"]),
    false,
    researchCatalog.candidates,
    "REPEATED_SEMANTIC_QUESTION_MUST_THROW",
  );
  add(
    "q5_without_opt_in_rejected",
    "Fifth-question acceptance is required, even when separation exists",
    uncertain,
    false,
    researchCatalog.candidates,
    "RECOVERY_WITHOUT_ACCEPTANCE_MUST_THROW",
  );
  return cases;
}

export function benchmarkResult(item: BenchmarkCase) {
  const r = evaluate(item.state, item.candidates);
  const next = nextStep(item.state);
  return {
    resultState: r.resultState,
    headline: r.headline.map((c) => c.id),
    expandedMain: r.expandedMain.map((c) => c.id),
    exploration: r.exploration.map((c) => c.id),
    extraQuestionAppropriate: next.recovery,
    nextQuestion: next.question?.id ?? "",
    questionCount: item.state.answers.length,
    explanations: [...r.headline, ...r.expandedMain, ...r.exploration].map(
      (c) => ({ conceptId: c.id, text: c.explanation, lineage: c.lineage }),
    ),
  };
}

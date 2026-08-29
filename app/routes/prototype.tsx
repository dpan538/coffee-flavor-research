import { useMemo, useState } from "react";
import {
  descriptors,
  questionPlan,
  rankCandidateSet,
  type PreparationContext,
  type RoastLevel,
  type SensoryAnswer,
} from "flavor-data";
import {
  COLLECTION_MODE,
  exportSyntheticPreview,
  previewSyntheticEvent,
  saveSyntheticPreview,
  withdrawAndDeleteLocalPreviews,
} from "@/lib/research-events";

const preparations: Array<{ value: PreparationContext; label: string }> = [
  { value: "filter", label: "Filter / 手冲" },
  { value: "espresso", label: "Espresso / 意式浓缩" },
  { value: "immersion", label: "Immersion / 浸泡" },
  { value: "cupping", label: "Cupping / 杯测" },
];

const questions = [
  {
    id: "Q1" as const,
    prompt: "Which bright or aromatic reference feels closest?",
    ids: ["jasmine", "lemon", "orange", "green-tea"],
  },
  {
    id: "Q2" as const,
    prompt: "Which fruit direction is most useful?",
    ids: ["blueberry", "red-berries", "dried-fruit", "winey"],
  },
  {
    id: "Q3" as const,
    prompt: "Which sweet or deep reference fits?",
    ids: ["honey", "caramel", "brown-sugar", "dark-chocolate"],
  },
  {
    id: "Q4" as const,
    prompt: "Which structure or finish is closest?",
    ids: ["almond", "cinnamon", "cedar", "earthy"],
  },
  {
    id: "Q5" as const,
    prompt: "One exceptional tie-breaker: which boundary direction helps?",
    ids: ["rose", "smoky", "fermented", "bellflower"],
  },
];

export function meta() {
  return [
    { title: "5+3 prototype — Coffee Flavor Atlas" },
    {
      name: "description",
      content:
        "A deterministic, evidence-aware 5+3 coffee descriptor candidate prototype.",
    },
  ];
}

export default function PrototypeRoute() {
  const [C0, setC0] = useState<PreparationContext | "">("");
  const [C1, setC1] = useState<RoastLevel | 0>(0);
  const [answers, setAnswers] = useState<SensoryAnswer[]>([]);
  const [consentPreview, setConsentPreview] = useState(false);
  const [exportPreview, setExportPreview] = useState("");
  const input = C0 && C1 ? { C0, C1, answers } : null;
  const plan: Array<SensoryAnswer["questionId"]> = input
    ? questionPlan(input)
    : ["Q1", "Q2", "Q3", "Q4"];
  const visibleQuestions = questions.filter((question) =>
    plan.includes(question.id),
  );
  const complete = Boolean(
    input &&
    visibleQuestions.every((question) =>
      answers.some((answer) => answer.questionId === question.id),
    ),
  );
  const receipt = useMemo(
    () => (complete && input ? rankCandidateSet(input) : null),
    [complete, input],
  );

  function choose(
    questionId: SensoryAnswer["questionId"],
    descriptorId: string,
  ) {
    setAnswers((current) => [
      ...current.filter((answer) => answer.questionId !== questionId),
      {
        questionId,
        descriptorIds: [descriptorId],
        answerVersion: "round4a-q-v1",
      },
    ]);
  }

  function savePreview() {
    if (!consentPreview || !C0 || !C1) return;
    saveSyntheticPreview(
      previewSyntheticEvent({
        C0,
        C1,
        question_id: "RESULT",
        question_order: 5,
        answer:
          receipt?.selected
            .map((candidate) => candidate.descriptorId)
            .join("|") ?? null,
        completion_state: receipt ? "COMPLETED" : "STARTED",
      }),
    );
    setExportPreview(exportSyntheticPreview());
  }

  return (
    <div className="page prototype-page">
      <header className="prototype-hero">
        <p className="meta-label">ROUND 4A / DETERMINISTIC 5+3</p>
        <h1>Evidence-connected candidates</h1>
        <p>
          A structured candidate set, not eight independent predictions. Context
          is a soft prior; your answers can override it.
        </p>
        <p className="prototype-notice">
          No calibrated probabilities. No model training. No remote collection.
          Current mode: <strong>{COLLECTION_MODE}</strong>.
        </p>
      </header>

      <form
        className="prototype-flow"
        onSubmit={(event) => event.preventDefault()}
      >
        <fieldset>
          <legend>C0 — preparation (required)</legend>
          <div className="choice-grid">
            {preparations.map((item) => (
              <label
                key={item.value}
                className={
                  C0 === item.value ? "choice choice--active" : "choice"
                }
              >
                <input
                  type="radio"
                  name="C0"
                  value={item.value}
                  checked={C0 === item.value}
                  onChange={() => setC0(item.value)}
                />
                {item.label}
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend>C1 — roast appearance, seven levels (required)</legend>
          <div className="roast-scale">
            {[1, 2, 3, 4, 5, 6, 7].map((level) => (
              <label
                key={level}
                className={C1 === level ? "choice choice--active" : "choice"}
              >
                <input
                  type="radio"
                  name="C1"
                  value={level}
                  checked={C1 === level}
                  onChange={() => setC1(level as RoastLevel)}
                />
                {level}
              </label>
            ))}
          </div>
          <p className="field-help">
            1 lighter-looking · 4 middle · 7 darker-looking. This does not infer
            roast from tasting words.
          </p>
        </fieldset>

        {C0 && C1 ? (
          visibleQuestions.map((question, index) => (
            <fieldset key={question.id}>
              <legend>
                {question.id} — {question.prompt}
              </legend>
              {question.id === "Q5" ? (
                <p className="field-help">
                  Q5 appears only because the first four answers leave
                  insufficient stronger evidence.
                </p>
              ) : null}
              <div className="choice-grid">
                {question.ids.map((id) => {
                  const descriptor = descriptors.find(
                    (candidate) => candidate.id === id,
                  )!;
                  const checked = answers.some(
                    (answer) =>
                      answer.questionId === question.id &&
                      answer.descriptorIds.includes(id),
                  );
                  return (
                    <label
                      key={id}
                      className={checked ? "choice choice--active" : "choice"}
                    >
                      <input
                        type="radio"
                        name={question.id}
                        checked={checked}
                        onChange={() => choose(question.id, id)}
                      />
                      <span>{descriptor.labels.en}</span>
                      <small>{descriptor.labels.zhHans}</small>
                    </label>
                  );
                })}
              </div>
              <p className="meta-label">
                QUESTION {index + 1} OF {visibleQuestions.length}
              </p>
            </fieldset>
          ))
        ) : (
          <p className="prototype-gate">
            Choose both C0 and C1 to begin Q1–Q4.
          </p>
        )}
      </form>

      {receipt ? (
        <section className="candidate-results" aria-live="polite">
          <div>
            <p className="meta-label">PRIMARY / HIGH-CONFIDENCE CORE</p>
            <h2>Five primary candidates</h2>
          </div>
          <ol className="candidate-list">
            {receipt.selected
              .filter((candidate) => candidate.role === "PRIMARY")
              .map((candidate) => (
                <li key={candidate.descriptorId}>
                  <strong>
                    {candidate.rank}.{" "}
                    {
                      descriptors.find(
                        (item) => item.id === candidate.descriptorId,
                      )?.labels.en
                    }
                  </strong>
                  <span>{candidate.evidenceLabel}</span>
                  <small>{candidate.uncertaintyReason}</small>
                </li>
              ))}
          </ol>
          <div>
            <p className="meta-label">SECONDARY / ADJACENT REFERENCE</p>
            <h2>Three secondary candidates</h2>
          </div>
          <ol className="candidate-list candidate-list--secondary" start={6}>
            {receipt.selected
              .filter((candidate) => candidate.role === "SECONDARY")
              .map((candidate) => (
                <li key={candidate.descriptorId}>
                  <strong>
                    {candidate.rank}.{" "}
                    {
                      descriptors.find(
                        (item) => item.id === candidate.descriptorId,
                      )?.labels.en
                    }
                  </strong>
                  <span>{candidate.evidenceLabel}</span>
                  <small>{candidate.uncertaintyReason}</small>
                </li>
              ))}
          </ol>
          <dl className="receipt-summary">
            <div>
              <dt>Objective</dt>
              <dd>{receipt.objective}</dd>
            </div>
            <div>
              <dt>Connected components</dt>
              <dd>{receipt.connectedComponents}</dd>
            </div>
            <div>
              <dt>Unsupported isolated candidates</dt>
              <dd>{receipt.isolatedCandidateCount}</dd>
            </div>
            <div>
              <dt>Override receipts</dt>
              <dd>{receipt.overrideReceipts.length}</dd>
            </div>
          </dl>
          <details>
            <summary>View deterministic scoring receipt</summary>
            <pre>{JSON.stringify(receipt, null, 2)}</pre>
          </details>
        </section>
      ) : null}

      <section className="consent-panel" aria-labelledby="consent-title">
        <p className="meta-label">LOCAL SYNTHETIC EVENT PREVIEW</p>
        <h2 id="consent-title">Consent and privacy sandbox</h2>
        <p>
          This preview never sends data to a server and is not a research
          consent process. It demonstrates the future event contract with
          synthetic local-only rows.
        </p>
        <label className="consent-check">
          <input
            type="checkbox"
            checked={consentPreview}
            onChange={(event) => setConsentPreview(event.target.checked)}
          />
          I understand this creates only a synthetic preview in this browser.
        </label>
        <div className="prototype-actions">
          <button
            type="button"
            disabled={!consentPreview}
            onClick={savePreview}
          >
            Create export preview
          </button>
          <button
            type="button"
            onClick={() => {
              withdrawAndDeleteLocalPreviews();
              setExportPreview("");
            }}
          >
            Withdraw and delete local preview
          </button>
        </div>
        {exportPreview ? (
          <pre aria-label="Synthetic data export preview">{exportPreview}</pre>
        ) : null}
      </section>
    </div>
  );
}

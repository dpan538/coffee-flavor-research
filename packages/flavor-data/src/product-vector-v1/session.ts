/**
 * Session API for the front end (owner Step 5, 2026-09-12): the whole chain behind one immutable state.
 *
 *   createSession(context, locale)
 *     → nextStep(session)        "ask" a slot (prompt + options from the question bank), or "describe"
 *     → answer(session, slot, option)
 *     → firstDescription(session) 3 + 5 words + the pick prompt
 *     → submitPicks(session, words) escalation gate → { stage: "final", card } or { stage: "q6", options }
 *     → answerQ6(session, dimensions) → second description + card
 *
 * Every function returns a new session object; nothing is mutated, nothing touches storage. A UI
 * persists the session however it likes (IndexedDB for the local library is a separate module).
 */
import bundle from "../../../../db/data/product-vector-v1/product-vector-v1.json" with { type: "json" };
import { infer, type BeanVector, type ContextAnswers, type InferenceResult, type Locale } from "./engine";
import {
  applyQ6,
  describe,
  escalationGate,
  finalCard,
  flowStep,
  perceptionAnswers,
  q6Options,
  type Description,
  type FinalCard,
  type FlowAnswers,
  type FlowStep,
  type GateDecision,
  type Q6Option,
  type Slot,
  type Word,
} from "./flow";
import { mapUtterance } from "./lexicon";

export type Stage = "context" | "questions" | "describe" | "picks" | "q6" | "final";

export type QuestionCard = {
  slot: Slot;
  prompt: string;
  options: Array<{ option: string; label: string }>;
  progress: { answered: number; expected: number };
};

export type Session = {
  version: string;
  locale: Locale;
  context: ContextAnswers;
  answers: FlowAnswers;
  beans: BeanVector[];
  stage: Stage;
  step: FlowStep;
  result: InferenceResult | null;
  description: Description | null;
  picks: Word[];
  gate: GateDecision | null;
  q6: { options: Q6Option[]; selected: string[] } | null;
  card: FinalCard | null;
  history: Array<{ at: number; event: string; detail?: unknown }>;
};

const bank = bundle.question_bank as Record<string, { question: string; prompt: Record<Locale, string>; options: Record<string, { label: Record<Locale, string> }> }>;

function log(session: Session, event: string, detail?: unknown): Session {
  return { ...session, history: [...session.history, { at: session.history.length, event, detail }] };
}

export function createSession(context: ContextAnswers, locale: Locale, beans: BeanVector[] = []): Session {
  const base: Session = {
    version: bundle.version,
    locale,
    context,
    answers: {},
    beans,
    stage: "questions",
    step: flowStep({}, context),
    result: null,
    description: null,
    picks: [],
    gate: null,
    q6: null,
    card: null,
    history: [],
  };
  return log(base, "created", { context, locale });
}

/** What the UI should render now. */
export function nextStep(session: Session): { kind: "ask"; card: QuestionCard } | { kind: "describe" } | { kind: "picks" } | { kind: "q6" } | { kind: "final" } {
  if (session.stage === "questions") {
    const slot = session.step.ask[0];
    if (!slot || session.step.deliver) return { kind: "describe" };
    const q = bank[slot]!;
    const answered = Object.keys(session.answers).length;
    const expected = session.step.path === null ? (answered < 4 ? 5 : 6) : session.step.path === 1 || session.step.path === 4 ? 5 : 6;
    return {
      kind: "ask",
      card: {
        slot,
        prompt: q.prompt[session.locale],
        options: Object.entries(q.options).map(([option, spec]) => ({ option, label: spec.label[session.locale] })),
        progress: { answered, expected },
      },
    };
  }
  if (session.stage === "describe") return { kind: "describe" };
  if (session.stage === "picks") return { kind: "picks" };
  if (session.stage === "q6") return { kind: "q6" };
  return { kind: "final" };
}

export function answer(session: Session, slot: Slot, option: string): Session {
  if (session.stage !== "questions") return session;
  if (!bank[slot]?.options[option]) throw new Error(`unknown option ${slot}:${option}`);
  const answers = { ...session.answers, [slot]: option };
  const step = flowStep(answers, session.context);
  const next: Session = { ...session, answers, step, stage: step.deliver ? "describe" : "questions" };
  return log(next, "answer", { slot, option, path: step.path, deliver: step.deliver });
}

/** Optional: seed answers from a free-text utterance (the hybrid mapper); only unanswered slots are filled. */
export function answerFromUtterance(session: Session, text: string): Session {
  const mapped = mapUtterance(text, session.locale);
  let current = session;
  for (const [slot, option] of Object.entries(mapped.answers)) {
    if (current.stage !== "questions") break;
    if (current.answers[slot as Slot] || !current.step.ask.includes(slot as Slot)) continue;
    current = answer(current, slot as Slot, option!);
  }
  return log(current, "utterance", { text, mapped: mapped.answers, forced: mapped.forced });
}

/** Run the inference and build the first 3 + 5 description; moves the session to the picks stage. */
export function firstDescription(session: Session): Session {
  if (session.stage !== "describe") return session;
  const result = infer(session.context, perceptionAnswers(session.answers), { beans: session.beans });
  const description = describe(result, session.locale);
  return log({ ...session, result, description, stage: "picks" }, "first_description", { path: session.step.path, main: description.main.map((w) => w.text) });
}

/** The user's picks (implicit feedback). Branch A → final card; branch B → Q6 options. */
export function submitPicks(session: Session, picks: Word[]): Session {
  if (session.stage !== "picks" || !session.result || !session.description) return session;
  const allowed = new Set(session.description.all.map((w) => w.text));
  const chosen = picks.filter((w) => allowed.has(w.text)).slice(0, bundle.question_flow.first_description.pick_count);
  const gate = escalationGate(session.step, session.result, chosen);
  if (gate.escalate) {
    const options = q6Options(session.result, session.locale);
    return log({ ...session, picks: chosen, gate, q6: { options, selected: [] }, stage: "q6" }, "picks_escalate", { reason: gate.reason });
  }
  const card = finalCard(session.result, chosen, session.locale);
  return log({ ...session, picks: chosen, gate, card, stage: "final" }, "picks_final", { reason: gate.reason });
}

/** Q6: the strong correction; returns the session with the second description and the final card. */
export function answerQ6(session: Session, selectedDimensions: string[]): Session {
  if (session.stage !== "q6" || !session.result || !session.q6) return session;
  const corrected = applyQ6(session.result, selectedDimensions);
  const description = describe(corrected, session.locale);
  const picks = description.all.slice(0, bundle.question_flow.first_description.pick_count);
  const card = finalCard(corrected, picks, session.locale);
  return log({ ...session, result: corrected, description, picks, card, q6: { ...session.q6, selected: selectedDimensions }, stage: "final" }, "q6", { selectedDimensions });
}

/** The same session in another language: the description, the picks (matched by position) and the card are re-derived. */
export function relocalize(session: Session, locale: Locale): Session {
  if (session.locale === locale) return session;
  let next: Session = { ...session, locale };
  if (session.result && session.description) {
    const description = describe(session.result, locale);
    const index = new Map(session.description.all.map((w, i) => [w.text, i]));
    const picks = session.picks.map((w) => description.all[index.get(w.text) ?? -1] ?? w);
    next = { ...next, description, picks };
    if (session.card) next = { ...next, card: finalCard(session.result, picks, locale) };
    if (session.q6) next = { ...next, q6: { ...session.q6, options: q6Options(session.result, locale) } };
  }
  return next;
}

export const sessionVersion = bundle.version;

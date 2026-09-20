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
import {
  add,
  buildVPred,
  cosine,
  infer,
  normalize,
  zero,
  type BeanVector,
  type ContextAnswers,
  type InferenceResult,
  type Locale,
} from "./engine";
import {
  applyQ6,
  describe,
  dynamicUserVector,
  escalationGate,
  finalCard,
  flowStep,
  perceptionAnswers,
  q6Options,
  localizeWord,
  q6Word,
  slotVector,
  type Description,
  type FinalCard,
  type FlowAnswers,
  type FlowStep,
  type GateDecision,
  type Q6Option,
  type Slot,
  type Word,
  SLOTS,
} from "./flow";
import { questionForKey, wordHints } from "./dynamicBank";
import { mapUtterance } from "./lexicon";

export type Stage =
  | "context"
  | "questions"
  | "describe"
  | "picks"
  | "q6"
  | "final";

export type QuestionCard = {
  /** the question's key: a slot, or in the dynamic bank also "E1", "E2", "S:<first-level option>" */
  slot: string;
  prompt: string;
  /** the prompt was chosen by the previous answer (a variant), not the bank's default */
  adapted: boolean;
  /** re-ranked by fit to the cup and the answers so far; absence options last */
  options: Array<{ option: string; label: string; fit: number }>;
  /** dynamic bank: the line under the options for a reader who cannot answer; not one of the five */
  unanswered?: { option: string; label: string };
  progress: { answered: number; expected: number };
};

/** "fixed": the six Matrix_Q questions; "dynamic": the dynamic question bank (R3-D40) — four core questions and two
 *  follow-ups at most, options pruned for this kind of coffee. The app runs "dynamic"; "fixed" stays as the reference
 *  implementation of the coherence tree, with its exhaustive tests. */
export type SessionMode = "fixed" | "dynamic";

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
  /** varies the card's supporting statistics between visits; 0 (the default) keeps a session fully deterministic */
  nonce: number;
  mode: SessionMode;
};

const bank = bundle.question_bank as Record<
  string,
  {
    question: string;
    prompt: Record<Locale, string>;
    options: Record<string, { label: Record<Locale, string> }>;
  }
>;
type Variant = { by: string } & Record<string, Record<Locale, string> | string>;
const variants = ((
  bundle.question_flow as { prompt_variants?: Record<string, Variant> }
).prompt_variants ?? {}) as Record<string, Variant>;

/** the prompt for a slot given the answers so far: the variant keyed by the previous answer, else the bank's default */
export function promptFor(
  slot: Slot,
  answers: FlowAnswers,
  locale: Locale,
): { prompt: string; adapted: boolean } {
  const v = variants[slot];
  const prev = v ? answers[v.by as Slot] : undefined;
  const pick =
    v && prev ? (v[prev] as Record<Locale, string> | undefined) : undefined;
  return pick
    ? { prompt: pick[locale], adapted: true }
    : { prompt: bank[slot]!.prompt[locale], adapted: false };
}

/** the options of a slot re-ranked by fit to the cup and the answers so far (absence options last) */
export function rankedOptions(
  slot: Slot,
  context: ContextAnswers,
  answers: FlowAnswers,
  locale: Locale,
): Array<{ option: string; label: string; fit: number }> {
  let v = buildVPred(context).vPred;
  for (const [s, a] of Object.entries(answers))
    if (a) v = add(v, slotVector(s as Slot, a));
  const target = v.some((x) => x !== 0) ? normalize(v) : zero();
  return Object.entries(bank[slot]!.options)
    .map(([option, spec]) => {
      const inc = slotVector(slot, option);
      const absent = !inc.some((x) => x !== 0);
      return {
        option,
        label: spec.label[locale],
        fit: absent ? -1 : cosine(normalize(inc), target),
      };
    })
    .sort((a, b) => b.fit - a.fit);
}

function log(session: Session, event: string, detail?: unknown): Session {
  return {
    ...session,
    history: [
      ...session.history,
      { at: session.history.length, event, detail },
    ],
  };
}

const flowOptions = (session: { mode: SessionMode; nonce: number }) =>
  session.mode === "dynamic" ? { dynamic: true, nonce: session.nonce } : {};

export function createSession(
  context: ContextAnswers,
  locale: Locale,
  beans: BeanVector[] = [],
  nonce = 0,
  mode: SessionMode = "fixed",
): Session {
  const base: Session = {
    version: bundle.version,
    locale,
    context,
    answers: {},
    beans,
    stage: "questions",
    step: flowStep({}, context, flowOptions({ mode, nonce })),
    result: null,
    description: null,
    picks: [],
    gate: null,
    q6: null,
    card: null,
    history: [],
    nonce,
    mode,
  };
  return log(base, "created", { context, locale, mode });
}

/** What the UI should render now. */
export function nextStep(
  session: Session,
):
  | { kind: "ask"; card: QuestionCard }
  | { kind: "describe" }
  | { kind: "picks" }
  | { kind: "q6" }
  | { kind: "final" } {
  if (session.stage === "questions") {
    const slot = session.step.ask[0];
    if (!slot || session.step.deliver) return { kind: "describe" };
    const answered = Object.keys(session.answers).length;
    if (session.mode === "dynamic") {
      const question = questionForKey(
        slot,
        session.context,
        session.answers,
        session.locale,
        session.nonce,
        session.step.strong === true,
      );
      if (!question) return { kind: "describe" };
      return {
        kind: "ask",
        card: {
          slot,
          prompt: question.prompt,
          adapted: question.prompt !== "",
          // pruned by the corpus, never sorted: the pool's fixed order
          options: question.options.map((o) => ({
            option: o.id,
            label: o.label,
            fit: 0,
          })),
          ...(question.unanswered
            ? {
                unanswered: {
                  option: question.unanswered.id,
                  label: question.unanswered.label,
                },
              }
            : {}),
          // four core questions, then two follow-ups at most; the count is known once the core answers are in
          progress: { answered, expected: session.step.planned ?? 6 },
        },
      };
    }
    const expected =
      session.step.path === null
        ? answered < 4
          ? 5
          : 6
        : session.step.path === 1 || session.step.path === 4
          ? 5
          : 6;
    const { prompt, adapted } = promptFor(
      slot as Slot,
      session.answers,
      session.locale,
    );
    return {
      kind: "ask",
      card: {
        slot,
        prompt,
        adapted,
        options: rankedOptions(
          slot as Slot,
          session.context,
          session.answers,
          session.locale,
        ),
        progress: { answered, expected },
      },
    };
  }
  if (session.stage === "describe") return { kind: "describe" };
  if (session.stage === "picks") return { kind: "picks" };
  if (session.stage === "q6") return { kind: "q6" };
  return { kind: "final" };
}

export function answer(
  session: Session,
  slot: string,
  option: string,
): Session {
  if (session.stage !== "questions") return session;
  if (!option) throw new Error(`no option given for ${slot}`);
  if (session.mode === "dynamic") {
    const question = questionForKey(
      slot,
      session.context,
      session.answers,
      session.locale,
      session.nonce,
      session.step.strong === true,
    );
    const known =
      question?.options.some((o) => o.id === option) ||
      question?.unanswered?.id === option;
    if (!known) throw new Error(`unknown option ${slot}:${option}`);
  } else if (!bank[slot]?.options[option])
    throw new Error(`unknown option ${slot}:${option}`);
  const answers = { ...session.answers, [slot]: option };
  const step = flowStep(answers, session.context, flowOptions(session));
  const next: Session = {
    ...session,
    answers,
    step,
    stage: step.deliver ? "describe" : "questions",
  };
  return log(next, "answer", {
    slot,
    option,
    path: step.path,
    deliver: step.deliver,
  });
}

/** Optional: seed answers from a free-text utterance (the hybrid mapper); only unanswered slots are filled. */
/**
 * Editing an earlier answer without losing the others (owner, 2026-09-18). A session's state is a function of the
 * context and the answers, and every question's option ids are fixed — only the prompt's lead-in, the order of the
 * options and the path follow the earlier answers — so an answer given later still means the same thing after an
 * earlier one changes. `reopenQuestion` rebuilds the session up to the question being edited and keeps every answer
 * from that question onward; `answerAndReplay` answers it and then replays the kept answers through the engine for as
 * long as the flow asks for them. The result is, by construction and by test (tests/product-vector-v1-edit-replay),
 * identical to a fresh session given the same final answers: path, prompts, option order, progress and vectors are
 * all recomputed. The flow stops where the new path asks something never answered; answers it no longer needs are dropped.
 */
export type KeptAnswers = Partial<Record<string, string>>;
export type ReplayedAnswer = {
  slot: string;
  prompt: string;
  option: string;
  label: string;
};
export type EditResult = {
  session: Session;
  kept: KeptAnswers;
  replayed: ReplayedAnswer[];
};

function replayAnswers(
  from: Session,
  answers: KeptAnswers,
  stopAt?: string,
): EditResult {
  const kept = { ...answers };
  const replayed: ReplayedAnswer[] = [];
  let session = from;
  let guard = 0;
  while (session.stage === "questions" && guard < SLOTS.length + 2) {
    const step = nextStep(session);
    if (step.kind !== "ask") break;
    const slot = step.card.slot;
    if (slot === stopAt) break;
    const option = kept[slot];
    const label = [
      ...step.card.options,
      ...(step.card.unanswered ? [step.card.unanswered] : []),
    ].find((o) => o.option === option)?.label;
    if (!option || label === undefined) break;
    replayed.push({ slot, prompt: step.card.prompt, option, label });
    session = answer(session, slot, option);
    delete kept[slot];
    guard += 1;
  }
  // Once the four core answers are in, the follow-ups of this path are decided: an answer kept from the earlier path
  // for a question this path never asks is dropped now, not when the flow ends — the progress row showed it as a
  // seventh and eighth question (found by the owner, 2026-09-20).
  const planned = session.stage === "questions" && session.step.plannedKeys;
  if (planned)
    for (const slot of Object.keys(kept))
      if (!planned.includes(slot)) delete kept[slot];
  return { session, kept, replayed };
}

/** Open an answered (or kept) question for editing: the answers before it are re-applied, the rest are kept. */
export function reopenQuestion(
  session: Session,
  target: string,
  kept: KeptAnswers = {},
): EditResult {
  const known: KeptAnswers = { ...session.answers, ...kept };
  if (!known[target]) return { session, kept, replayed: [] };
  const rebuilt = replayAnswers(
    createSession(
      session.context,
      session.locale,
      session.beans,
      session.nonce,
      session.mode,
    ),
    known,
    target,
  );
  // the questions from the edited one onward, in the order they were asked (the six slots are asked in slot order; a
  // dynamic session's follow-ups come after the core ones, and the answers keep their insertion order)
  const order =
    session.mode === "dynamic" ? Object.keys(known) : (SLOTS as string[]);
  const at = order.indexOf(target);
  const held: KeptAnswers = {};
  for (const slot of order)
    if (order.indexOf(slot) >= at && known[slot]) held[slot] = known[slot];
  return { session: rebuilt.session, kept: held, replayed: rebuilt.replayed };
}

/** Leave editing without changing anything: replay every kept answer and return to the question that was open before. */
export function resumeKept(session: Session, kept: KeptAnswers): EditResult {
  const result = replayAnswers(session, kept);
  return {
    ...result,
    kept: result.session.stage === "questions" ? result.kept : {},
  };
}

/** Answer `slot`, then replay the kept answers while the flow asks for them; leftovers the flow no longer needs are dropped. */
export function answerAndReplay(
  session: Session,
  slot: string,
  option: string,
  kept: KeptAnswers = {},
): EditResult {
  const rest = { ...kept };
  delete rest[slot];
  const result = replayAnswers(answer(session, slot, option), rest);
  return {
    ...result,
    kept: result.session.stage === "questions" ? result.kept : {},
  };
}

export function answerFromUtterance(session: Session, text: string): Session {
  if (session.mode === "dynamic") return session; // the hybrid mapper speaks Matrix_Q letters only
  const mapped = mapUtterance(text, session.locale);
  let current = session;
  for (const [slot, option] of Object.entries(mapped.answers)) {
    if (current.stage !== "questions") break;
    if (
      current.answers[slot as Slot] ||
      !current.step.ask.includes(slot as Slot)
    )
      continue;
    current = answer(current, slot as Slot, option!);
  }
  return log(current, "utterance", {
    text,
    mapped: mapped.answers,
    forced: mapped.forced,
  });
}

/** Run the inference and build the first 3 + 5 description; moves the session to the picks stage. */
export function firstDescription(session: Session): Session {
  if (session.stage !== "describe") return session;
  const vUser = dynamicUserVector(session.answers);
  const result = infer(session.context, perceptionAnswers(session.answers), {
    beans: session.beans,
    ...(vUser ? { vUser } : {}),
  });
  // what the reader pointed to leads the words: the sub-family of a first-level answer, the very word of a second-level one
  const description = describe(
    result,
    session.locale,
    wordHints(session.answers, session.context),
    { neighbours: session.mode === "dynamic" },
  );
  return log(
    { ...session, result, description, stage: "picks" },
    "first_description",
    { path: session.step.path, main: description.main.map((w) => w.text) },
  );
}

/** The user's picks (implicit feedback). Branch A → final card; branch B → Q6 options. */
export function submitPicks(session: Session, picks: Word[]): Session {
  if (session.stage !== "picks" || !session.result || !session.description)
    return session;
  const allowed = new Set(session.description.all.map((w) => w.text));
  const chosen = picks
    .filter((w) => allowed.has(w.text))
    .slice(0, bundle.question_flow.first_description.pick_count);
  const gate = escalationGate(session.step, session.result, chosen);
  if (gate.escalate) {
    const options = q6Options(session.result, session.locale);
    return log(
      {
        ...session,
        picks: chosen,
        gate,
        q6: { options, selected: [] },
        stage: "q6",
      },
      "picks_escalate",
      { reason: gate.reason },
    );
  }
  const card = finalCard(session.result, chosen, session.locale, {
    nonce: session.nonce,
    answers: session.answers,
  });
  return log(
    { ...session, picks: chosen, gate, card, stage: "final" },
    "picks_final",
    { reason: gate.reason },
  );
}

/** Q6: the strong correction; returns the session with the second description and the final card. */
export function answerQ6(
  session: Session,
  selectedDimensions: string[],
): Session {
  if (session.stage !== "q6" || !session.result || !session.q6) return session;
  const corrected = applyQ6(session.result, selectedDimensions);
  const description = describe(
    corrected,
    session.locale,
    hintsOf(session, selectedDimensions),
    { neighbours: session.mode === "dynamic" },
  );
  // The card keeps the words the reader picked (owner, 2026-09-20: the card follows the reader's signals — the
  // confirmation step used to replace them with the first five words of the second description) and adds the leading
  // word of every candidate dimension just confirmed; five at most, the confirmed words first in line to stay. An
  // evaluation dimension confirmed here gets its row instead (finalCard). Nothing the reader did not choose is added.
  const count = bundle.question_flow.first_description.pick_count;
  // (owner, 2026-09-20: asking the reader to confirm flavors and then not showing them is counter-intuitive — of the
  // flavors ticked, at least two must be in the final description. Every ticked word is, as the very word its option
  // showed — a spice or a roast word too: the reader chose it themselves, and the on-screen card has no evaluation
  // rows to carry it. Only beyond five words does an evaluation word fall back to its row on the exported card.)
  const confirmedWords: Word[] = selectedDimensions
    .map((d) => ({ text: q6Word(d, session.locale), dimension: d }))
    .filter((w) => w.text);
  const seen = new Set<string>();
  const picks = [...confirmedWords, ...session.picks]
    .filter((w) => !seen.has(w.text) && Boolean(seen.add(w.text)))
    .slice(0, count);
  const card = finalCard(corrected, picks, session.locale, {
    nonce: session.nonce,
    secondLook: selectedDimensions,
    answers: session.answers,
  });
  return log(
    {
      ...session,
      result: corrected,
      description,
      picks,
      card,
      q6: { ...session.q6, selected: selectedDimensions },
      stage: "final",
    },
    "q6",
    { selectedDimensions },
  );
}

/**
 * What leads the words of a description: the reader's answers, and — after the confirmation step — the words ticked
 * there. A candidate dimension chosen in that step is led by the very word its option showed, unless the reader had
 * already named a word of that dimension at the second level (their own word stays first).
 */
function hintsOf(
  session: Session,
  selected: string[] = session.q6?.selected ?? [],
) {
  const hints: Record<
    string,
    { family?: string; lead?: string; passed?: string[]; from?: string }
  > = wordHints(session.answers, session.context);
  for (const dimension of selected) {
    const word = q6Word(dimension, "zh-CN"); // leads are matched by the Chinese list, position by position
    if (!word || hints[dimension]?.lead) continue;
    const { from: _from, ...rest } = hints[dimension] ?? {};
    hints[dimension] = { ...rest, lead: word };
  }
  return hints;
}

/** The same session in another language: the description, the picks (matched by position) and the card are re-derived. */
export function relocalize(session: Session, locale: Locale): Session {
  if (session.locale === locale) return session;
  let next: Session = { ...session, locale };
  if (session.result && session.description) {
    const description = describe(session.result, locale, hintsOf(session), {
      neighbours: session.mode === "dynamic",
    });
    const index = new Map(session.description.all.map((w, i) => [w.text, i]));
    // by position in the description; a word kept from before the confirmation step is not in the second description
    // and is translated through its dimension's list
    const picks = session.picks.map(
      (w) =>
        description.all[index.get(w.text) ?? -1] ?? localizeWord(w, locale),
    );
    next = { ...next, description, picks };
    if (session.card)
      next = {
        ...next,
        card: finalCard(session.result, picks, locale, {
          nonce: session.nonce,
          secondLook: session.q6?.selected ?? [],
          answers: session.answers,
        }),
      };
    if (session.q6)
      next = {
        ...next,
        q6: { ...session.q6, options: q6Options(session.result, locale) },
      };
  }
  return next;
}

export const sessionVersion = bundle.version;

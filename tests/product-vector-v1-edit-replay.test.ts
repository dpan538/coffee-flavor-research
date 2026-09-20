/**
 * Going back to change an answer (owner, 2026-09-18). From any question the reader can reopen an earlier one; the other
 * answers are kept and replayed through the engine. The owner's requirement is that the dynamic computation stays
 * exactly what the engine would compute — path, prompts, option order, progress, vectors, words — for every way of
 * going back: changing the fourth, third, second or first answer from the fifth question, changing more than one,
 * jumping between kept questions, or leaving without changing anything.
 *
 * The invariant, checked by enumeration: whatever the sequence of edits, the session must be identical to a fresh
 * session that is simply given the final answers in the order the flow asks for them. Identical means the whole
 * session state (answers, step with its path and coherence checks, stage), the next question card (prompt, ranked
 * options, progress) and, once the flow delivers, the inference result and the description.
 *
 * Default run: in the first context every state from the second to the fifth question (the fifth is the owner's case:
 * all 256 states) and every third state at the sixth get the single edits, the no-change return and the follow-up
 * question, with jumps between kept questions and double edits on a stride; the other contexts run every fifth state. EDIT_REPLAY_EXHAUSTIVE=1 runs
 * them on every state of every context (minutes) and can write its counts to EDIT_REPLAY_COUNTS_FILE.
 */
import { writeFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { SLOTS } from "../packages/flavor-data/src/product-vector-v1/flow";
import type { Slot } from "../packages/flavor-data/src/product-vector-v1/flow";
import {
  answer,
  answerAndReplay,
  answerQ6,
  createSession,
  firstDescription,
  nextStep,
  reopenQuestion,
  resumeKept,
  submitPicks,
} from "../packages/flavor-data/src/product-vector-v1/session";
import type {
  KeptAnswers,
  Session,
} from "../packages/flavor-data/src/product-vector-v1/session";

const OPTIONS: Record<Slot, string[]> = {
  Q0: ["A", "B", "C", "D"],
  Q1: ["A", "B", "C", "D"],
  Q2: ["A", "B", "C", "D"],
  Q3: ["A", "B", "C", "D"],
  Q4: ["A", "B", "C"],
  Q5: ["A", "B", "C", "D"],
};
type Ctx = Record<string, string>;
const CONTEXTS: Array<{ name: string; context: Ctx }> = [
  {
    name: "light pour-over, washed gesha, Ethiopia",
    context: {
      c0_preparation: "pour_over_v60",
      c1_roast: "light",
      c2_variety: "gesha",
      c2_process: "washed",
      c2_origin: "ethiopia",
    },
  },
  {
    name: "medium-dark moka pot, washed typica, Brazil",
    context: {
      c0_preparation: "moka_pot",
      c1_roast: "medium_dark",
      c2_variety: "typica",
      c2_process: "washed",
      c2_origin: "brazil",
    },
  },
  {
    name: "dark espresso, natural bourbon",
    context: {
      c0_preparation: "espresso",
      c1_roast: "dark",
      c2_variety: "bourbon",
      c2_process: "natural",
    },
  },
];
const EXHAUSTIVE = process.env.EDIT_REPLAY_EXHAUSTIVE === "1";

const canonical = (value: unknown): string =>
  JSON.stringify(value, (_key, v: unknown) =>
    v && typeof v === "object" && !Array.isArray(v)
      ? Object.fromEntries(
          Object.entries(v as Record<string, unknown>).sort(([a], [b]) =>
            a < b ? -1 : 1,
          ),
        )
      : v,
  );

/**
 * Everything the reader sees and the engine will use, without the event log. The delivery (inference result and
 * description) is a pure function of the state compared here, so the enumeration includes it the first time each final
 * answer set is reached and compares the state alone after that — it keeps the run to seconds without weakening it.
 */
function observable(session: Session, withDelivery = true): string {
  const { history: _history, ...state } = session;
  const delivered =
    withDelivery && session.stage === "describe"
      ? (({ result, description }) => ({ result, description }))(
          firstDescription(session),
        )
      : null;
  return canonical({ state, next: nextStep(session), delivered });
}

/** the engine's own answer: a fresh session given these answers in the order the flow asks for them */
function makeFresh(context: Ctx) {
  const cache = new Map<string, string>();
  const build = (answers: KeptAnswers): Session => {
    let s = createSession(context as never, "zh-CN");
    let guard = 0;
    while (s.stage === "questions" && guard < 10) {
      const step = nextStep(s);
      if (step.kind !== "ask") break;
      const option = answers[step.card.slot as Slot];
      if (!option) break;
      s = answer(s, step.card.slot as Slot, option);
      guard += 1;
    }
    return s;
  };
  const seen = (answers: KeptAnswers, withDelivery = true): string => {
    const key = `${withDelivery ? "full" : "state"}:${canonical(answers)}`;
    let value = cache.get(key);
    if (value === undefined) {
      value = observable(build(answers), withDelivery);
      cache.set(key, value);
    }
    return value;
  };
  return { build, seen };
}

const before = (answers: KeptAnswers, target: Slot): KeptAnswers =>
  Object.fromEntries(
    Object.entries(answers).filter(
      ([slot]) => SLOTS.indexOf(slot as Slot) < SLOTS.indexOf(target),
    ),
  );
const fromOn = (answers: KeptAnswers, target: Slot): KeptAnswers =>
  Object.fromEntries(
    Object.entries(answers).filter(
      ([slot]) => SLOTS.indexOf(slot as Slot) >= SLOTS.indexOf(target),
    ),
  );

/** every state a reader can be in on a question card: one to five answers given, the flow still asking */
function reachableStates(context: Ctx): Session[] {
  const out: Session[] = [];
  const walk = (s: Session) => {
    const step = nextStep(s);
    if (step.kind !== "ask") return;
    if (Object.keys(s.answers).length > 0) out.push(s);
    for (const option of OPTIONS[step.card.slot as Slot])
      walk(answer(s, step.card.slot as Slot, option));
  };
  walk(createSession(context as never, "zh-CN"));
  return out;
}

describe("editing earlier answers keeps the engine's computation exact (enumeration)", () => {
  it.each(CONTEXTS)(
    "$name",
    ({ name, context }) => {
      const primary = name === CONTEXTS[0]!.name;
      const fresh = makeFresh(context);
      const states = reachableStates(context);
      const counts = {
        states: states.length,
        atFifthQuestion: 0,
        reopen: 0,
        resume: 0,
        singleEdit: 0,
        jumpThenEdit: 0,
        continuedAfterEdit: 0,
        doubleEdit: 0,
        delivered: 0,
      };
      const failures: string[] = [];
      const deliveryChecked = new Set<string>();
      const check = (label: string, actual: Session, answers: KeptAnswers) => {
        const key = canonical(answers);
        const full = !deliveryChecked.has(key);
        deliveryChecked.add(key);
        if (observable(actual, full) !== fresh.seen(answers, full))
          failures.push(`${label} | final answers ${key}`);
        if (actual.stage === "describe") counts.delivered += 1;
      };

      states.forEach((state, index) => {
        const known: KeptAnswers = { ...state.answers };
        const answered = Object.keys(known) as Slot[];
        if (answered.length === 4) counts.atFifthQuestion += 1;
        if (!EXHAUSTIVE) {
          if (!primary && index % 5 !== 0) return;
          if (primary && answered.length === 5 && index % 3 !== 0) return;
        }
        const jumps = EXHAUSTIVE || (primary && index % 8 === 0);
        const doubleEdits = EXHAUSTIVE || (primary && index % 48 === 0);

        for (const target of answered) {
          // reopen: the answers before the target are applied, the rest are kept, the target is the question on screen
          const opened = reopenQuestion(state, target);
          counts.reopen += 1;
          check(`reopen ${target}`, opened.session, before(known, target));
          const asked = nextStep(opened.session);
          if (asked.kind !== "ask" || asked.card.slot !== target)
            failures.push(`reopen ${target}: the target is not on screen`);
          if (canonical(opened.kept) !== canonical(fromOn(known, target)))
            failures.push(`reopen ${target}: kept answers differ`);

          // leave without changing anything: back to exactly where the reader was
          const resumed = resumeKept(opened.session, opened.kept);
          counts.resume += 1;
          check(`resume from ${target}`, resumed.session, known);
          if (Object.keys(resumed.kept).length)
            failures.push(`resume from ${target}: answers left over`);

          // jump to a kept question without answering, change that one instead
          for (const other of (jumps ? answered : []).filter(
            (slot) => SLOTS.indexOf(slot) > SLOTS.indexOf(target),
          )) {
            const jumped = reopenQuestion(opened.session, other, opened.kept);
            check(
              `jump ${target}→${other}`,
              jumped.session,
              before(known, other),
            );
            for (const option of OPTIONS[other]) {
              const edited = answerAndReplay(
                jumped.session,
                other,
                option,
                jumped.kept,
              );
              counts.jumpThenEdit += 1;
              check(`jump ${target}→${other}:=${option}`, edited.session, {
                ...known,
                [other]: option,
              });
            }
          }

          // change the target (every option, the same one included); the kept answers replay
          for (const option of OPTIONS[target]) {
            const edited = answerAndReplay(
              opened.session,
              target,
              option,
              opened.kept,
            );
            const after: KeptAnswers = { ...known, [target]: option };
            counts.singleEdit += 1;
            check(`edit ${target}:=${option}`, edited.session, after);
            if (edited.session.stage !== "questions") {
              if (Object.keys(edited.kept).length)
                failures.push(`edit ${target}:=${option}: kept after delivery`);
              continue;
            }

            // carry on from where the edit left the reader — the question they were on, or one the new path added —
            // with every option: what follows an edit must be what the engine computes too
            const step = nextStep(edited.session);
            if (
              (EXHAUSTIVE || index % 2 === 0) &&
              step.kind === "ask" &&
              !after[step.card.slot as Slot]
            ) {
              const slot = step.card.slot as Slot;
              for (const extra of OPTIONS[slot]) {
                const continued = answerAndReplay(
                  edited.session,
                  slot,
                  extra,
                  edited.kept,
                );
                counts.continuedAfterEdit += 1;
                check(
                  `edit ${target}:=${option} then ${slot}:=${extra}`,
                  continued.session,
                  {
                    ...after,
                    [slot]: extra,
                  },
                );
              }
            }

            // a second edit from the state the first one left
            if (!doubleEdits) continue;
            const knownAfter: KeptAnswers = {
              ...edited.session.answers,
              ...edited.kept,
            };
            for (const second of Object.keys(
              edited.session.answers,
            ) as Slot[]) {
              const reopened = reopenQuestion(
                edited.session,
                second,
                edited.kept,
              );
              for (const option2 of OPTIONS[second]) {
                const twice = answerAndReplay(
                  reopened.session,
                  second,
                  option2,
                  reopened.kept,
                );
                counts.doubleEdit += 1;
                check(
                  `edit ${target}:=${option} then ${second}:=${option2}`,
                  twice.session,
                  { ...knownAfter, [second]: option2 },
                );
              }
            }
          }
        }
      });

      if (process.env.EDIT_REPLAY_COUNTS_FILE)
        writeFileSync(
          `${process.env.EDIT_REPLAY_COUNTS_FILE}.${CONTEXTS.findIndex((c) => c.name === name)}.json`,
          JSON.stringify({
            name,
            exhaustive: EXHAUSTIVE,
            failures: failures.length,
            ...counts,
          }),
        );
      expect(failures.slice(0, 5)).toEqual([]);
      if (primary || EXHAUSTIVE) {
        expect(counts.atFifthQuestion).toBe(256);
        expect(counts.singleEdit).toBeGreaterThan(5_000);
        expect(counts.jumpThenEdit).toBeGreaterThan(1_000);
        expect(counts.doubleEdit).toBeGreaterThan(3_000);
      } else {
        expect(counts.singleEdit).toBeGreaterThan(2_000);
      }
      expect(counts.delivered).toBeGreaterThan(0);
    },
    EXHAUSTIVE ? 1_800_000 : 240_000,
  );

  it.each(CONTEXTS)(
    "back into the questions from the description or the final card: $name",
    ({ name, context }) => {
      // the stack's question cards reopen a question after the flow has delivered (owner, 2026-09-18): the words, the
      // picks and the card are rebuilt from the engine's new result, so the state must again equal a fresh session's
      const primary = name === CONTEXTS[0]!.name;
      const fresh = makeFresh(context);
      const delivered: Session[] = [];
      const walk = (s: Session) => {
        const step = nextStep(s);
        if (step.kind !== "ask") {
          delivered.push(s);
          return;
        }
        for (const option of OPTIONS[step.card.slot as Slot])
          walk(answer(s, step.card.slot as Slot, option));
      };
      walk(createSession(context as never, "zh-CN"));
      const stride = EXHAUSTIVE ? 1 : primary ? 24 : 96;
      const counts = {
        delivered: delivered.length,
        from: 0,
        reopen: 0,
        edits: 0,
      };
      const failures: string[] = [];
      const deliveryChecked = new Set<string>();
      const check = (label: string, actual: Session, answers: KeptAnswers) => {
        const key = canonical(answers);
        const full = !deliveryChecked.has(key);
        deliveryChecked.add(key);
        if (observable(actual, full) !== fresh.seen(answers, full))
          failures.push(`${label} | final answers ${key}`);
      };

      delivered.forEach((done, index) => {
        if (index % stride !== 0) return;
        const known: KeptAnswers = { ...done.answers };
        const described = firstDescription(done);
        let confirmed = submitPicks(
          described,
          described.description!.all.slice(0, 5),
        );
        if (confirmed.stage === "q6")
          confirmed = answerQ6(confirmed, [
            confirmed.q6!.options[0]!.dimension,
          ]);
        expect(confirmed.stage).toBe("final");

        for (const from of [described, confirmed]) {
          counts.from += 1;
          for (const target of Object.keys(known) as Slot[]) {
            const opened = reopenQuestion(from, target);
            counts.reopen += 1;
            check(
              `${from.stage}: reopen ${target}`,
              opened.session,
              before(known, target),
            );
            if (
              opened.session.description ||
              opened.session.card ||
              opened.session.picks.length
            )
              failures.push(
                `${from.stage}: reopen ${target} kept a stale description, picks or card`,
              );
            check(
              `${from.stage}: resume from ${target}`,
              resumeKept(opened.session, opened.kept).session,
              known,
            );
            for (const option of OPTIONS[target]) {
              const edited = answerAndReplay(
                opened.session,
                target,
                option,
                opened.kept,
              );
              counts.edits += 1;
              check(
                `${from.stage}: edit ${target}:=${option}`,
                edited.session,
                {
                  ...known,
                  [target]: option,
                },
              );
            }
          }
        }
      });

      if (process.env.EDIT_REPLAY_COUNTS_FILE)
        writeFileSync(
          `${process.env.EDIT_REPLAY_COUNTS_FILE}.delivered.${CONTEXTS.findIndex((c) => c.name === name)}.json`,
          JSON.stringify({
            name,
            exhaustive: EXHAUSTIVE,
            failures: failures.length,
            ...counts,
          }),
        );
      expect(failures.slice(0, 5)).toEqual([]);
      // coherent paths deliver after five questions, so the answer tree has fewer than 3,072 delivering leaves
      expect(counts.delivered).toBeGreaterThan(2_000);
      expect(counts.edits).toBeGreaterThan(
        primary || EXHAUSTIVE ? 4_000 : 1_000,
      );
    },
    EXHAUSTIVE ? 1_800_000 : 240_000,
  );

  it("the owner's walk-through: on the fourth question, go back to the second, keep the third, return to the fourth", () => {
    const context = CONTEXTS[1]!.context;
    const fresh = makeFresh(context);
    const atFourth = fresh.build({ Q0: "B", Q1: "C", Q2: "B" });
    expect(nextStep(atFourth)).toMatchObject({
      kind: "ask",
      card: { slot: "Q3" },
    });

    const opened = reopenQuestion(atFourth, "Q1");
    expect(opened.kept).toEqual({ Q1: "C", Q2: "B" });
    expect(opened.replayed.map((r) => r.slot)).toEqual(["Q0"]);

    // not changing anything: tapping the fourth segment applies the second and third answers as they were
    const untouched = resumeKept(opened.session, opened.kept);
    expect(observable(untouched.session)).toBe(observable(atFourth));
    expect(untouched.replayed.map((r) => `${r.slot}:${r.option}`)).toEqual([
      "Q1:C",
      "Q2:B",
    ]);

    // changing the second answer: the third is recomputed under it with the reader's original choice
    const changed = answerAndReplay(opened.session, "Q1", "B", opened.kept);
    expect(changed.replayed.map((r) => `${r.slot}:${r.option}`)).toEqual([
      "Q2:B",
    ]);
    expect(changed.replayed[0]!.prompt).not.toBe(
      untouched.replayed[1]!.prompt, // the third question's lead-in follows the new second answer
    );
    expect(observable(changed.session)).toBe(
      fresh.seen({ Q0: "B", Q1: "B", Q2: "B" }),
    );
    expect(nextStep(changed.session)).toMatchObject({
      kind: "ask",
      card: { slot: "Q3" },
    });
  });
});

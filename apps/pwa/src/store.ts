/**
 * The only bridge between the algorithm and the UI (owner: 算法归算法，UI 归 UI).
 * One session lives here; every user action calls a session function and refreshes
 * `screen = shallowRef(screenModel(session))`. The UI-only state (collected cards in the top zone,
 * the short "collecting" animation, the context stepper) also lives here so components stay dumb.
 */
import { computed, ref, shallowRef, watch } from "vue";
import type {
  ContextAnswers,
  Locale,
} from "flavor-data/product-vector-v1/engine";
import { isQuestionKey } from "flavor-data/product-vector-v1/dynamicBank";
import type { Word } from "flavor-data/product-vector-v1/flow";
import {
  answer,
  answerAndReplay,
  answerQ6,
  createSession,
  firstDescription,
  nextStep,
  relocalize,
  reopenQuestion,
  resumeKept,
  submitPicks,
  type Session,
} from "flavor-data/product-vector-v1/session";
import {
  appShell,
  contextCatalog,
  normalizeContext,
  screenModel,
  type ContextCard,
  type ScreenModel,
} from "flavor-data/product-vector-v1/view";
import {
  aboutCitations,
  aboutSections,
} from "flavor-data/product-vector-v1/about";
import { beansAsVectors, userDatabase } from "flavor-data/user-db";

export type Stage = "hero" | "context" | "session";
export type CollectedCard = {
  key: string;
  title: string;
  label: string;
  color: string;
};

/** card colours: the Big Sur bag palette (owner, 2026-09-12), one flat block per step; the final card is the navy block */
// Every card of a flow has its own colour (owner, 2026-09-20: no colour twice, and brighter, purer than before — the
// olive of the overall question read as dark). Fifteen hues about 24° apart at high saturation and 72–80% lightness,
// so the ink on them keeps its contrast; the five context cards and the four core questions are always on screen
// together, the follow-ups take the hues left between them. A second level has its own colour, not its parent's.
export const COLORS: Record<string, string> = {
  c0_preparation: "#FFD84D", // yellow
  c1_roast: "#FFB98A", // peach
  c2_variety: "#7CE3B5", // mint
  c2_process: "#FF94BE", // pink
  c2_origin: "#A6E36A", // leaf
  Q0: "#BDA3FF", // lavender
  Q1: "#FF8E6E", // coral
  Q2: "#D6EC5A", // lime
  Q3: "#7ED6F5", // sky
  Q4: "#DFA3FF", // orchid — bitterness
  Q5: "#94BEFF", // blue — the overall impression
  E1: "#7FE38B", // green — how strong the aroma is
  E2: "#A9ADFF", // periwinkle — the aftertaste
  "S:A": "#FF9FE5", // magenta — which fruit
  "S:B": "#6FE3D6", // aqua — which aroma word
  description: "#EFE7D5",
  final: "#1F3B5C",
  escalation: "#8C4A4C",
  hero: "#A995E3",
};
/** the pause between a tap and the card folding away: long enough to read the highlight, short enough not to lag
 *  (520 → 240 ms after users reported the flow as sluggish, owner 2026-09-17) */
export const COLLECT_MS = 240;

// the language follows the device on first open — Chinese devices get 中文, everyone else English — and a manual
// switch is remembered on this device (owner, 2026-09-17: English users must not land on a Chinese screen)
const LOCALE_KEY = "flavorwords.locale";
function initialLocale(): Locale {
  try {
    const saved = localStorage.getItem(LOCALE_KEY);
    if (saved === "zh-CN" || saved === "en") return saved;
  } catch {
    /* storage unavailable: fall through to the device language */
  }
  const primary =
    typeof navigator === "undefined"
      ? ""
      : (navigator.languages?.[0] ?? navigator.language ?? "");
  return /^zh/i.test(primary) ? "zh-CN" : "en";
}
export const locale = ref<Locale>(initialLocale());
watch(
  locale,
  (l) => {
    if (typeof document !== "undefined") document.documentElement.lang = l;
  },
  { immediate: true },
);
export const stage = ref<Stage>("hero");
/** a flow left through the wordmark or the exit button: the home page offers 继续 until 开始 or 首页 clears it (owner, 2026-09-17) */
export const paused = ref<Stage | null>(null);
export const aboutOpen = ref(false);
export const online = ref(
  typeof navigator === "undefined" ? true : navigator.onLine,
);
export const session = shallowRef<Session | null>(null);
export const screen = shallowRef<ScreenModel | null>(null);
export const draftContext = ref<ContextAnswers>({});
export const contextIndex = ref(0);
export const collected = ref<CollectedCard[]>([]);
export const collecting = ref(false);

export const shell = computed(() => appShell(locale.value));

/** the bottom block's colour: the whole page takes it (owner: the two blocks are the page, not a card on a background) */
export const stageColor = computed(() => {
  if (stage.value === "hero") return COLORS.hero!;
  if (stage.value === "context")
    return (
      COLORS[currentContextCard.value?.key ?? "c0_preparation"] ??
      COLORS.c0_preparation!
    );
  const s = screen.value;
  if (!s) return COLORS.description!;
  if (s.kind === "question") return questionColor(s.slot);
  if (s.kind === "first_description" || s.kind === "describe_ready")
    return COLORS.description!;
  if (s.kind === "escalation") return COLORS.escalation!;
  return COLORS.final!;
});

/** ink on light blocks, paper on dark blocks */
export function onColor(hex: string): string {
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 255,
    g = (n >> 8) & 255,
    b = n & 255;
  const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
  return luminance > 0.6 ? "#1E1C1A" : "#FFFFFF";
}
export const stageInk = computed(() => onColor(stageColor.value));
export const catalog = computed(() => contextCatalog(locale.value));
export const currentContextCard = computed<ContextCard | null>(
  () => catalog.value[contextIndex.value] ?? null,
);
export const about = computed(() => ({
  sections: aboutSections(locale.value),
  citations: aboutCitations(locale.value),
}));

if (typeof window !== "undefined") {
  window.addEventListener("online", () => (online.value = true));
  window.addEventListener("offline", () => (online.value = false));
}

function refresh() {
  screen.value = session.value ? screenModel(session.value) : null;
}

function collect(card: CollectedCard) {
  collected.value = [...collected.value, card];
}

function wait(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

export function toggleLocale() {
  locale.value = locale.value === "zh-CN" ? "en" : "zh-CN";
  try {
    localStorage.setItem(LOCALE_KEY, locale.value);
  } catch {
    /* storage unavailable: the choice lasts for this visit */
  }
  if (session.value) {
    session.value = relocalize(session.value, locale.value);
    refresh();
  }
}

export function start() {
  keptAnswers.value = {};
  paused.value = null;
  session.value = null;
  screen.value = null;
  stage.value = "context";
  draftContext.value = {};
  contextIndex.value = 0;
  collected.value = [];
}

/** the wordmark and the exit button: back to the home page, the flow kept for 继续 */
export function exitToHome() {
  if (stage.value === "hero") return;
  paused.value = stage.value;
  stage.value = "hero";
}

/** 继续: back into the flow exactly where it was left */
export function resume() {
  if (!paused.value) return;
  stage.value = paused.value;
  paused.value = null;
}

/** value(s) chosen on the current context card, as a list */
export function contextSelection(key: string): string[] {
  const value = (
    draftContext.value as Record<string, string | string[] | undefined>
  )[key];
  return Array.isArray(value) ? value : value ? [value] : [];
}

export function chooseContext(
  key: string,
  value: string,
  multi: boolean,
  max = 3,
) {
  const draft = { ...draftContext.value } as Record<
    string,
    string | string[] | undefined
  >;
  if (multi) {
    const current = contextSelection(key);
    draft[key] = current.includes(value)
      ? current.filter((v) => v !== value)
      : current.length < max
        ? [...current, value]
        : current;
  } else {
    draft[key] = draft[key] === value ? undefined : value;
  }
  draftContext.value = draft as ContextAnswers;
}

/** the current context card folds into the stack; the last card starts the session */
export async function advanceContext(labelForStack: string) {
  const card = currentContextCard.value;
  if (!card) return;
  collecting.value = true;
  await wait(COLLECT_MS);
  collect({
    key: card.key,
    title: card.title,
    label: labelForStack,
    color: COLORS[card.key] ?? "#9B7B5D",
  });
  if (contextIndex.value < catalog.value.length - 1) {
    contextIndex.value += 1;
    collecting.value = false;
    return;
  }
  const beans = await beansAsVectors(userDatabase()).catch(() => []);
  session.value = createSession(
    normalizeContext(draftContext.value),
    locale.value,
    beans,
    Date.now(), // the nonce: another visit may draw a different supporting statistic, wording and second follow-up
    "dynamic", // the dynamic question bank (R3-D40): four core questions, two follow-ups at most
  );
  stage.value = "session";
  refresh();
  collecting.value = false;
}

export async function pick(
  slot: string,
  option: string,
  label: string,
  title: string,
) {
  if (!session.value) return;
  collecting.value = true;
  await wait(COLLECT_MS);
  collect({ key: slot, title, label, color: questionColor(slot) });
  const edited = answerAndReplay(
    session.value,
    slot,
    option,
    keptAnswers.value,
  );
  for (const r of edited.replayed)
    collect(stackCard(r.slot, r.prompt, r.label));
  keptAnswers.value = edited.kept;
  let next = edited.session;
  if (next.stage === "describe") next = firstDescription(next);
  session.value = next;
  refresh();
  collecting.value = false;
}

/** the questions answered so far, in the order they were asked (the stack's question cards) */
export const answeredSlots = computed(() =>
  collected.value.map((c) => c.key).filter(isQuestionKey),
);

/** every question has its own colour; the second level of a fruit answer (S:A…) and of an aroma answer (S:B…) too */
const questionColor = (key: string): string =>
  COLORS[key] ?? COLORS[key.slice(0, 3)] ?? COLORS.Q0!;

/**
 * Going back through the progress segments keeps the other answers (owner, 2026-09-18). The logic is the engine's
 * (session.ts: reopenQuestion / answerAndReplay, enumerated in tests/product-vector-v1-edit-replay); the store only
 * holds the kept answers and folds the stack to match.
 */
export const keptAnswers = ref<Partial<Record<string, string>>>({});

const stackCard = (
  slot: string,
  title: string,
  label: string,
): CollectedCard => ({
  key: slot,
  title,
  label,
  color: questionColor(slot),
});

/** open an answered (or kept) question for editing: the answers before it stay applied, the rest are kept for replay */
export function editSlot(target: string) {
  const current = session.value;
  if (!current || collecting.value) return;
  const known = { ...current.answers, ...keptAnswers.value };
  if (!known[target]) return;
  const edited = reopenQuestion(current, target, keptAnswers.value);
  collected.value = [
    ...collected.value.filter(
      (c) => !isQuestionKey(c.key) && c.key !== "picks",
    ),
    ...edited.replayed.map((r) => stackCard(r.slot, r.prompt, r.label)),
  ];
  keptAnswers.value = edited.kept;
  session.value = edited.session;
  refresh();
}

/** back to where the reader was, with every kept answer applied unchanged (the first open segment after the kept ones) */
export function resumeEditing() {
  const current = session.value;
  if (!current || collecting.value) return;
  if (!Object.keys(keptAnswers.value).length) return;
  const edited = resumeKept(current, keptAnswers.value);
  for (const r of edited.replayed)
    collect(stackCard(r.slot, r.prompt, r.label));
  keptAnswers.value = edited.kept;
  let next = edited.session;
  if (next.stage === "describe") next = firstDescription(next);
  session.value = next;
  refresh();
}

export type ProgressSegment = {
  slot: string | null;
  /** frontier: where the reader was before going back — tapping it applies the kept answers and returns there */
  state: "answered" | "current" | "kept" | "frontier" | "future";
  /** a frontier that is the description itself: the kept answers complete the flow */
  delivers?: boolean;
};
/** the progress row of a question card: answered questions, the current one, kept answers after it, then the rest */
export const progressSegments = computed<ProgressSegment[]>(() => {
  const model = screen.value;
  if (!model || model.kind !== "question") return [];
  const current = model.slot;
  const segments: ProgressSegment[] = [
    ...answeredSlots.value.map((slot) => ({
      slot,
      state: "answered" as const,
    })),
    { slot: current, state: "current" as const },
    // the kept answers keep the order the questions were asked in
    ...Object.keys(keptAnswers.value)
      .filter((slot) => slot !== current && keptAnswers.value[slot])
      .map((slot) => ({ slot, state: "kept" as const })),
  ];
  if (Object.keys(keptAnswers.value).length > 0 && session.value)
    segments.push({
      slot: null,
      state: "frontier",
      delivers:
        resumeKept(session.value, keptAnswers.value).session.stage !==
        "questions",
    });
  const total = Math.max(model.progress.expected, segments.length);
  while (segments.length < total)
    segments.push({ slot: null, state: "future" });
  return segments;
});

export async function submitPickedWords(words: Word[]) {
  if (!session.value) return;
  collecting.value = true;
  await wait(COLLECT_MS);
  collect({
    key: "picks",
    title: locale.value === "zh-CN" ? "候选风味描述" : "Candidate descriptions",
    label: words.map((w) => w.text).join(" · "),
    color: COLORS.description!,
  });
  session.value = submitPicks(session.value, words);
  refresh();
  collecting.value = false;
}

export function submitQ6(dimensions: string[]) {
  if (!session.value) return;
  session.value = answerQ6(session.value, dimensions);
  refresh();
}

// The flow survives closing the app for a few hours (owner, 2026-09-17): a paused or half-finished flow comes back as
// 继续 on the next open; older than FLOW_TTL_MS it is dropped and the app opens clean. What is saved are the inputs
// (context, answers, picks, second look) and the stack's labels; the session is rebuilt by replaying them through the
// engine, which is deterministic.
const FLOW_KEY = "flavorwords.flow";
export const FLOW_TTL_MS = 6 * 60 * 60 * 1000;
type SavedFlow = {
  savedAt: number;
  stage: Exclude<Stage, "hero">;
  draftContext: ContextAnswers;
  contextIndex: number;
  collected: CollectedCard[];
  answers: Partial<Record<string, string>>;
  kept?: Partial<Record<string, string>>;
  /** a flow saved by the six fixed questions cannot be replayed by the dynamic bank: it is dropped */
  mode?: "dynamic";
  nonce?: number;
  picks: Word[] | null;
  q6: string[] | null;
};

function readSavedFlow(): SavedFlow | null {
  try {
    const raw = localStorage.getItem(FLOW_KEY);
    if (!raw) return null;
    const saved = JSON.parse(raw) as SavedFlow;
    if (
      typeof saved.savedAt !== "number" ||
      Date.now() - saved.savedAt > FLOW_TTL_MS ||
      (saved.stage !== "context" && saved.stage !== "session") ||
      // answers given to the six fixed questions mean nothing to the dynamic bank: such a flow starts over
      (saved.stage === "session" && saved.mode !== "dynamic")
    ) {
      localStorage.removeItem(FLOW_KEY);
      return null;
    }
    return saved;
  } catch {
    return null;
  }
}

function saveFlow() {
  const live: Stage | null =
    stage.value === "hero" ? paused.value : stage.value;
  const current = live === "context" || live === "session" ? live : null;
  try {
    if (!current) {
      localStorage.removeItem(FLOW_KEY);
      return;
    }
    const s = session.value;
    const saved: SavedFlow = {
      savedAt: Date.now(),
      stage: current,
      draftContext: draftContext.value,
      contextIndex: contextIndex.value,
      collected: collected.value,
      answers: s?.answers ?? {},
      mode: "dynamic",
      kept: keptAnswers.value,
      nonce: s?.nonce ?? 0,
      picks: s && s.picks.length ? s.picks : null,
      q6: s?.q6 && s.q6.selected.length ? s.q6.selected : null,
    };
    localStorage.setItem(FLOW_KEY, JSON.stringify(saved));
  } catch {
    /* storage unavailable: the flow lasts for this visit */
  }
}
watch(
  [stage, paused, contextIndex, draftContext, collected, session],
  saveFlow,
  {
    deep: true,
  },
);

/** on launch: bring a saved flow back as a paused one (the home page shows 继续), or drop it when it is stale */
export async function restoreFlow() {
  const saved = readSavedFlow();
  if (!saved) return;
  draftContext.value = saved.draftContext;
  contextIndex.value = saved.contextIndex;
  collected.value = saved.collected;
  if (saved.stage === "session") {
    const beans = await beansAsVectors(userDatabase()).catch(() => []);
    let s = createSession(
      normalizeContext(saved.draftContext),
      locale.value,
      beans,
      saved.nonce ?? Date.now(),
      "dynamic",
    );
    let guard = 0;
    while (s.stage === "questions" && guard < 10) {
      const step = nextStep(s);
      if (step.kind !== "ask") break;
      const option = saved.answers[step.card.slot];
      if (!option) break;
      try {
        s = answer(s, step.card.slot, option);
      } catch {
        break; // an option this build no longer shows: the reader continues from this question
      }
      guard += 1;
    }
    if (s.stage === "describe") s = firstDescription(s);
    if (saved.picks && s.stage === "picks" && s.description) {
      const words = saved.picks
        .map((p) => s.description!.all.find((w) => w.text === p.text))
        .filter((w): w is Word => Boolean(w));
      if (words.length === saved.picks.length) s = submitPicks(s, words);
    }
    if (saved.q6 && s.stage === "q6") s = answerQ6(s, saved.q6);
    session.value = s;
    keptAnswers.value = saved.kept ?? {};
    refresh();
  }
  paused.value = saved.stage;
  stage.value = "hero";
}

export function home() {
  keptAnswers.value = {};
  paused.value = null;
  session.value = null;
  screen.value = null;
  collected.value = [];
  contextIndex.value = 0;
  stage.value = "hero";
}

/** 重新体验: straight into a fresh diagnosis */
export function restart() {
  home();
  start();
}

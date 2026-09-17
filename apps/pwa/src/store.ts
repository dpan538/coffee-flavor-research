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
import type { Word, Slot } from "flavor-data/product-vector-v1/flow";
import {
  answer,
  answerQ6,
  createSession,
  firstDescription,
  nextStep,
  relocalize,
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
export const COLORS: Record<string, string> = {
  c0_preparation: "#F3D66E",
  c1_roast: "#FFDCC8",
  c2_variety: "#C9DB6E",
  c2_process: "#E97BAF",
  c2_origin: "#6F8B5A",
  Q0: "#A995E3",
  Q1: "#E4724B",
  Q2: "#C9DB6E",
  Q3: "#F2C7B5",
  Q4: "#E97BAF",
  Q5: "#CBBB4C",
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
  if (s.kind === "question") return COLORS[s.slot] ?? COLORS.Q0!;
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
  );
  stage.value = "session";
  refresh();
  collecting.value = false;
}

export async function pick(
  slot: Slot,
  option: string,
  label: string,
  title: string,
) {
  if (!session.value) return;
  collecting.value = true;
  await wait(COLLECT_MS);
  collect({ key: slot, title, label, color: COLORS[slot] ?? "#7F90B8" });
  session.value = answer(session.value, slot, option);
  if (session.value.stage === "describe")
    session.value = firstDescription(session.value);
  refresh();
  collecting.value = false;
}

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
  answers: Partial<Record<Slot, string>>;
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
      (saved.stage !== "context" && saved.stage !== "session")
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
      answers: (s?.answers ?? {}) as Partial<Record<Slot, string>>,
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
    );
    let guard = 0;
    while (s.stage === "questions" && guard < 10) {
      const step = nextStep(s);
      if (step.kind !== "ask") break;
      const option = saved.answers[step.card.slot as Slot];
      if (!option) break;
      s = answer(s, step.card.slot as Slot, option);
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
    refresh();
  }
  paused.value = saved.stage;
  stage.value = "hero";
}

export function home() {
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

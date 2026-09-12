/**
 * The only bridge between the algorithm and the UI (owner: 算法归算法，UI 归 UI).
 * One session lives here; every user action calls a session function and refreshes
 * `screen = shallowRef(screenModel(session))`. The UI-only state (collected cards in the top zone,
 * the short "collecting" animation, the context stepper) also lives here so components stay dumb.
 */
import { shallowRef, ref, computed } from "vue";
import type { ContextAnswers, Locale } from "flavor-data/product-vector-v1/engine";
import type { Word, Slot } from "flavor-data/product-vector-v1/flow";
import { answer, answerQ6, createSession, firstDescription, submitPicks, type Session } from "flavor-data/product-vector-v1/session";
import { appShell, contextCatalog, normalizeContext, screenModel, type ContextCard, type ScreenModel } from "flavor-data/product-vector-v1/view";
import { aboutCitations, aboutSections } from "flavor-data/product-vector-v1/about";
import { beansAsVectors, userDatabase } from "flavor-data/user-db";

export type Stage = "hero" | "context" | "session";
export type CollectedCard = { key: string; title: string; label: string; color: string };

/** card colours: the retro block palette, one per step so the collected stack reads as the book cover */
export const COLORS: Record<string, string> = {
  c0_preparation: "#F2C24E", c1_roast: "#5FAEE8", c2_variety: "#86CBB4", c2_process: "#F5B0C6", c2_origin: "#9B7B5D",
  Q0: "#7268C9", Q1: "#EE8F70", Q2: "#86CBB4", Q3: "#7F90B8", Q4: "#DA8A80", Q5: "#5FAEE8",
  description: "#EFE7D5", final: "#2F7A4C", escalation: "#8C4A4C", hero: "#7268C9",
};
export const COLLECT_MS = 520;

export const locale = ref<Locale>("zh-CN");
export const stage = ref<Stage>("hero");
export const aboutOpen = ref(false);
export const online = ref(typeof navigator === "undefined" ? true : navigator.onLine);
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
  if (stage.value === "context") return COLORS[currentContextCard.value?.key ?? "c0_preparation"] ?? COLORS.c0_preparation!;
  const s = screen.value;
  if (!s) return COLORS.description!;
  if (s.kind === "question") return COLORS[s.slot] ?? COLORS.Q0!;
  if (s.kind === "first_description" || s.kind === "describe_ready") return COLORS.description!;
  if (s.kind === "escalation") return COLORS.escalation!;
  return COLORS.final!;
});

/** ink on light blocks, paper on dark blocks */
export function onColor(hex: string): string {
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
  return luminance > 0.6 ? "#1E1C1A" : "#FFFFFF";
}
export const stageInk = computed(() => onColor(stageColor.value));
export const catalog = computed(() => contextCatalog(locale.value));
export const currentContextCard = computed<ContextCard | null>(() => catalog.value[contextIndex.value] ?? null);
export const about = computed(() => ({ sections: aboutSections(locale.value), citations: aboutCitations(locale.value) }));

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
  if (session.value) {
    session.value = { ...session.value, locale: locale.value };
    refresh();
  }
}

export function start() {
  stage.value = "context";
  draftContext.value = {};
  contextIndex.value = 0;
  collected.value = [];
}

/** value(s) chosen on the current context card, as a list */
export function contextSelection(key: string): string[] {
  const value = (draftContext.value as Record<string, string | string[] | undefined>)[key];
  return Array.isArray(value) ? value : value ? [value] : [];
}

export function chooseContext(key: string, value: string, multi: boolean, max = 3) {
  const draft = { ...draftContext.value } as Record<string, string | string[] | undefined>;
  if (multi) {
    const current = contextSelection(key);
    draft[key] = current.includes(value) ? current.filter((v) => v !== value) : current.length < max ? [...current, value] : current;
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
  collect({ key: card.key, title: card.title, label: labelForStack, color: COLORS[card.key] ?? "#9B7B5D" });
  if (contextIndex.value < catalog.value.length - 1) {
    contextIndex.value += 1;
    collecting.value = false;
    return;
  }
  const beans = await beansAsVectors(userDatabase()).catch(() => []);
  session.value = createSession(normalizeContext(draftContext.value), locale.value, beans);
  stage.value = "session";
  refresh();
  collecting.value = false;
}

export async function pick(slot: Slot, option: string, label: string, title: string) {
  if (!session.value) return;
  collecting.value = true;
  await wait(COLLECT_MS);
  collect({ key: slot, title, label, color: COLORS[slot] ?? "#7F90B8" });
  session.value = answer(session.value, slot, option);
  if (session.value.stage === "describe") session.value = firstDescription(session.value);
  refresh();
  collecting.value = false;
}

export async function submitPickedWords(words: Word[]) {
  if (!session.value) return;
  collecting.value = true;
  await wait(COLLECT_MS);
  collect({ key: "picks", title: locale.value === "zh-CN" ? "你的 5 个词" : "Your 5 words", label: words.map((w) => w.text).join(" · "), color: COLORS.description! });
  session.value = submitPicks(session.value, words);
  refresh();
  collecting.value = false;
}

export function submitQ6(dimensions: string[]) {
  if (!session.value) return;
  session.value = answerQ6(session.value, dimensions);
  refresh();
}

export function home() {
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

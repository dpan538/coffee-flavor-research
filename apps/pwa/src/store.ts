/**
 * The only bridge between the algorithm and the UI (owner: 算法归算法，UI 归 UI).
 * A single session object lives here; every user action calls a session function and refreshes
 * `screen = shallowRef(screenModel(session))`. Nothing in the components computes flavor.
 */
import { shallowRef, ref, computed } from "vue";
import type { ContextAnswers, Locale } from "flavor-data/product-vector-v1/engine";
import type { Word, Slot } from "flavor-data/product-vector-v1/flow";
import { answer, answerQ6, createSession, firstDescription, submitPicks, type Session } from "flavor-data/product-vector-v1/session";
import { appShell, contextCatalog, normalizeContext, screenModel, type ScreenModel } from "flavor-data/product-vector-v1/view";
import { aboutCitations, aboutSections } from "flavor-data/product-vector-v1/about";
import { beansAsVectors, userDatabase } from "flavor-data/user-db";

export type Stage = "hero" | "context" | "session";

export const locale = ref<Locale>("zh-CN");
export const stage = ref<Stage>("hero");
export const aboutOpen = ref(false);
export const online = ref(typeof navigator === "undefined" ? true : navigator.onLine);
export const session = shallowRef<Session | null>(null);
export const screen = shallowRef<ScreenModel | null>(null);
export const draftContext = ref<ContextAnswers>({});

export const shell = computed(() => appShell(locale.value));
export const catalog = computed(() => contextCatalog(locale.value));
export const about = computed(() => ({ sections: aboutSections(locale.value), citations: aboutCitations(locale.value) }));

if (typeof window !== "undefined") {
  window.addEventListener("online", () => (online.value = true));
  window.addEventListener("offline", () => (online.value = false));
}

function refresh() {
  screen.value = session.value ? screenModel(session.value) : null;
}

export function toggleLocale() {
  locale.value = locale.value === "zh-CN" ? "en" : "zh-CN";
  if (session.value) {
    // the vectors do not depend on the locale; rebuild the presentation in the other language
    session.value = { ...session.value, locale: locale.value };
    refresh();
  }
}

export function start() {
  stage.value = "context";
  draftContext.value = {};
}

export async function confirmContext() {
  const beans = await beansAsVectors(userDatabase()).catch(() => []);
  session.value = createSession(normalizeContext(draftContext.value), locale.value, beans);
  stage.value = "session";
  refresh();
}

export function pick(slot: Slot, option: string) {
  if (!session.value) return;
  session.value = answer(session.value, slot, option);
  if (session.value.stage === "describe") session.value = firstDescription(session.value);
  refresh();
}

export function submitPickedWords(words: Word[]) {
  if (!session.value) return;
  session.value = submitPicks(session.value, words);
  refresh();
}

export function submitQ6(dimensions: string[]) {
  if (!session.value) return;
  session.value = answerQ6(session.value, dimensions);
  refresh();
}

export function restart() {
  session.value = null;
  screen.value = null;
  stage.value = "hero";
}

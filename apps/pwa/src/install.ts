// Add to home screen (owner, 2026-09-13): Chrome and Edge hand us an install prompt we can open on tap; Safari on
// iOS and iPadOS has no API, so the sheet explains Share → Add to Home Screen. Hidden once the app runs standalone.
import { computed, ref } from "vue";

const deferred = ref<BeforeInstallPromptEvent | null>(null);
export const installed = ref(
  window.matchMedia("(display-mode: standalone)").matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true,
);

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferred.value = event as BeforeInstallPromptEvent;
});
window.addEventListener("appinstalled", () => {
  installed.value = true;
  deferred.value = null;
});
window
  .matchMedia("(display-mode: standalone)")
  .addEventListener("change", (e) => {
    if (e.matches) installed.value = true;
  });

export const canPrompt = computed(() => deferred.value !== null);

const ua = navigator.userAgent;
export const platform = {
  ios:
    /iPhone|iPad|iPod/.test(ua) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1),
  safari: /Safari/.test(ua) && !/CriOS|FxiOS|EdgiOS|Chrome|Android/.test(ua),
  // HarmonyOS 4 (Android lineage) and HarmonyOS NEXT (ArkWeb) both identify themselves; Huawei Browser installs from its menu
  harmony: /OpenHarmony|HarmonyOS|ArkWeb|HuaweiBrowser/i.test(ua),
  android: /Android/.test(ua),
  // WeChat's in-app browser cannot install; the page has to be opened in the system browser first
  wechat: /MicroMessenger/i.test(ua),
};

/** opens the browser's own prompt when there is one; otherwise the caller shows the sheet */
export async function promptInstall(): Promise<
  "accepted" | "dismissed" | "unavailable"
> {
  const event = deferred.value;
  if (!event) return "unavailable";
  await event.prompt();
  const { outcome } = await event.userChoice;
  if (outcome === "accepted") deferred.value = null;
  return outcome;
}

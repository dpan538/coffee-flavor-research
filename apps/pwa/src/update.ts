// Keeping the installed app current (owner, 2026-09-17): the service worker is registered in "prompt" mode, so a new
// build is downloaded and parked as a waiting worker while the current one keeps serving. The app checks for a new
// build when it starts, whenever it returns to the foreground or comes back online, and once an hour while open. When
// a new build is waiting, App.vue applies it with a silent reload as soon as the app is on the home page (a paused
// flow is saved on the device and comes back), so nobody stays on an old version for more than one visit.
import { ref } from "vue";
import { registerSW } from "virtual:pwa-register";

/** a newer build is installed and waiting to take over */
export const updateReady = ref(false);
/**
 * The worker controlling this page changed under it: this page asked for the swap, or another tab or the installed app
 * did (the new worker claims every open page). Either way the page is now an old build on a new worker and must
 * reload at the next safe moment. Found on 2026-09-19: only the page that asked was listening, the others stayed old.
 */
export const workerSwapped = ref(false);

/**
 * The server offers a build other than the one running here (version.json, always read from the network). It catches
 * what the two events can miss: on a plain reload a waiting worker activates as soon as the old document is gone and
 * claims the freshly loaded old page, possibly before this module listens.
 */
export const staleBuild = ref(false);

const CHECK_EVERY_MS = 60 * 60 * 1000;
const RELOADED_FOR = "flavorwords.reloadedFor";
let served: string | null = null;

async function checkServedBuild() {
  try {
    const response = await fetch(`/version.json?${Date.now()}`, {
      cache: "no-store",
    });
    if (!response.ok) return;
    const build = ((await response.json()) as { build?: string }).build;
    if (!build) return;
    served = build;
    staleBuild.value = build !== __BUILD_ID__;
  } catch {
    /* offline: nothing to compare with */
  }
}
let activate: ((reloadPage?: boolean) => Promise<void>) | null = null;
let registered: ServiceWorkerRegistration | null = null;

export function startUpdates() {
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator))
    return;
  // a first visit has no controller yet; the worker claiming the page then is an install, not an update
  const hadController = Boolean(navigator.serviceWorker.controller);
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (hadController) workerSwapped.value = true;
  });
  activate = registerSW({
    immediate: true,
    onNeedRefresh() {
      updateReady.value = true;
    },
    onRegisteredSW(_url, registration) {
      if (!registration) return;
      registered = registration;
      const check = () => {
        if (!navigator.onLine) return;
        registration.update().catch(() => undefined);
        void checkServedBuild();
      };
      void checkServedBuild();
      window.setInterval(check, CHECK_EVERY_MS);
      document.addEventListener("visibilitychange", () => {
        if (!document.hidden) check();
      });
      window.addEventListener("online", check);
    },
  });
}

/**
 * Called by App.vue at a safe moment (the home page). A waiting worker is told to take over — the controller change
 * that follows brings App.vue back here — and once the worker has changed, the page reloads into the new build.
 */
let reloading = false;
export function applyUpdate() {
  if (reloading) return;
  if (!workerSwapped.value && activate && registered?.waiting) {
    void activate(false);
    return;
  }
  if (!workerSwapped.value && !updateReady.value) {
    // only the version check fired: a new worker still installing will announce itself; with none in sight, reload
    // once for this served build — never in a loop while the old worker keeps answering
    if (registered?.installing) return;
    try {
      if (sessionStorage.getItem(RELOADED_FOR) === served) return;
      sessionStorage.setItem(RELOADED_FOR, served ?? "");
    } catch {
      return;
    }
  }
  reloading = true;
  window.location.reload();
}

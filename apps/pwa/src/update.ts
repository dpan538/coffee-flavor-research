// Keeping the installed app current (owner, 2026-09-17): the service worker is registered in "prompt" mode, so a new
// build is downloaded and parked as a waiting worker while the current one keeps serving. The app checks for a new
// build when it starts, whenever it returns to the foreground or comes back online, and once an hour while open. When
// a new build is waiting, App.vue applies it — a silent reload on a clean home page, or a visible line when a paused
// flow would be lost — so nobody stays on an old version for more than one visit.
import { ref } from "vue";
import { registerSW } from "virtual:pwa-register";

/** a newer build is installed and waiting to take over */
export const updateReady = ref(false);

const CHECK_EVERY_MS = 60 * 60 * 1000;
let activate: ((reloadPage?: boolean) => Promise<void>) | null = null;

export function startUpdates() {
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator))
    return;
  activate = registerSW({
    immediate: true,
    onNeedRefresh() {
      updateReady.value = true;
    },
    onRegisteredSW(_url, registration) {
      if (!registration) return;
      const check = () => {
        if (navigator.onLine) registration.update().catch(() => undefined);
      };
      window.setInterval(check, CHECK_EVERY_MS);
      document.addEventListener("visibilitychange", () => {
        if (!document.hidden) check();
      });
      window.addEventListener("online", check);
    },
  });
}

/** hand over to the waiting build and reload once the new worker controls the page */
let reloading = false;
export function applyUpdate() {
  if (!activate) {
    window.location.reload();
    return;
  }
  // the reload is ours, not the register helper's: its hook depends on how the worker was first registered and did
  // not fire in testing; controllerchange is the moment the new build is the one that will answer the next load
  navigator.serviceWorker.addEventListener(
    "controllerchange",
    () => {
      if (reloading) return;
      reloading = true;
      window.location.reload();
    },
    { once: true },
  );
  void activate(false);
}

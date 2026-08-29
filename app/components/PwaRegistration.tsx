import { useEffect, useState } from "react";

export function PwaRegistration() {
  const [updateReady, setUpdateReady] = useState(false);

  useEffect(() => {
    if (!("serviceWorker" in navigator) || import.meta.env.DEV) return;
    let registration: ServiceWorkerRegistration | undefined;
    navigator.serviceWorker
      .register("/service-worker.js", { scope: "/" })
      .then((value) => {
        registration = value;
        if (value.waiting) setUpdateReady(true);
        value.addEventListener("updatefound", () => {
          const worker = value.installing;
          worker?.addEventListener("statechange", () => {
            if (
              worker.state === "installed" &&
              navigator.serviceWorker.controller
            ) {
              setUpdateReady(true);
            }
          });
        });
      })
      .catch(() => {
        // The app remains fully usable without service-worker support.
      });
    return () =>
      registration?.installing?.removeEventListener(
        "statechange",
        () => undefined,
      );
  }, []);

  if (!updateReady) return null;
  return (
    <button
      className="pwa-update"
      type="button"
      onClick={() => window.location.reload()}
    >
      Update ready — reload / 更新可用
    </button>
  );
}

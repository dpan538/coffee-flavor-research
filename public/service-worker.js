const CACHE_VERSION = "coffee-flavor-atlas-round4a-v2";
const APP_SHELL = [
  "/",
  "/prototype/",
  "/manifest.webmanifest",
  "/icon-192.png",
  "/icon-512.png",
  "/knowledge/round4a-public-v1.json",
];
const RESTRICTED_PATH =
  /(?:\/db\/|\/restricted\/|reviewer|rights[_-]decision)/i;

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(APP_SHELL)),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_VERSION)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (
    request.method !== "GET" ||
    url.origin !== self.location.origin ||
    RESTRICTED_PATH.test(url.pathname)
  )
    return;
  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request)
        .then((response) => {
          if (response.ok)
            caches
              .open(CACHE_VERSION)
              .then((cache) => cache.put(request, response.clone()));
          return response;
        })
        .catch(() => cached ?? caches.match("/prototype/"));
      return cached ?? network;
    }),
  );
});

import { createScope, type Scope } from "animejs";
import { useEffect, useRef } from "react";

export function useAnimeScope<T extends HTMLElement>() {
  const rootRef = useRef<T | null>(null);
  const scopeRef = useRef<Scope | null>(null);

  useEffect(() => {
    if (!rootRef.current) {
      return;
    }

    const scope = createScope({ root: rootRef.current });
    scopeRef.current = scope;
    window.__coffeeAtlasDebug = {
      ...window.__coffeeAtlasDebug,
      animeScopes: (window.__coffeeAtlasDebug?.animeScopes ?? 0) + 1,
    };

    return () => {
      scope.revert();
      scopeRef.current = null;
      window.__coffeeAtlasDebug = {
        ...window.__coffeeAtlasDebug,
        animeScopes: Math.max(
          0,
          (window.__coffeeAtlasDebug?.animeScopes ?? 1) - 1,
        ),
      };
    };
  }, []);

  return { rootRef, scopeRef };
}

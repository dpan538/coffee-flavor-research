import { onScroll, type ScrollObserver } from "animejs";
import { useEffect } from "react";
import type { RefObject } from "react";
import { useReducedMotion } from "./reducedMotion";

export function useScrollScene(root: RefObject<HTMLElement | null>) {
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (reducedMotion || !root.current) {
      return;
    }

    const observers: ScrollObserver[] = [];

    root.current
      .querySelectorAll<HTMLElement>("[data-scroll-scene]")
      .forEach((scene) => {
        const observer = onScroll({
          target: scene,
          enter: "bottom top",
          leave: "top bottom",
          sync: 0.25,
          onUpdate: ({ progress }) => {
            scene.style.setProperty("--scroll-progress", progress.toFixed(3));
          },
        });
        observers.push(observer);

        scene
          .querySelectorAll<HTMLElement>("[data-reveal]")
          .forEach((element) => {
            element.style.opacity = "1";
            element.style.transform = "translateY(0)";
          });
      });

    window.__coffeeAtlasDebug = {
      ...window.__coffeeAtlasDebug,
      scrollObservers:
        (window.__coffeeAtlasDebug?.scrollObservers ?? 0) + observers.length,
    };

    return () => {
      observers.forEach((observer) => observer.revert());
      window.__coffeeAtlasDebug = {
        ...window.__coffeeAtlasDebug,
        scrollObservers: Math.max(
          0,
          (window.__coffeeAtlasDebug?.scrollObservers ?? observers.length) -
            observers.length,
        ),
      };
    };
  }, [reducedMotion, root]);
}

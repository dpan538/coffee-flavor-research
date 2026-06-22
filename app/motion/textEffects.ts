import { animate, splitText } from "animejs";
import { useEffect } from "react";
import type { RefObject } from "react";
import { useReducedMotion } from "./reducedMotion";

export function useTextReveal(root: RefObject<HTMLElement | null>) {
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (reducedMotion || !root.current) {
      return;
    }

    const splitters: Array<{ revert: () => void }> = [];

    const run = () => {
      root.current
        ?.querySelectorAll<HTMLElement>("[data-text-reveal]")
        .forEach((element) => {
          const splitter = splitText(element, { words: true, chars: false });
          splitters.push(splitter);
          animate(splitter.words, {
            opacity: [0, 1],
            translateY: ["0.8em", 0],
            delay: (_target: unknown, index: number) => index * 28,
            duration: 520,
            ease: "outExpo",
          });
        });
    };

    document.fonts.ready.then(run);

    return () => {
      splitters.forEach((splitter) => splitter.revert());
    };
  }, [reducedMotion, root]);
}

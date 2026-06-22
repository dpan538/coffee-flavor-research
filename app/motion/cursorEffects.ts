import { animate } from "animejs";
import { useEffect, useMemo, useRef, useState } from "react";
import { useReducedMotion } from "./reducedMotion";

export type CursorMode =
  | "default"
  | "view"
  | "open"
  | "compare"
  | "drag"
  | "back"
  | "source"
  | "category";

export function useFinePointer() {
  const [finePointer, setFinePointer] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(pointer: fine) and (hover: hover)");
    const update = () => setFinePointer(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  return finePointer;
}

export function useCursorMode() {
  const [mode, setMode] = useState<CursorMode>("default");
  const [label, setLabel] = useState("");

  return useMemo(
    () => ({
      mode,
      label,
      setCursor: (nextMode: CursorMode, nextLabel = "") => {
        setMode(nextMode);
        setLabel(nextLabel);
      },
      resetCursor: () => {
        setMode("default");
        setLabel("");
      },
    }),
    [label, mode],
  );
}

export type CursorController = ReturnType<typeof useCursorMode>;

export function useCursorFollower(
  enabled: boolean,
  mode: CursorMode,
  label: string,
) {
  const cursorRef = useRef<HTMLDivElement | null>(null);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (!enabled || reducedMotion) {
      return;
    }

    let targetX = window.innerWidth / 2;
    let targetY = window.innerHeight / 2;
    let currentX = targetX;
    let currentY = targetY;
    let raf = 0;

    const move = (event: PointerEvent) => {
      targetX = event.clientX;
      targetY = event.clientY;
    };

    const tick = () => {
      currentX += (targetX - currentX) * 0.18;
      currentY += (targetY - currentY) * 0.18;
      cursorRef.current?.style.setProperty("--cursor-x", `${currentX}px`);
      cursorRef.current?.style.setProperty("--cursor-y", `${currentY}px`);
      raf = window.requestAnimationFrame(tick);
    };

    window.addEventListener("pointermove", move, { passive: true });
    raf = window.requestAnimationFrame(tick);

    window.__coffeeAtlasDebug = {
      ...window.__coffeeAtlasDebug,
      pointerCapability: "fine",
    };

    return () => {
      window.removeEventListener("pointermove", move);
      window.cancelAnimationFrame(raf);
    };
  }, [enabled, reducedMotion]);

  useEffect(() => {
    if (!enabled || reducedMotion || !cursorRef.current) {
      return;
    }

    animate(cursorRef.current, {
      scale: mode === "default" ? 1 : mode === "category" ? 1.8 : 1.45,
      opacity: 1,
      duration: 180,
      ease: "outCubic",
    });
  }, [enabled, mode, reducedMotion]);

  return { cursorRef, reducedMotion, label };
}

import { animate } from "animejs";
import { useEffect, useRef } from "react";
import { useLocation } from "react-router";
import { useReducedMotion } from "./reducedMotion";

export function useRouteTransition() {
  const location = useLocation();
  const layerRef = useRef<HTMLDivElement | null>(null);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (!layerRef.current) {
      return;
    }

    animate(layerRef.current, {
      opacity: reducedMotion ? [0.16, 0] : [0.48, 0],
      scaleX: reducedMotion ? [1, 1] : [0, 1, 1],
      transformOrigin: ["0% 50%", "0% 50%", "100% 50%"],
      duration: reducedMotion ? 160 : 520,
      ease: "outExpo",
    });
  }, [location.key, reducedMotion]);

  return layerRef;
}

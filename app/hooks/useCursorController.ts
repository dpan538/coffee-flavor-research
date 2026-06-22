import { useOutletContext } from "react-router";
import type { CursorController } from "@/motion/cursorEffects";

export function useCursorController() {
  return useOutletContext<CursorController>();
}

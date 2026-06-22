export {};

declare global {
  interface Window {
    __coffeeAtlasDebug?: {
      animeScopes?: number;
      scrollObservers?: number;
      reducedMotion?: boolean;
      pointerCapability?: "fine" | "coarse" | "unknown";
      cursorMode?: string;
    };
  }
}

/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />
/** commit + day of the build (vite.config.ts define) */
declare const __BUILD_ID__: string;
interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  readonly userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}
declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<
    Record<string, never>,
    Record<string, never>,
    unknown
  >;
  export default component;
}

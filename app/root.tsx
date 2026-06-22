import "@fontsource/bodoni-moda/400.css";
import "@fontsource/bodoni-moda/700.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/700.css";
import "@fontsource/noto-sans-sc/400.css";
import "@fontsource/noto-sans-sc/700.css";
import "@fontsource/noto-serif-sc/400.css";
import "@fontsource/noto-serif-sc/700.css";
import "./styles/global.css";

import {
  isRouteErrorResponse,
  Links,
  Meta,
  NavLink,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLocation,
} from "react-router";
import type { LinksFunction } from "react-router";
import { useEffect, useMemo, useRef } from "react";
import type { ReactNode } from "react";
import {
  useCursorFollower,
  useCursorMode,
  useFinePointer,
} from "@/motion/cursorEffects";
import { useReducedMotion } from "@/motion/reducedMotion";
import { useRouteTransition } from "@/motion/routeTransitions";

export const links: LinksFunction = () => [
  { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" },
  {
    rel: "preconnect",
    href: "https://game-icons.net",
  },
];

export function meta() {
  return [
    { title: "Coffee Flavor Atlas / 咖啡风味图谱" },
    {
      name: "description",
      content:
        "An experimental digital publication and sensory specimen index for bilingual coffee flavor descriptors.",
    },
  ];
}

function CursorLayer({
  mode,
  label,
}: {
  mode: ReturnType<typeof useCursorMode>["mode"];
  label: string;
}) {
  const finePointer = useFinePointer();
  const { cursorRef, reducedMotion } = useCursorFollower(
    finePointer,
    mode,
    label,
  );

  useEffect(() => {
    window.__coffeeAtlasDebug = {
      ...window.__coffeeAtlasDebug,
      reducedMotion,
      pointerCapability: finePointer ? "fine" : "coarse",
      cursorMode: mode,
    };
  }, [finePointer, mode, reducedMotion]);

  if (!finePointer || reducedMotion) {
    return null;
  }

  return (
    <div
      ref={cursorRef}
      className={`cursor-layer cursor-layer--${mode}`}
      aria-hidden="true"
    >
      <span className="cursor-layer__dot" />
      <span className="cursor-layer__label">{label || mode}</span>
    </div>
  );
}

function DevDebugPanel() {
  const reducedMotion = useReducedMotion();
  const finePointer = useFinePointer();
  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (import.meta.env.PROD || !panelRef.current) {
      return;
    }

    let raf = 0;
    const tick = () => {
      if (panelRef.current) {
        const debug = window.__coffeeAtlasDebug ?? {};
        panelRef.current.textContent = [
          `anime scopes: ${debug.animeScopes ?? 0}`,
          `scroll observers: ${debug.scrollObservers ?? 0}`,
          `reduced motion: ${reducedMotion}`,
          `pointer: ${finePointer ? "fine" : "coarse"}`,
          `cursor: ${debug.cursorMode ?? "default"}`,
        ].join(" / ");
      }
      raf = window.requestAnimationFrame(tick);
    };
    raf = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(raf);
  }, [finePointer, reducedMotion]);

  if (import.meta.env.PROD) {
    return null;
  }

  return <div ref={panelRef} className="debug-panel" aria-hidden="true" />;
}

function AppChrome() {
  const cursor = useCursorMode();
  const transitionRef = useRouteTransition();
  const location = useLocation();
  const navItems = useMemo(
    () => [
      { to: "/", label: "FIELD", zh: "词场" },
      { to: "/atlas", label: "ATLAS", zh: "索引" },
      { to: "/methodology", label: "METHOD", zh: "方法" },
    ],
    [],
  );

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content / 跳到正文
      </a>
      <header
        className="site-chrome"
        data-theme={location.pathname === "/" ? "dark" : "light"}
      >
        <NavLink
          to="/"
          className="site-mark"
          data-cursor="view"
          onPointerEnter={() => cursor.setCursor("view", "FIELD")}
          onPointerLeave={cursor.resetCursor}
        >
          <span>COFFEE FLAVOR ATLAS</span>
          <span>咖啡风味图谱</span>
        </NavLink>
        <nav aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              data-cursor="open"
              onPointerEnter={() => cursor.setCursor("open", item.label)}
              onPointerLeave={cursor.resetCursor}
            >
              <span>{item.label}</span>
              <span>{item.zh}</span>
            </NavLink>
          ))}
        </nav>
      </header>
      <div
        className="route-transition-layer"
        ref={transitionRef}
        aria-hidden="true"
      />
      <CursorLayer mode={cursor.mode} label={cursor.label} />
      <main id="main-content">
        <Outlet context={cursor} />
      </main>
      <footer className="publication-footer">
        <span>v0.2 editorial field migration</span>
        <span>project-curated draft sensory association profiles</span>
        <span>not chemical indicators / not fixed cupping results</span>
      </footer>
      <DevDebugPanel />
    </>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function Root() {
  return <AppChrome />;
}

export function ErrorBoundary({ error }: { error: unknown }) {
  const message = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : error instanceof Error
      ? error.message
      : "Unknown route error";

  return (
    <section className="route-error">
      <p className="meta-label">ROUTE ERROR</p>
      <h1>{message}</h1>
      <NavLink to="/">Return to field / 返回词场</NavLink>
    </section>
  );
}

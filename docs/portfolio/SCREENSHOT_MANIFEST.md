# Screenshot manifest

These screenshots were captured from the built flavorwords PWA (`apps/pwa/dist`
served by `vite preview`) with reduced motion enabled. They show the real
current interface; no model output or restricted source content is present.
Routes in parentheses are on-screen states of the single-page app, reached by
the listed action.

<!-- prettier-ignore -->
| File | Route | Viewport | Capture date | Browser | Commit SHA | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `pwa-mobile-home.png` | `/` | `390x844` | 2026-09-13 | Chromium 149.0.7827.55 | `a3337f58324c89b6df90a4a1009f48b220ded349` | `5fb2ed6ec8a180b29fe6a4aedc553f77e287f2ff4e11335944273f69da11b044` |
| `pwa-mobile-card.png` | `/ (flow → flavor card)` | `390x844` | 2026-09-13 | Chromium 149.0.7827.55 | `a3337f58324c89b6df90a4a1009f48b220ded349` | `4f02532611bfb03e82ae4ae3f3b959e93ba9bfe0ecd4088667e1ea0c3f1c4f93` |
| `pwa-desktop-home.png` | `/` | `1440x900` | 2026-09-13 | Chromium 149.0.7827.55 | `a3337f58324c89b6df90a4a1009f48b220ded349` | `6f9ec0c84921b4a3e256f0573ec179b15bc876cef12229af0befd8efc3f3da54` |
| `pwa-desktop-context.png` | `/ (start → context card)` | `1440x900` | 2026-09-13 | Chromium 149.0.7827.55 | `a3337f58324c89b6df90a4a1009f48b220ded349` | `06be35c7be47c16f1e2231b3094dbef78852efb9cf4472ac363c1bf41cb1758a` |
| `pwa-desktop-about-sources.png` | `/ (about → sources poster)` | `1440x900` | 2026-09-13 | Chromium 149.0.7827.55 | `a3337f58324c89b6df90a4a1009f48b220ded349` | `541d4421c4a0f6d59e3638cead15b1b4034a7789e393acdb5e76c94bc667ffcc` |
| `pwa-desktop-about-profiles.png` | `/ (about → profile network)` | `1440x900` | 2026-09-13 | Chromium 149.0.7827.55 | `a3337f58324c89b6df90a4a1009f48b220ded349` | `a3c4222829eadf9469c4281f738e865d63da3b631e64f030e1708a13245787b4` |

## Reproduce

```bash
npm run pwa:build
npx vite preview --config apps/pwa/vite.config.ts --host 127.0.0.1 --port 4173 --strictPort
# In another shell:
npm run portfolio:screenshots
npm run public:screenshots:check
```

The file hashes will change if browser rendering, fonts, viewport, application
code, or browser version changes. Regenerated captures must be reviewed and
committed with their new manifest.

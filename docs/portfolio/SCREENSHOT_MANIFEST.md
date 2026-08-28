# Screenshot manifest

These screenshots were captured from the production frontend preview with
reduced motion enabled. They show the real current interface; no model output or
restricted source content is present.

| File                            | Route                                                      | Viewport    | Capture date | Browser                 | Commit SHA                                 | SHA-256                                                            |
| ------------------------------- | ---------------------------------------------------------- | ----------- | ------------ | ----------------------- | ------------------------------------------ | ------------------------------------------------------------------ |
| `desktop-home.png`              | `/`                                                        | `1440x1100` | 2026-08-28   | Chromium 151.0.7922.175 | `dd4e9eb29eb9c3ae887cb07bc8e5f297c3ceb028` | `6c5385751be39ce9d07c27ef13b88fb9a6af2a72e4f99f66df1b2a04ad7b86fe` |
| `mobile-home.png`               | `/`                                                        | `390x900`   | 2026-08-28   | Chromium 151.0.7922.175 | `dd4e9eb29eb9c3ae887cb07bc8e5f297c3ceb028` | `0e202b26b91fb3d33025ff5fc0bdd6fa102b50a0e89543c8f381c83e9677ff4f` |
| `desktop-atlas-interaction.png` | `/atlas?view=index&q=cacao&compare=jasmine,dark-chocolate` | `1440x1100` | 2026-08-28   | Chromium 151.0.7922.175 | `dd4e9eb29eb9c3ae887cb07bc8e5f297c3ceb028` | `aba2769f003dc1440ddd4981a86bd7a5daa4ff35a5c86d4c21d7c00b693e21ae` |
| `desktop-project-status.png`    | `/methodology#project-status`                              | `1440x1100` | 2026-08-28   | Chromium 151.0.7922.175 | `dd4e9eb29eb9c3ae887cb07bc8e5f297c3ceb028` | `d8c3818655bd51815690f7cea615b268629218e17a436b232a292c165cf7f842` |

## Reproduce

```bash
npm run build
npm run preview -- --host 127.0.0.1 --port 4321
# In another shell:
npm run portfolio:screenshots
npm run public:screenshots:check
```

The file hashes will change if browser rendering, fonts, viewport, application
code, or browser version changes. Regenerated captures must be reviewed and
committed with their new manifest.

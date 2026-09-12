# Vercel 部署填写表（flavorwords PWA）

适用页面：vercel.com → Add New → Project → Import `dpan538/coffee-flavor-research`。仓库根目录的 `vercel.json` 已经写死了框架、安装、构建与输出目录，Vercel 以 `vercel.json` 为准；表单按下面填写是为了让面板显示与仓库一致。

## 一、New Project 表单

| 字段                                  | 填写值              | 说明                                                                                                                                |
| ------------------------------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Vercel Team                           | dpan538's projects  | 现有团队即可                                                                                                                        |
| Project Name                          | `flavorwords`       | 也可保留 `coffee-flavor-research`；只影响 `*.vercel.app` 预览域名                                                                   |
| Application Preset / Framework Preset | **Other**           | 页面会自动猜成 React Router（因为根目录有 `react-router.config.ts`），必须改成 Other；`vercel.json` 里 `"framework": null` 与之对应 |
| Root Directory                        | `./`                | 保持默认。不要填 `apps/pwa`：`package.json` 与 `package-lock.json` 在仓库根目录                                                     |
| Build Command                         | `npm run pwa:build` | 打开 Override 开关后填写                                                                                                            |
| Output Directory                      | `apps/pwa/dist`     | 打开 Override 开关后填写                                                                                                            |
| Install Command                       | `npm ci`            | 打开 Override 开关后填写                                                                                                            |
| Development Command                   | 留空                | 不用                                                                                                                                |
| Environment Variables                 | 不添加              | 构建不读取任何环境变量。`COFFEE_KB_ALLOW_DATABASE_DROP` 只属于本地数据库回放，不要放到 Vercel                                       |

填完点 Deploy。首次构建会先 clone 仓库，仓库里有大量 TSV 数据，clone 可能需要一两分钟。

## 二、部署后的 Project Settings

| 位置                                              | 设置              | 值                                                                                                          |
| ------------------------------------------------- | ----------------- | ----------------------------------------------------------------------------------------------------------- |
| Settings → General → Node.js Version              | Node.js Version   | **22.x**（`package.json` 的 `engines.node` 已写 `22.x`，Vercel 会据此选择）                                 |
| Settings → General → Build & Development Settings | Framework Preset  | Other                                                                                                       |
| 同上                                              | Build Command     | `npm run pwa:build`                                                                                         |
| 同上                                              | Output Directory  | `apps/pwa/dist`                                                                                             |
| 同上                                              | Install Command   | `npm ci`                                                                                                    |
| Settings → Git                                    | Production Branch | `main`                                                                                                      |
| Settings → Git → Git Large File Storage           | Git LFS           | **关闭**（默认）。两份 77K / 83K 来源账本在 LFS 里，PWA 构建不读取它们，关闭可省下每次 clone 约 211 MB 下载 |
| Settings → Git → Ignored Build Step               | 留默认            | 每次推到 main 都会重新部署                                                                                  |
| Settings → Domains                                | 添加域名          | `flavorwords.com`（主域）与 `www.flavorwords.com`（重定向到主域）                                           |

域名 DNS（在域名注册商处）：

| 记录  | 名称  | 值                     |
| ----- | ----- | ---------------------- |
| A     | `@`   | `76.76.21.21`          |
| CNAME | `www` | `cname.vercel-dns.com` |

Vercel 的 Domains 页面会显示它当前要求的记录，以页面显示为准。

## 三、构建产物与 vercel.json 的对应关系

- 构建脚本：`vite build --config apps/pwa/vite.config.ts`，输出到 `apps/pwa/dist`（`index.html`、`assets/`、`fonts/`、`icons/`、`sw.js`、`workbox-*.js`、`manifest.webmanifest`、`robots.txt`、`sitemap.xml`、`humans.txt`、`llms.txt`）。
- `vercel.json` 的 headers：`/sw.js` 不缓存（Service Worker 更新即时生效）；`/manifest.webmanifest` 的 Content-Type 为 `application/manifest+json`；`/fonts/*` 与 `/assets/*` 一年不可变缓存（文件名带哈希）。
- `cleanUrls: true`：`/index.html` 会重定向到 `/`。应用只有一个页面，没有客户端路由，不需要 rewrites。

## 四、部署后的检查清单

1. 打开 `https://<project>.vercel.app/`：首页出现 slogan、开始 / 关于两个按钮；中英文切换正常。
2. `/manifest.webmanifest` 返回 JSON，响应头 `content-type: application/manifest+json`。
3. `/sw.js` 响应头 `cache-control: no-cache, no-store, must-revalidate`。
4. `/robots.txt`、`/sitemap.xml`、`/llms.txt`、`/humans.txt` 都能打开；`sitemap.xml` 与 `index.html` 里的 canonical 指向正式域名。
5. 手机浏览器「添加到主屏幕」可安装；断网后再打开仍能进入首页（Service Worker 预缓存）。
6. 走一遍 `docs/product/Q6_TRIGGER_TEST_SET.md` 的第 6 条序列，确认 Q6 弹层与「更新风味卡」在线上构建里正常。

## 五、GitHub 侧

- 分支 `research/round2-capture` 领先 `origin/main` 的提交全部是快进（origin/main 是它的祖先）。推送命令（在 worktree 里执行）：

```bash
git push origin research/round2-capture:main
```

- 两份来源账本 `db/data/current/CLEANED_83K_SOURCE_ASSERTION_LEDGER.tsv`（109.9 MB）与 `CLEANED_77K_SOURCE_ASSERTION_LEDGER.tsv`（100.8 MB）超过或逼近 GitHub 100 MiB 的单文件硬限制，已迁入 Git LFS；`git push` 时 LFS 的 pre-push 钩子会先上传这两个对象，再推提交。
- CI 里读取这两份账本的两个 workflow（`ci.yml` 的 `database-artifacts`、`historical-replay.yml`）已改为 `actions/checkout` 加 `lfs: true`；每次运行下载约 211 MB LFS 带宽。`checks`（网页门禁）与 `database-current` 不读取它们，保持普通 checkout。

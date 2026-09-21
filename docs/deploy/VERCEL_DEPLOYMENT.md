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

| 位置                                              | 设置              | 值                                                                                     |
| ------------------------------------------------- | ----------------- | -------------------------------------------------------------------------------------- |
| Settings → General → Node.js Version              | Node.js Version   | **22.x**（`package.json` 的 `engines.node` 已写 `22.x`，Vercel 会据此选择）            |
| Settings → General → Build & Development Settings | Framework Preset  | Other                                                                                  |
| 同上                                              | Build Command     | `npm run pwa:build`                                                                    |
| 同上                                              | Output Directory  | `apps/pwa/dist`                                                                        |
| 同上                                              | Install Command   | `npm ci`                                                                               |
| Settings → Git                                    | Production Branch | `main`                                                                                 |
| Settings → Git → Git Large File Storage           | Git LFS           | **关闭**（默认）。仓库自 2026-09-20 起不再使用 Git LFS，PWA 构建也不读取那两份来源账本 |
| Settings → Git → Ignored Build Step               | 留默认            | 每次推到 main 都会重新部署                                                             |
| Settings → Domains                                | 添加域名          | `flavorwords.com`（主域）与 `www.flavorwords.com`（重定向到主域）                      |

域名 DNS（在域名注册商处）：

| 记录  | 名称  | 值                     |
| ----- | ----- | ---------------------- |
| A     | `@`   | `76.76.21.21`          |
| CNAME | `www` | `cname.vercel-dns.com` |

Vercel 的 Domains 页面会显示它当前要求的记录，以页面显示为准。

## 三、构建产物与 vercel.json 的对应关系

- 构建脚本：`vite build --config apps/pwa/vite.config.ts`，输出到 `apps/pwa/dist`（`index.html`、`assets/`、`fonts/`、`icons/`、`sw.js`、`workbox-*.js`、`manifest.webmanifest`、`robots.txt`、`sitemap.xml`、`humans.txt`、`llms.txt`、`zh.html`、`en.html`、`404.html`、`favicon.ico`、`og.png`）。
- `vercel.json` 的 headers：`/sw.js` 不缓存（Service Worker 更新即时生效）；`/manifest.webmanifest` 的 Content-Type 为 `application/manifest+json`；`/fonts/*` 与 `/assets/*` 一年不可变缓存（文件名带哈希）。
- `cleanUrls: true`：`/index.html` 会重定向到 `/`，`zh.html` 与 `en.html` 以 `/zh`、`/en` 提供。应用只有一个页面，没有客户端路由，不需要 rewrites；`redirects` 里只有 `/about` → `/en`。

## 四、部署后的检查清单

1. 打开 `https://<project>.vercel.app/`：首页出现 slogan、开始 / 关于两个按钮；中英文切换正常。
2. `/manifest.webmanifest` 返回 JSON，响应头 `content-type: application/manifest+json`。
3. `/sw.js` 响应头 `cache-control: no-cache, no-store, must-revalidate`。
4. `/robots.txt`、`/sitemap.xml`、`/llms.txt`、`/humans.txt` 都能打开；`sitemap.xml` 与 `index.html` 里的 canonical 指向正式域名。
   `/zh` 与 `/en` 是不需要 JavaScript 的分语言静态页（`<html lang>` 分别为 zh-CN 与 en，响应头带 `content-language`），`/about` 转到 `/en`，`/favicon.ico` 返回图标，不存在的地址返回品牌化的 404 页。
   这一层每次改动并部署之后：在 Google Search Console 提交 `https://flavorwords.com/sitemap.xml`，对 `/`、`/zh`、`/en` 逐个「请求编入索引」（必须在部署之后——地址在线上还是 404 时请求会被拒绝）；Bing Webmaster Tools 可直接从 Search Console 导入已验证的站点；百度搜索资源平台需要 owner 自己的账号，验证码放进 `apps/pwa/index.html`。
5. 手机浏览器「添加到主屏幕」可安装；断网后再打开仍能进入首页（Service Worker 预缓存）。
6. 走一遍 `docs/product/Q6_TRIGGER_TEST_SET.md` 的第 6 条序列，确认 Q6 弹层与「更新风味卡」在线上构建里正常。

## 五、GitHub 侧

- 分支 `research/round2-capture` 领先 `origin/main` 的提交全部是快进（origin/main 是它的祖先）。推送命令（在 worktree 里执行）：

```bash
git push origin research/round2-capture:main
```

- 两份来源账本 `db/data/current/CLEANED_83K_SOURCE_ASSERTION_LEDGER.tsv`（109.9 MB）与 `CLEANED_77K_SOURCE_ASSERTION_LEDGER.tsv`（100.8 MB）超过或逼近 GitHub 100 MiB 的单文件硬限制。2026-09-13 起它们放在 Git LFS；2026-09-20 起改为以 xz 压缩包（5–6 MB）存放在普通 git 里，由 `db/scripts/materialize-large-ledgers.py` 写回原文件并校验 SHA-256（压缩包与清单在 `db/data/large-ledger-archives/`；原文件已加入 `.gitignore`）。原因：带 LFS 的 CI 检出每次下载约 211 MB，月度 LFS 流量用完之后数据库作业连检出都无法完成；owner 要求不再依赖 LFS。
- `ci.yml` 的 `database-artifacts` 与 `historical-replay.yml` 改回普通 checkout，随后运行上述脚本；本机的 `db/scripts/ci-verify.sh` 同样先运行它。新克隆仓库后如果要在本机跑数据库相关脚本，先执行一次 `python3 db/scripts/materialize-large-ledgers.py`。账本内容如有合法变更，用 `--pack` 重新生成压缩包与清单。

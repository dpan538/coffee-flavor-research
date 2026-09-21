// The static pages of the machine-readable layer: public/zh.html, public/en.html and public/404.html.
// One language, one address (owner, 2026-09-21: both languages have to be detectable): a search engine cannot tell two
// languages apart on one URL, so /zh is the Chinese page, /en the English one, and / — the app, which follows the
// device language — is their x-default. The pages need no JavaScript, carry the brand (wordmark, the five shapes,
// the app's own typefaces) and say the same things as index.html, llms.txt and the README: keep the facts in step.
// Run: node apps/pwa/scripts/build-static-pages.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { format } from "prettier";

const pub = join(dirname(fileURLToPath(import.meta.url)), "..", "public");
// what this script writes has to pass `prettier . --check` (the web gate), so every page is formatted on the way out
const write = async (file, html) =>
  writeFileSync(join(pub, file), await format(html, { parser: "html" }));
const UPDATED = "2026-09-21";
const SITE = "https://flavorwords.com";
const icon = readFileSync(join(pub, "icons", "icon.svg"), "utf8");
const paths = [...icon.matchAll(/<path d="([^"]+)" fill="([^"]+)"\/>/g)];
// the wordmark alone (no white square), for the pages here and as the brand's logo in the structured data
writeFileSync(
  join(pub, "icons", "wordmark.svg"),
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="78 170 360 170" width="720" height="340" role="img" aria-label="flavorwords">${paths.map((m) => `<path d="${m[1]}" fill="${m[2]}"/>`).join("")}</svg>\n`,
);
// Safari's pinned tab takes one colour from the page and the shape from here: the same drawing, all black, no ground
writeFileSync(
  join(pub, "icons", "mask-icon.svg"),
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="69 66 380 380">${paths.map((m) => `<path d="${m[1]}" fill="#000"/>`).join("")}</svg>\n`,
);
const wordmark = `<img class="mark" src="/icons/wordmark.svg" alt="flavorwords" width="184" height="87" />`;
const shapes = `<div class="shapes" aria-hidden="true">
  <svg viewBox="0 0 120 120"><path d="M0 120a60 60 0 0 1 120 0z" fill="#7268C9"/></svg>
  <svg viewBox="0 0 120 120"><path d="M60 8 116 112H4z" fill="#E4724B"/></svg>
  <svg viewBox="0 0 120 120"><circle cx="60" cy="60" r="56" fill="#2EC27E"/></svg>
  <svg viewBox="0 0 120 120"><path d="M4 116V4a112 112 0 0 1 112 112z" fill="#FFB300"/></svg>
  <svg viewBox="0 0 120 120"><path d="M60 4 116 60 60 116 4 60z" fill="#1F3B5C"/></svg>
</div>`;

const css = `
@font-face { font-family: "Stack Sans Text"; src: url("/fonts/StackSansText-Variable.woff2") format("woff2"); font-weight: 200 700; font-display: swap; }
@font-face { font-family: "MiSans"; src: url("/fonts/MiSans-Regular.woff2") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "MiSans"; src: url("/fonts/MiSans-Demibold.woff2") format("woff2"); font-weight: 600; font-display: swap; }
:root { --ink: #1e1c1a; --muted: #6b6660; --violet: #7268c9; --paper: #fff; --cream: #f3eee2; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink); line-height: 1.7; -webkit-text-size-adjust: 100%;
  font-family: "Stack Sans Text", "MiSans", system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; }
main { max-width: 44rem; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }
.top { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
.mark { width: 11.5rem; height: auto; display: block; }
.lang { font-size: 0.95rem; white-space: nowrap; padding-top: 0.4rem; }
.shapes { display: flex; gap: 0.6rem; margin: 1.6rem 0 0; }
.shapes svg { width: 2.1rem; height: 2.1rem; }
h1 { font-size: 2rem; line-height: 1.2; margin: 1.6rem 0 0.4rem; letter-spacing: -0.01em; }
.lede { font-size: 1.15rem; margin: 0 0 1.2rem; }
h2 { font-size: 1.3rem; margin: 2.6rem 0 0.5rem; }
a { color: var(--violet); }
.open { display: inline-block; margin: 0.4rem 0 0; padding: 0.8rem 1.4rem; border-radius: 16px; background: var(--ink); color: #fff; text-decoration: none; font-weight: 600; }
.note { background: var(--cream); border-radius: 18px; padding: 1rem 1.2rem; margin: 1.6rem 0; }
li { margin: 0.35rem 0; }
footer { margin-top: 3.5rem; padding-top: 1.2rem; border-top: 1px solid #e4dfd3; color: var(--muted); font-size: 0.92rem; }
`;

const pages = {
  zh: {
    file: "zh.html",
    lang: "zh-CN",
    path: "/zh",
    ogLocale: "zh_CN",
    ogAlt: "en_US",
    title: "flavorwords — 咖啡风味描述工具：把这一杯咖啡说出来",
    description:
      "flavorwords 是一款免费的咖啡品鉴网页应用：回答几个关于这一杯咖啡的简单问题，选出贴近感受的风味词，得到一张自己的风味卡。基于 9,128 条专业评审的咖啡记录，可离线使用，中英双语。",
    other: `<a href="/en" hreflang="en" lang="en">English</a>`,
    open: ["/?lang=zh-CN", "打开 flavorwords"],
    body: `
<h1>把这一杯咖啡说出来</h1>
<p class="lede">风味，自有表达。flavorwords 是一款免费的<strong>咖啡品鉴</strong>网页应用。</p>
<p>喝得出两杯咖啡不一样，却说不出哪里不一样——像柑橘，像可可，或是某种熟悉却一时叫不出名字的味道。flavorwords 用几个简单问题，帮你找到贴近感受的风味词，组成这一杯咖啡的风味卡。</p>
<p>{OPEN}</p>
<div class="note">flavorwords <strong>不是</strong>学英语或背单词的网站，不是食品文案工具，也不是香精香料网站。这里的“词”是葡萄柚、茉莉花、黑巧克力、柏木这样的咖啡风味词。它描述你面前的这一杯，不测定、不评分、不识别、也不推荐咖啡。</div>
<h2>怎么用</h2>
<ol>
<li><strong>说明这一杯是怎么做的。</strong>冲煮方式、烘焙度、豆种（单一或至多三种拼配）、处理法，以及已知的产地。它给出一个来自评审资料的起点，不是结论。</li>
<li><strong>回答至多六个简单问题。</strong>酸与水果、香气主调、甜、口感，再按你的回答追问至多两题（具体是哪种柑橘或莓果、苦感、余韵、香气有多明显、整体印象）。每题四个选项，最前面两题五个；“说不上来”是正式选项，不改变任何东西。选项随咖啡种类变化，任何选项都不回指前面的题目。</li>
<li><strong>从八个具体的风味词里选出三到五个。</strong>卡片先听你的：你选中的词领头，其次是你指到的那一类；只有你没说的地方才参考资料。</li>
<li><strong>回答互相矛盾时多问一步。</strong>你在这一步选中的词一定出现在卡上，你自己勾选的词也会保留。</li>
<li><strong>得到一张风味卡。</strong>语境、你确认的词、评价行（醇厚度、烘烤苦感、香气、余韵）、十六组参考风味里最接近的一组，以及每句话的来源；可以导出为图片。任何一题都可以从进度条点回去修改，其余答案保留并重新计算。</li>
</ol>
<p>中文与英文共用同一套数据；可离线使用，可添加到 iOS、Android、HarmonyOS 的主屏幕；没有账号，没有服务器端状态，你的回答不会离开设备；运行时不使用生成式模型。</p>
<h2>数据从哪来</h2>
<p>八类专业评审来源的 9,128 条咖啡记录与 83,031 条风味描述（清洗后 77,637 条），其中包括 CoffeeReview 的评审与 Cup of Excellence 的评审团记录；归一为 94 个规范感官概念，投影到 12 个风味维度（酸质、甜感、醇厚度、花香、果香、坚果巧克力、发酵酒香、烘烤苦感、辛香、草本茶感、木质泥土、瑕疵），离线聚类成 16 组参考风味；应用里共有 101 个中英文风味词。不保存任何来源原文，不点名任何商业咖啡。运行时只在浏览器里做确定性的向量匹配，每个结果都能追溯到一行数据或一条规则。</p>
<h2>谁做的</h2>
<p>研究、设计与开发：潘岱（Dai Pan），2026 年 6–9 月，个人主导，AI 辅助实现。产品经过专家访谈、杯测研究、两轮问卷与两轮上线前品鉴测试的调整；尚未用普通消费者样本验证。</p>
<p><a href="https://github.com/dpan538/coffee-flavor-research">GitHub 上的源码、数据说明与方法</a> · <a href="/llms.txt">给语言模型的纯文本摘要</a></p>`,
    footer: `最后更新 ${UPDATED} · <a href="/">flavorwords.com</a> · <a href="/en" hreflang="en" lang="en">English</a>`,
  },
  en: {
    file: "en.html",
    lang: "en",
    path: "/en",
    ogLocale: "en_US",
    ogAlt: "zh_CN",
    title: "flavorwords — a coffee-tasting app: put this cup into words",
    description:
      "flavorwords is a free coffee-tasting web app: answer a few plain questions about the cup of coffee you are drinking, keep the flavor words that fit, and get a flavor card in your own words. Built on 9,128 professionally reviewed coffees. Works offline, in English and Chinese.",
    other: `<a href="/zh" hreflang="zh-CN" lang="zh-CN">中文</a>`,
    open: ["/?lang=en", "Open flavorwords"],
    body: `
<h1>Put this cup of coffee into words</h1>
<p class="lede">Every taste has its own vocabulary. flavorwords is a free <strong>coffee-tasting</strong> web app.</p>
<p>Most people can tell that two coffees taste different but not say how. flavorwords asks a few plain questions about the cup in front of you and helps you find flavor words that fit — grapefruit, jasmine, dark chocolate, cypress — then puts them on a flavor card.</p>
<p>{OPEN}</p>
<div class="note">flavorwords is <strong>not</strong> a language-learning or vocabulary-memorising site, not a food-copywriting tool and not a flavoring site. The “words” are coffee flavor words. It describes the cup in front of you; it does not measure, grade, identify or recommend coffee.</div>
<h2>How it works</h2>
<ol>
<li><strong>Say how the cup was made.</strong> Brewing method, roast, variety (single or a blend of up to three), process and, if known, origin. This gives a starting point from the review corpus, never a verdict.</li>
<li><strong>Answer up to six plain questions.</strong> Acidity and fruit, the main aroma, sweetness, mouthfeel, then at most two follow-ups chosen by your answers (which citrus or berry exactly, bitterness, aftertaste, how clear the aroma is, the overall impression). Four options a question, five for the first two; “I can’t say” is a regular option and changes nothing. The options differ by kind of coffee and none refers back to an earlier question.</li>
<li><strong>Keep three to five of eight concrete flavor words.</strong> The card follows you first: the word you chose leads, then the kind you pointed to; the data speaks only where you said nothing.</li>
<li><strong>One more step when your answers conflict.</strong> Whatever you tick there appears on the card, and the words you picked yourself are kept.</li>
<li><strong>Get a flavor card.</strong> The context, the words you confirmed, evaluation rows (body, roast and bitterness, aroma, aftertaste), the nearest of sixteen reference profiles, and where each sentence comes from. Export it as an image. Any question can be reopened from the progress bar; the other answers are kept and recomputed.</li>
</ol>
<p>English and Chinese share one data backend. It works offline and installs to the home screen on iOS, Android and HarmonyOS. No account, no server-side state, nothing you answer leaves your device, and no generative model runs.</p>
<h2>Where the data comes from</h2>
<p>9,128 coffee records and 83,031 flavor descriptions (77,637 after cleaning) from eight professional review sources — CoffeeReview editorial reviews, Cup of Excellence juries, two Q-grader datasets and four smaller panels — normalised to 94 sensory concepts on 12 flavor dimensions (acidity, sweetness, body, floral, fruity, nutty and chocolate, fermented and winey, roast and bitter, spice, herbal and green, woody and earthy, defect) and clustered offline into 16 reference profiles; the app carries 101 flavor words in English and Chinese. No source text is stored and no commercial coffee is named. At run time the app does deterministic vector matching in the browser; every output is traceable to a row or a rule.</p>
<h2>Who made it</h2>
<p>Research, design and development: Dai Pan (潘岱), June–September 2026, individually led with AI-assisted implementation. Expert interviews, a cupping study, two questionnaire rounds and two pre-launch tasting tests shaped the product; it has not been validated with a general-audience sample.</p>
<p><a href="https://github.com/dpan538/coffee-flavor-research">Source, data guide and method on GitHub</a> · <a href="/llms.txt">plain-text summary for language models</a></p>`,
    footer: `Last updated ${UPDATED} · <a href="/">flavorwords.com</a> · <a href="/zh" hreflang="zh-CN" lang="zh-CN">中文</a>`,
  },
};

const head = (p) => `<!doctype html>
<html lang="${p.lang}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <!-- generated by apps/pwa/scripts/build-static-pages.mjs — edit the script, not this file -->
    <title>${p.title}</title>
    <meta name="description" content="${p.description}" />
    <meta name="author" content="Dai Pan (潘岱)" />
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
    <meta http-equiv="content-language" content="${p.lang}" />
    <meta name="theme-color" content="#ffffff" />
    <meta name="format-detection" content="telephone=no" />
    <meta name="applicable-device" content="pc,mobile" />
    <meta http-equiv="Cache-Control" content="no-transform" />
    <meta http-equiv="Cache-Control" content="no-siteapp" />
    <meta name="renderer" content="webkit" />
    <link rel="canonical" href="${SITE}${p.path}" />
    <link rel="alternate" hreflang="zh-CN" href="${SITE}/zh" />
    <link rel="alternate" hreflang="en" href="${SITE}/en" />
    <link rel="alternate" hreflang="x-default" href="${SITE}/" />
    <link rel="alternate" type="text/plain" href="/llms.txt" title="plain-text summary for language models" />
    <link rel="icon" href="/favicon.ico" sizes="32x32" />
    <link rel="icon" type="image/svg+xml" href="/icons/icon.svg" />
    <link rel="apple-touch-icon" sizes="180x180" href="/icons/apple-touch-icon.png" />
    <link rel="mask-icon" href="/icons/mask-icon.svg" color="#7268C9" />
    <link rel="manifest" href="/manifest.webmanifest" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="flavorwords" />
    <meta property="og:title" content="${p.title}" />
    <meta property="og:description" content="${p.description}" />
    <meta property="og:url" content="${SITE}${p.path}" />
    <meta property="og:image" content="${SITE}/og.png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:locale" content="${p.ogLocale}" />
    <meta property="og:locale:alternate" content="${p.ogAlt}" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="${p.title}" />
    <meta name="twitter:description" content="${p.description}" />
    <meta name="twitter:image" content="${SITE}/og.png" />
    <meta itemprop="name" content="${p.title}" />
    <meta itemprop="description" content="${p.description}" />
    <meta itemprop="image" content="${SITE}/og.png" />
    <script type="application/ld+json">
${JSON.stringify({ "@context": "https://schema.org", "@type": "AboutPage", "@id": `${SITE}${p.path}`, url: `${SITE}${p.path}`, name: p.title, description: p.description, inLanguage: p.lang, dateModified: UPDATED, primaryImageOfPage: `${SITE}/og.png`, isPartOf: { "@id": `${SITE}/#website` }, about: { "@id": `${SITE}/#app` }, author: { "@type": "Person", name: "Dai Pan", alternateName: "潘岱", url: "https://github.com/dpan538" } }, null, 2)}
    </script>
    <style>${css}</style>
  </head>`;

for (const p of Object.values(pages)) {
  const open = `<a class="open" href="${p.open[0]}">${p.open[1]} →</a>`;
  await write(
    p.file,
    `${head(p)}
  <body>
    <main>
      <div class="top"><a href="/" aria-label="flavorwords">${wordmark}</a><span class="lang">${p.other}</span></div>
      ${shapes}
${p.body.replace("{OPEN}", open)}
      <p>${open}</p>
      <footer>${p.footer}</footer>
    </main>
  </body>
</html>
`,
  );
  console.log("wrote", p.file);
}

// a branded page for addresses that do not exist (Vercel serves /404.html with status 404)
await write(
  "404.html",
  `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <!-- generated by apps/pwa/scripts/build-static-pages.mjs -->
    <title>Page not found · 没有这个页面 — flavorwords</title>
    <meta name="robots" content="noindex" />
    <link rel="icon" href="/favicon.ico" sizes="32x32" />
    <link rel="icon" type="image/svg+xml" href="/icons/icon.svg" />
    <style>${css}</style>
  </head>
  <body>
    <main>
      <div class="top"><a href="/" aria-label="flavorwords">${wordmark}</a></div>
      ${shapes}
      <h1>Page not found · <span lang="zh-CN">没有这个页面</span></h1>
      <p class="lede">flavorwords is a free coffee-tasting web app. <span lang="zh-CN">flavorwords 是一款免费的咖啡品鉴网页应用。</span></p>
      <p><a class="open" href="/">Open flavorwords · <span lang="zh-CN">打开应用</span> →</a></p>
      <p><a href="/en">About, in English</a> · <a href="/zh" lang="zh-CN">中文介绍</a></p>
    </main>
  </body>
</html>
`,
);
console.log("wrote 404.html");

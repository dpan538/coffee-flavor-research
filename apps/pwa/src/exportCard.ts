/**
 * Export the flavor card as a 1200 × 2500 PNG — 1.2 : 2.5 (owner, 2026-09-19): a stamp. The image is the stamp itself:
 * the background is transparent and the perforated edge is cut out of it, so what the reader receives is a stamp-like
 * object. The upper part, down to the flavor words, is a faint grey-white with black type; below it is one of four of
 * the app's own colours (navy, forest, maroon, ink — drawn by the card's seed) with white type. No boxes, no section headings, nothing addressed to the reader — a shared card does not say "your".
 *
 * The layout is fixed, the same in both languages and for every cup:
 *   white part   wordmark and the row of five shapes at the top, the small print at the bottom, the flavor words
 *                centred between them. It ends at one of two fixed heights: 920 when the cup has many rows (the words
 *                flow, at most three lines), 1180 when it has six rows or fewer (the words stack one to a line);
 *   rows         anchored under the white part: evaluation rows with the reference flavor, a hairline, the cup;
 *   footer       anchored to the bottom as one group: the supplementary description, then the slogan on one line.
 * The only flexible space lies between the rows and the description; the description gives up whole sentences when a
 * cup has so many rows that it would not fit.
 *
 * Drawn with the Canvas 2D API from the same model the screen renders — no DOM capture, no dependency.
 */
import type { ResultCardModel } from "flavor-data/product-vector-v1/view";

const DIM_COLORS: Record<string, string> = {
  acidity: "#F2C24E",
  sweetness: "#F5B0C6",
  body: "#9B7B5D",
  floral: "#7268C9",
  fruity: "#EE8F70",
  nutty_chocolate: "#B97C4E",
  fermented_winey: "#8C4A4C",
  bitter_roasted: "#1E1C1A",
  spice: "#DA8A80",
  herbal_green: "#6FA85A",
  woody_earthy: "#2F7A4C",
  defect: "#7F90B8",
};
const LETTERS = ["#7C6CFF", "#FF6B4A", "#2EC27E", "#FFB300", "#2F9BFF"]; // the five letters of "taste" on the home page
const INK = "#1E1C1A";
const MUTED = "#6B6660";
const PAPER = "#F1F1EF"; // a faint grey rather than pure white, so the stamp's upper part never vanishes on a white screen (owner, 2026-09-19)
const VIOLET = "#7268C9";
// The stamp's lower part takes one of the app's own colours, drawn by the card's seed (owner, 2026-09-19) — the ones
// that carry white type (contrast 5.2 : 1 or better). On the two mid-dark grounds the letters of "taste" use the
// palette's light tones, where the home page's five would sink in.
const LIGHT_LETTERS = ["#F5B0C6", "#F2C7B5", "#7BE0C8", "#FFD54A", "#7CC4FF"]; // pink, peach, mint2, sun, sky2
const PANELS: Array<{ fill: string; letters: string[] }> = [
  { fill: "#1F3B5C", letters: LETTERS }, // navy — the final page's deep blue
  { fill: "#2F7A4C", letters: LIGHT_LETTERS }, // forest
  { fill: "#8C4A4C", letters: LIGHT_LETTERS }, // maroon
  { fill: "#1E1C1A", letters: LETTERS }, // ink
];
const ON_DEEP = "#FFFFFF";
const ON_DEEP_MUTED = "rgba(255,255,255,0.64)";
const SANS = '"MiSans", "PingFang SC", "Noto Sans SC", system-ui, sans-serif';
const DISPLAY =
  '"Stack Sans", "MiSans", "Helvetica Neue", system-ui, sans-serif';
const SERIF = '"Fraunces", Georgia, serif';
// English flavor words — and only these, all other English keeps its face: a slender, elegant serif (owner,
// 2026-09-19). Fraunces, the wordmark's family, at its display optical size with the soft and wonky forms off, set
// tight. Weight 400: at 300 the hairlines went too thin once the card is seen at phone size.
const WORDS_EN = '"Fraunces Display", "Fraunces", Georgia, serif';
const WORDS_EN_WEIGHT = 400;
let displayFace: Promise<void> | null = null;
function loadDisplayFace(): Promise<void> {
  if (typeof FontFace === "undefined" || typeof document === "undefined")
    return Promise.resolve();
  displayFace ??= (async () => {
    const face = new FontFace(
      "Fraunces Display",
      'url("/fonts/Fraunces-Variable.woff2") format("woff2")',
      {
        weight: "100 900",
        variationSettings: '"opsz" 144, "SOFT" 0, "WONK" 0',
      },
    );
    await face.load();
    document.fonts.add(face);
  })().catch(() => undefined); // without it the plain Fraunces face is used
  return displayFace;
}

const W = 1200; // 1.2 : 2.5 (owner, 2026-09-19)
const H = 2500;
const X0 = 100; // content edges
const X1 = W - X0;
// The white part ends at one of two fixed heights, the same in both languages. A cup with many rows lets the words
// flow (several to a line, at most three lines); a cup with few rows stacks them one to a line, which makes the white
// part taller and takes up the space the rows leave empty (owner, 2026-09-19).
const SPLIT_FLOW = 920;
const SPLIT_STACK = 1180;
const STACK_UP_TO_ROWS = 6;
const MARK_TOP = 96;
const ROW_PITCH = { min: 92, max: 112 }; // the rows open up a little when a cup has few of them
const ROWS_TO_NOTE = 150; // the space kept between the last row and the description
const SLOGAN_BASELINE = H - 150;

type Ctx = CanvasRenderingContext2D;
type Shape = "quarter" | "circle" | "half" | "triangle" | "diamond";
const SHAPES: Shape[] = ["quarter", "circle", "half", "triangle", "diamond"];

/** a small deterministic generator, so a card's pattern and grain are the same every time it is exported */
function generator(seedText: string) {
  let h = 2166136261;
  for (const ch of seedText) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return () => {
    h = Math.imul(h ^ (h >>> 15), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  };
}

/** one of the five simple shapes inside a size × size box at (x, y), turned by quarter turns */
function shape(
  ctx: Ctx,
  kind: Shape,
  x: number,
  y: number,
  size: number,
  color: string,
  turns = 0,
) {
  const u = size / 30;
  ctx.save();
  ctx.translate(x + size / 2, y + size / 2);
  ctx.rotate((turns * Math.PI) / 2);
  ctx.translate(-size / 2, -size / 2);
  ctx.scale(u, u);
  ctx.fillStyle = color;
  ctx.beginPath();
  if (kind === "quarter") {
    ctx.moveTo(3, 27);
    ctx.lineTo(3, 3);
    ctx.arc(3, 27, 24, -Math.PI / 2, 0);
  } else if (kind === "circle") ctx.arc(15, 15, 12, 0, Math.PI * 2);
  else if (kind === "half") {
    ctx.moveTo(3, 21);
    ctx.arc(15, 21, 12, Math.PI, 0);
  } else if (kind === "triangle") {
    ctx.moveTo(3, 27);
    ctx.lineTo(15, 3);
    ctx.lineTo(27, 27);
  } else {
    ctx.moveTo(15, 3);
    ctx.lineTo(27, 15);
    ctx.lineTo(15, 27);
    ctx.lineTo(3, 15);
  }
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

/** wrap to a width: by characters for Chinese, by words otherwise; at most `maxLines`, the last one closed with an ellipsis */
function wrap(
  ctx: Ctx,
  text: string,
  width: number,
  zh: boolean,
  maxLines: number,
): string[] {
  const units = zh ? [...text] : text.split(/(\s+)/).filter((t) => t !== "");
  const lines: string[] = [];
  let line = "";
  const noLineStart = /^[、，。；：！？）》」』…%]/;
  for (const unit of units) {
    const next = line + unit;
    if (
      line &&
      !noLineStart.test(unit) &&
      ctx.measureText(next.trimEnd()).width > width
    ) {
      // Chinese: when a comma sits in the last third of the line, break after it instead of inside a word
      const mark = zh
        ? Math.max(...["，", "、", "；", "。"].map((m) => line.lastIndexOf(m)))
        : -1;
      if (mark >= line.length * 0.66 && mark < line.length - 1) {
        lines.push(line.slice(0, mark + 1));
        line = line.slice(mark + 1) + unit;
      } else {
        lines.push(line.trimEnd());
        line = unit.trimStart();
      }
    } else line = next;
  }
  if (line.trim()) lines.push(line.trimEnd());
  if (lines.length <= maxLines) return lines;
  const kept = lines.slice(0, maxLines);
  let last = kept[maxLines - 1]!;
  while (last && ctx.measureText(`${last}…`).width > width)
    last = last.slice(0, -1);
  kept[maxLines - 1] = `${last.trimEnd()}…`;
  return kept;
}

/** Wrap a note into at most `maxLines`, dropping whole trailing sentences before resorting to an ellipsis. */
function fitSentences(
  ctx: Ctx,
  text: string,
  width: number,
  zh: boolean,
  maxLines: number,
): string[] {
  const sentences = text.match(
    zh ? /[^。！？]+[。！？]?/g : /[^.!?]+[.!?]*\s*/g,
  ) ?? [text];
  for (let n = sentences.length; n >= 1; n--) {
    const lines = wrap(
      ctx,
      sentences.slice(0, n).join("").trim(),
      width,
      zh,
      99,
    );
    if (lines.length <= maxLines) return lines;
  }
  return wrap(ctx, text, width, zh, maxLines);
}

/** a label and a value joined by a dotted leader; a value too long for the row is set smaller, never over its label */
function leaderRow(
  ctx: Ctx,
  label: string,
  value: string,
  y: number,
  labelSize: number,
  valueSize: number,
) {
  ctx.font = `400 ${labelSize}px ${SANS}`;
  ctx.fillStyle = ON_DEEP_MUTED;
  ctx.fillText(label, X0, y);
  const lw = ctx.measureText(label).width;
  ctx.font = `600 ${valueSize}px ${SANS}`;
  const room = X1 - X0 - lw - 72;
  const natural = ctx.measureText(value).width;
  if (natural > room)
    ctx.font = `600 ${Math.max(28, Math.floor((valueSize * room) / natural))}px ${SANS}`;
  ctx.fillStyle = ON_DEEP;
  const vw = ctx.measureText(value).width;
  ctx.fillText(value, X1 - vw, y);
  if (X1 - vw - 22 - (X0 + lw + 22) > 24) {
    ctx.save();
    ctx.strokeStyle = "rgba(255,255,255,0.34)";
    ctx.lineWidth = 2;
    ctx.setLineDash([2, 8]);
    ctx.beginPath();
    ctx.moveTo(X0 + lw + 22, y - 11);
    ctx.lineTo(X1 - vw - 22, y - 11);
    ctx.stroke();
    ctx.restore();
  }
}

/** the stamp's perforation: round bites cut out of the image along all four edges, corners included */
function perforate(ctx: Ctx) {
  const radius = 15;
  ctx.save();
  ctx.globalCompositeOperation = "destination-out";
  const bite = (cx: number, cy: number) => {
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fill();
  };
  const across = Math.round(W / 48);
  const down = Math.round(H / 48);
  for (let i = 0; i <= across; i++) {
    bite((W * i) / across, 0);
    bite((W * i) / across, H);
  }
  for (let i = 1; i < down; i++) {
    bite(0, (H * i) / down);
    bite(W, (H * i) / down);
  }
  ctx.restore();
}

const caps = (text: string) => text.toUpperCase().split("").join(" ");
const capitalised = (text: string, zh: boolean) =>
  zh ? text : text.charAt(0).toUpperCase() + text.slice(1);

export async function renderCardPng(
  model: ResultCardModel,
  locale: "zh-CN" | "en",
): Promise<Blob> {
  const zh = locale === "zh-CN";
  if (typeof document !== "undefined" && document.fonts) {
    await loadDisplayFace();
    await Promise.all(
      [
        `${WORDS_EN_WEIGHT} 112px ${WORDS_EN}`,
        `600 124px ${SANS}`,
        `600 48px ${SANS}`,
        `400 42px ${SANS}`,
        `700 96px ${DISPLAY}`,
        `600 72px ${SERIF}`,
      ].map((f) => document.fonts.load(f).catch(() => undefined)),
    );
  }
  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d")!;
  ctx.textBaseline = "alphabetic";
  // the serial is seeded by the cup and the confirmed dimensions, not by words: the same in both languages
  const serial = Math.floor(generator(`${model.cardSeed}#`)() * 0xffff)
    .toString(16)
    .toUpperCase()
    .padStart(4, "0");
  // … and so is the lower part's colour: one card, one colour, in either language and every time it is exported
  const panel =
    PANELS[Math.floor(generator(`${model.cardSeed}~panel`)() * PANELS.length)]!;

  const rows: Array<{ label: string; value: string }> = [
    ...model.evaluation.map((row) => ({
      label: capitalised(row.label, zh),
      value: capitalised(row.text, zh),
    })),
    ...(model.title
      ? [{ label: zh ? "参考风味" : "Reference", value: model.title }]
      : []),
  ];
  const stacked = rows.length + model.cupInfo.length <= STACK_UP_TO_ROWS;
  const split = stacked ? SPLIT_STACK : SPLIT_FLOW;
  const printBaseline = split - 80; // the small print that closes the white part

  // ── the stamp: two fields on a transparent image, the perforated edge cut out
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = PAPER;
  ctx.fillRect(0, 0, W, split);
  ctx.fillStyle = panel.fill;
  ctx.fillRect(0, split, W, H - split);
  perforate(ctx);

  // 1 · the wordmark, small, and the five shapes in the words' colours — the same row the card on screen carries
  const markWidth = 260;
  const fitted = (text: string, font: (size: number) => string) => {
    ctx.font = font(100);
    return (100 * markWidth) / ctx.measureText(text).width;
  };
  const flavorSize = fitted("FLAVOR", (n) => `700 ${n}px ${DISPLAY}`);
  const wordsSize = fitted("WORDS", (n) => `600 ${n}px ${SERIF}`);
  const markHeight = flavorSize * 0.74 + wordsSize * 0.86;
  ctx.fillStyle = INK;
  ctx.font = `700 ${flavorSize}px ${DISPLAY}`;
  ctx.fillText("FLAVOR", X0, MARK_TOP + flavorSize * 0.74);
  ctx.fillStyle = VIOLET;
  ctx.font = `600 ${wordsSize}px ${SERIF}`;
  ctx.fillText("WORDS", X0, MARK_TOP + markHeight);
  const tile = 50;
  const tileGap = 16;
  const rowWidth = SHAPES.length * tile + (SHAPES.length - 1) * tileGap;
  SHAPES.forEach((kind, i) =>
    shape(
      ctx,
      kind,
      X1 - rowWidth + i * (tile + tileGap),
      MARK_TOP + (markHeight - tile) / 2,
      tile,
      DIM_COLORS[model.pickedDimensions[i] ?? ""] ?? VIOLET,
    ),
  );

  // 2 · the words, by far the largest thing on the card, centred between the header and the small print: flowing at
  //     the largest size that keeps them to three lines, or stacked one to a line when the cup has few rows
  type Line = Array<{ text: string; x: number }>;
  const font = (size: number) =>
    zh ? `600 ${size}px ${SANS}` : `${WORDS_EN_WEIGHT} ${size}px ${WORDS_EN}`;
  const tracking = (size: number) => {
    if ("letterSpacing" in ctx)
      (ctx as Ctx & { letterSpacing: string }).letterSpacing = zh
        ? "0px"
        : `${(-0.02 * size).toFixed(2)}px`;
  };
  const flow = (size: number): Line[] => {
    ctx.font = font(size);
    tracking(size);
    const gap = size * (zh ? 0.44 : 0.5);
    if (stacked)
      return model.picked.map((raw) => [{ text: capitalised(raw, zh), x: X0 }]);
    const out: Line[] = [[]];
    let x = X0;
    for (const raw of model.picked) {
      const text = capitalised(raw, zh);
      const width = ctx.measureText(text).width;
      if (x > X0 && x + width > X1) {
        out.push([]);
        x = X0;
      }
      out[out.length - 1]!.push({ text, x });
      x += width + gap;
    }
    return out;
  };
  const fitsWidth = (size: number) => {
    ctx.font = font(size);
    tracking(size);
    return model.picked.every(
      (raw) => ctx.measureText(capitalised(raw, zh)).width <= X1 - X0,
    );
  };
  const areaTop = MARK_TOP + markHeight + 56;
  const areaBottom = printBaseline - 26 - 56;
  const blockHeight = (size: number, count: number) =>
    (count - 1) * size * (zh ? 1.31 : 1.2) + size * (zh ? 0.88 : 0.72);
  const ladder = zh
    ? [124, 116, 108, 100, 92, 84]
    : [120, 112, 104, 96, 88, 80, 72];
  const wordSize =
    ladder.find(
      (size) =>
        (stacked ? fitsWidth(size) : flow(size).length <= 3) &&
        blockHeight(size, flow(size).length) <= areaBottom - areaTop,
    ) ??
    ladder.find(
      (size) => blockHeight(size, flow(size).length) <= areaBottom - areaTop,
    ) ??
    ladder[ladder.length - 1]!;
  const lines = flow(wordSize);
  const wordStep = wordSize * (zh ? 1.31 : 1.2);
  const firstBaseline =
    areaTop +
    (areaBottom - areaTop - blockHeight(wordSize, lines.length)) / 2 +
    wordSize * (zh ? 0.88 : 0.72);
  ctx.fillStyle = INK;
  ctx.font = font(wordSize);
  tracking(wordSize);
  lines.forEach((line, i) =>
    line.forEach((word) =>
      ctx.fillText(word.text, word.x, firstBaseline + i * wordStep),
    ),
  );
  if ("letterSpacing" in ctx)
    (ctx as Ctx & { letterSpacing: string }).letterSpacing = "0px";

  // the small print that closes the white part, as on a stamp: serial and date, the address
  const now = new Date();
  const date = `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, "0")}.${String(now.getDate()).padStart(2, "0")}`;
  ctx.fillStyle = MUTED;
  ctx.font = `600 26px ${DISPLAY}`;
  ctx.fillText(caps(`No. ${serial}   ${date}`), X0, printBaseline);
  const address = caps("flavorwords.com");
  ctx.fillText(address, X1 - ctx.measureText(address).width, printBaseline);

  // the footer is measured before the rows are drawn: slogan size, then the description at its natural length
  const slogan = ["Every ", "taste", " has its own vocabulary."];
  ctx.font = `700 60px ${DISPLAY}`;
  const sloganSize = Math.min(
    72,
    (60 * (X1 - X0)) / ctx.measureText(slogan.join("")).width,
  );
  const noteSize = zh ? 40 : 36;
  const noteLine = zh ? 62 : 54;
  const noteLast = SLOGAN_BASELINE - sloganSize - 84; // the description's last baseline, a fixed distance over the slogan
  const noteFont = `400 ${noteSize}px ${SANS}`;
  ctx.font = noteFont;
  const natural = model.cardNote
    ? fitSentences(ctx, model.cardNote, X1 - X0, zh, zh ? 4 : 5)
    : [];
  const noteTop =
    noteLast - Math.max(0, natural.length - 1) * noteLine - noteSize;

  // 3 · on the deep blue, anchored under the white part: the evaluation rows with the reference flavor, then the cup.
  //     The pitch opens up within a narrow range so that the space down to the description stays about the same.
  const labelSize = 42;
  const valueSize = 48;
  const rowCount = rows.length + model.cupInfo.length;
  const divider = rows.length && model.cupInfo.length ? 72 : 0;
  const pitch = Math.max(
    ROW_PITCH.min,
    Math.min(
      ROW_PITCH.max,
      (noteTop - ROWS_TO_NOTE - (split + 64) - divider) / Math.max(1, rowCount),
    ),
  );
  let y = split + 64;
  for (const row of rows) {
    y += pitch;
    leaderRow(ctx, row.label, row.value, y, labelSize, valueSize);
  }
  if (rows.length && model.cupInfo.length) {
    y += 64;
    ctx.save();
    ctx.strokeStyle = "rgba(255,255,255,0.24)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(X0, y);
    ctx.lineTo(X1, y);
    ctx.stroke();
    ctx.restore();
    y += 8;
  }
  for (const row of model.cupInfo) {
    y += pitch;
    leaderRow(
      ctx,
      capitalised(row.label, zh),
      row.value,
      y,
      labelSize,
      valueSize,
    );
  }

  // 4 · the footer, anchored to the bottom as one group: the slogan on one line, the letters of "taste" in colour …
  ctx.font = `700 ${sloganSize}px ${DISPLAY}`;
  let sx = X0;
  ctx.fillStyle = ON_DEEP;
  ctx.fillText(slogan[0]!, sx, SLOGAN_BASELINE);
  sx += ctx.measureText(slogan[0]!).width;
  [...slogan[1]!].forEach((ch, i) => {
    ctx.fillStyle = panel.letters[i]!;
    ctx.fillText(ch, sx, SLOGAN_BASELINE);
    sx += ctx.measureText(ch).width;
  });
  ctx.fillStyle = ON_DEEP;
  ctx.fillText(slogan[2]!, sx, SLOGAN_BASELINE);

  //     … and above it the supplementary description, its last line a fixed distance over the slogan. It keeps as many
  //     whole sentences as the space under the rows allows.
  if (natural.length) {
    const room = noteLast - (y + 96 + noteSize);
    const maxLines = Math.floor(room / noteLine) + 1;
    ctx.fillStyle = "rgba(255,255,255,0.88)";
    ctx.font = noteFont;
    const text =
      natural.length <= maxLines
        ? natural
        : maxLines >= 1
          ? fitSentences(ctx, model.cardNote, X1 - X0, zh, maxLines)
          : [];
    text.forEach((t, i) =>
      ctx.fillText(t, X0, noteLast - (text.length - 1 - i) * noteLine),
    );
  }

  return await new Promise<Blob>((resolve, reject) =>
    canvas.toBlob(
      (b) => (b ? resolve(b) : reject(new Error("toBlob failed"))),
      "image/png",
    ),
  );
}

/** Share the PNG through the system sheet when files are supported; otherwise save it. */
export async function shareCardPng(
  model: ResultCardModel,
  locale: "zh-CN" | "en",
): Promise<"shared" | "saved"> {
  const blob = await renderCardPng(model, locale);
  const file = new File([blob], "flavorwords-card.png", { type: "image/png" });
  const nav = navigator as Navigator & {
    canShare?: (d: { files: File[] }) => boolean;
    share?: (d: { files: File[]; title?: string }) => Promise<void>;
  };
  if (
    typeof nav.share === "function" &&
    typeof nav.canShare === "function" &&
    nav.canShare({ files: [file] })
  ) {
    await nav.share({ files: [file], title: "flavorwords" });
    return "shared";
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "flavorwords-card.png";
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
  return "saved";
}

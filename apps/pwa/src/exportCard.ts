/**
 * Export the flavor card as a 1200 × 1200 PNG (owner, 2026-09-12): the navy ground, the cream card, the motif row in
 * the words' feature colours, the cup's rows with dotted leaders, the words as one group, the reference and the
 * signature. Drawn with the Canvas 2D API from the same model the screen renders — no DOM capture, no dependency.
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
const FALLBACK = ["#7268C9", "#E4724B", "#C9DB6E", "#F2C24E", "#1F3B5C"];
const SANS = '"MiSans", "PingFang SC", "Noto Sans SC", system-ui, sans-serif';
const DISPLAY =
  '"Stack Sans", "MiSans", "Helvetica Neue", system-ui, sans-serif';

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

/** one motif tile, 30 × 30 units, at (x, y) scaled by s */
function tile(
  ctx: CanvasRenderingContext2D,
  i: number,
  x: number,
  y: number,
  s: number,
  color: string,
) {
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(s, s);
  ctx.fillStyle = color;
  ctx.strokeStyle = color;
  ctx.beginPath();
  switch (i % 5) {
    case 0:
      ctx.moveTo(3, 27);
      ctx.lineTo(3, 3);
      ctx.arc(3, 27, 24, -Math.PI / 2, 0);
      ctx.closePath();
      ctx.fill();
      break; // quarter
    case 1:
      ctx.arc(15, 15, 11, 0, Math.PI * 2);
      ctx.fill();
      break; // circle
    case 2:
      ctx.moveTo(3, 21);
      ctx.arc(15, 21, 12, Math.PI, 0);
      ctx.closePath();
      ctx.fill();
      break; // half
    case 3:
      ctx.moveTo(3, 27);
      ctx.lineTo(15, 3);
      ctx.lineTo(27, 27);
      ctx.closePath();
      ctx.fill();
      break; // triangle
    default:
      ctx.moveTo(15, 3);
      ctx.lineTo(27, 15);
      ctx.lineTo(15, 27);
      ctx.lineTo(3, 15);
      ctx.closePath();
      ctx.fill(); // diamond
  }
  ctx.restore();
}

function wrapWords(
  ctx: CanvasRenderingContext2D,
  words: string[],
  maxWidth: number,
  gap: number,
): string[][] {
  const lines: string[][] = [];
  let line: string[] = [];
  let width = 0;
  for (const w of words) {
    const ww = ctx.measureText(w).width;
    const next = line.length ? width + gap + ww : ww;
    if (line.length && next > maxWidth) {
      lines.push(line);
      line = [w];
      width = ww;
    } else {
      line.push(w);
      width = next;
    }
  }
  if (line.length) lines.push(line);
  return lines;
}

export async function renderCardPng(
  model: ResultCardModel,
  locale: "zh-CN" | "en",
): Promise<Blob> {
  const zh = locale === "zh-CN";
  if (typeof document !== "undefined" && document.fonts) {
    await Promise.all(
      [
        `600 96px ${SANS}`,
        `500 34px ${SANS}`,
        `400 30px ${SANS}`,
        `700 44px ${DISPLAY}`,
      ].map((f) => document.fonts.load(f).catch(() => undefined)),
    );
  }
  const S = 1200;
  const canvas = document.createElement("canvas");
  canvas.width = S;
  canvas.height = S;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = "#1F3B5C";
  ctx.fillRect(0, 0, S, S);
  const M = 72,
    X = M,
    Y = M,
    W = S - 2 * M,
    H = S - 2 * M;
  ctx.fillStyle = "#F3EEE2";
  roundRect(ctx, X, Y, W, H, 56);
  ctx.fill();
  const px = X + 72,
    pr = X + W - 72;
  let y = Y + 88;
  // eyebrow + motif row
  ctx.fillStyle = "#6B6660";
  ctx.font = `500 26px ${SANS}`;
  ctx.textBaseline = "alphabetic";
  ctx.fillText(
    (zh ? "风味卡" : "FLAVOR CARD").split("").join(zh ? "  " : " "),
    px,
    y,
  );
  const colors = model.picked.map(
    (_, i) =>
      DIM_COLORS[model.pickedDimensions[i] ?? ""] ??
      FALLBACK[i % FALLBACK.length]!,
  );
  const tileSize = 64,
    tileGap = 10;
  colors.forEach((c, i) =>
    tile(
      ctx,
      i,
      pr - colors.length * (tileSize + tileGap) + i * (tileSize + tileGap),
      y - 46,
      tileSize / 30,
      c,
    ),
  );
  y += 80;
  // cup rows with dotted leaders
  ctx.font = `400 30px ${SANS}`;
  for (const row of model.cupInfo) {
    ctx.fillStyle = "#6B6660";
    ctx.fillText(row.label, px, y);
    ctx.fillStyle = "#1E1C1A";
    ctx.font = `500 32px ${SANS}`;
    const vw = ctx.measureText(row.value).width;
    ctx.fillText(row.value, pr - vw, y);
    ctx.font = `400 30px ${SANS}`;
    const lw = ctx.measureText(row.label).width;
    ctx.save();
    ctx.strokeStyle = "rgba(30,28,26,0.4)";
    ctx.lineWidth = 2;
    ctx.setLineDash([2, 6]);
    ctx.beginPath();
    ctx.moveTo(px + lw + 18, y - 8);
    ctx.lineTo(pr - vw - 18, y - 8);
    ctx.stroke();
    ctx.restore();
    y += 52;
  }
  // the words as one group, set lower on the card (owner)
  y = Math.max(y + 40, Y + H * 0.5);
  ctx.fillStyle = "#1E1C1A";
  ctx.font = `600 96px ${SANS}`;
  const lines = wrapWords(ctx, model.picked, pr - px, 48);
  for (const line of lines) {
    let x = px;
    for (const w of line) {
      ctx.fillText(w, x, y + 80);
      x += ctx.measureText(w).width + 48;
    }
    y += 122;
  }
  // rule, reference, signature
  const footY = Y + H - 96;
  ctx.strokeStyle = "rgba(30,28,26,0.15)";
  ctx.lineWidth = 2;
  ctx.setLineDash([]);
  ctx.beginPath();
  ctx.moveTo(px, footY - 48);
  ctx.lineTo(pr, footY - 48);
  ctx.stroke();
  ctx.fillStyle = "#6B6660";
  ctx.font = `400 28px ${SANS}`;
  ctx.fillText(`${zh ? "参考风味" : "Reference"} · ${model.title}`, px, footY);
  ctx.fillStyle = "#1E1C1A";
  ctx.font = `700 40px ${DISPLAY}`;
  const bw = ctx.measureText("flavorwords").width;
  ctx.fillText("flavorwords", pr - bw, footY + 4);
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

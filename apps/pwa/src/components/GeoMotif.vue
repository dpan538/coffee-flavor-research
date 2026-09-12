<script setup lang="ts">
// The geometric kit (owner, 2026-09-12): flat shapes on 30 × 30 tiles, every shape inside its box, three compositions
// that share one language but are not the same row —
//   card:  a row of small tiles in the confirmed words' feature colours (quarter, circle, half, triangle, diamond);
//   home:  a stamp band — four tiles, each a coloured ground with a cream shape cut into it;
//   about: a quilt — six tiles in two rows, muted grounds, ink and cream shapes.
import { computed } from "vue";

type Tile = { bg?: string; fg: string; shape: "quarter" | "circle" | "half" | "triangle" | "diamond" | "ring" | "petals" | "bars" };
const props = withDefaults(defineProps<{ variant?: "card" | "home" | "about"; colors?: string[]; size?: number }>(), { variant: "card", colors: () => [], size: 24 });

const PALETTE = ["#7268C9", "#E4724B", "#FFD54A", "#7BE0C8", "#1F3B5C", "#E97BAF"];
const CARD_SHAPES: Tile["shape"][] = ["quarter", "circle", "half", "triangle", "diamond"];
const layout = computed<{ cols: number; rows: number; tiles: Tile[] }>(() => {
  if (props.variant === "home") {
    return { cols: 4, rows: 1, tiles: [
      { bg: "#7268C9", fg: "#F3EEE2", shape: "quarter" }, { bg: "#E4724B", fg: "#F3EEE2", shape: "half" },
      { bg: "#FFD54A", fg: "#1E1C1A", shape: "triangle" }, { bg: "#7BE0C8", fg: "#1E1C1A", shape: "petals" },
    ] };
  }
  if (props.variant === "about") {
    return { cols: 3, rows: 2, tiles: [
      { bg: "#EFE7D5", fg: "#7268C9", shape: "ring" }, { bg: "#7268C9", fg: "#F3EEE2", shape: "diamond" }, { bg: "#EFE7D5", fg: "#E4724B", shape: "bars" },
      { bg: "#1F3B5C", fg: "#F3EEE2", shape: "circle" }, { bg: "#EFE7D5", fg: "#1F3B5C", shape: "petals" }, { bg: "#FFD54A", fg: "#1E1C1A", shape: "quarter" },
    ] };
  }
  const colors = props.colors.length ? props.colors : PALETTE;
  return { cols: colors.length, rows: 1, tiles: colors.map((c, i) => ({ fg: c, shape: CARD_SHAPES[i % CARD_SHAPES.length]! })) };
});
const GAP = 4;
const width = computed(() => layout.value.cols * 30 + (layout.value.cols - 1) * GAP);
const height = computed(() => layout.value.rows * 30 + (layout.value.rows - 1) * GAP);
</script>

<template>
  <svg :viewBox="`0 0 ${width} ${height}`" :width="(width / 30) * size" :height="(height / 30) * size" aria-hidden="true" data-component="GeoMotif" :data-variant="variant">
    <g v-for="(t, i) in layout.tiles" :key="i" :transform="`translate(${(i % layout.cols) * (30 + GAP)} ${Math.floor(i / layout.cols) * (30 + GAP)})`">
      <rect v-if="t.bg" width="30" height="30" rx="3" :fill="t.bg" />
      <path v-if="t.shape === 'quarter'" d="M3 27 V3 A24 24 0 0 1 27 27 Z" :fill="t.fg" />
      <circle v-else-if="t.shape === 'circle'" cx="15" cy="15" r="11" :fill="t.fg" />
      <path v-else-if="t.shape === 'half'" d="M3 27 A12 12 0 0 1 27 27 Z" :fill="t.fg" transform="translate(0 -6)" />
      <path v-else-if="t.shape === 'triangle'" d="M3 27 L15 3 L27 27 Z" :fill="t.fg" />
      <path v-else-if="t.shape === 'diamond'" d="M15 3 L27 15 L15 27 L3 15 Z" :fill="t.fg" />
      <circle v-else-if="t.shape === 'ring'" cx="15" cy="15" r="9" fill="none" :stroke="t.fg" stroke-width="5" />
      <g v-else-if="t.shape === 'petals'" :fill="t.fg"><path d="M3 15 A12 12 0 0 1 15 3 A12 12 0 0 1 3 15 Z" /><path d="M27 15 A12 12 0 0 0 15 27 A12 12 0 0 0 27 15 Z" /></g>
      <g v-else :fill="t.fg"><rect x="3" y="5" width="24" height="6" rx="3" /><rect x="3" y="19" width="24" height="6" rx="3" /></g>
    </g>
  </svg>
</template>

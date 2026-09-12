<script setup lang="ts">
// The geometric motif kit (owner, 2026-09-12): a row of flat shapes in the palette — leaf, circle, fan, drop, ring,
// arch, wedge, wave — the same row the flavor card carries at its top, so home, About and the card share one
// signature. `shapes` picks the sequence, `colors` paints it (a card passes its words' feature colours).
import { computed } from "vue";

export type Shape = "leaf" | "circle" | "fan" | "drop" | "ring" | "arch" | "wedge" | "wave";
const props = withDefaults(defineProps<{ size?: number; colors?: string[]; shapes?: Shape[]; gap?: number }>(), {
  size: 22,
  colors: () => ["#7268C9", "#E4724B", "#C9DB6E", "#F2C24E", "#1F3B5C"],
  shapes: () => ["leaf", "circle", "fan", "drop", "ring"],
  gap: 4,
});
const step = computed(() => 30 + props.gap);
const width = computed(() => props.shapes.length * step.value - props.gap);
</script>

<template>
  <svg :viewBox="`0 0 ${width} 30`" :width="(width / 30) * size" :height="size" aria-hidden="true" data-component="BrandGlyphs">
    <g v-for="(shape, i) in shapes" :key="i" :transform="`translate(${i * step} 0)`">
      <path v-if="shape === 'leaf'" d="M2 28 C2 12 14 2 28 2 C28 18 16 28 2 28 Z" :fill="colors[i % colors.length]" />
      <circle v-else-if="shape === 'circle'" cx="15" cy="15" r="13" :fill="colors[i % colors.length]" />
      <path v-else-if="shape === 'fan'" d="M2 2 H28 A26 26 0 0 1 2 28 Z" :fill="colors[i % colors.length]" />
      <path v-else-if="shape === 'drop'" d="M15 2 C22 10 28 16 28 21 A13 13 0 0 1 2 21 C2 16 8 10 15 2 Z" :fill="colors[i % colors.length]" />
      <circle v-else-if="shape === 'ring'" cx="15" cy="15" r="11" fill="none" :stroke="colors[i % colors.length]" stroke-width="5" />
      <path v-else-if="shape === 'arch'" d="M2 28 V15 A13 13 0 0 1 28 15 V28 Z" :fill="colors[i % colors.length]" />
      <path v-else-if="shape === 'wedge'" d="M2 28 L15 2 L28 28 Z" :fill="colors[i % colors.length]" />
      <path v-else d="M2 22 C6 10 10 10 15 16 C20 22 24 22 28 10 V28 H2 Z" :fill="colors[i % colors.length]" />
    </g>
  </svg>
</template>

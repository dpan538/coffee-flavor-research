<script setup lang="ts">
// The flavor card — the product object (owner, 2026-09-12). Three layers: the cup's information (only what was
// entered), the confirmed words with the violet selection trace, the reference entry and the signature. Cream
// card like a printed tasting card; a motif made of the words' feature colours (one shape per word). No underline
// or highlight on the words (owner withdrew the violet trace): the words carry the card by size and spacing alone.
// Used by the final card, the home sample and the About sample.
import { computed } from "vue";

const props = withDefaults(defineProps<{
  cup: Array<{ label: string; value: string }>;
  words: string[];
  dimensions?: string[];
  reference?: string;
  brand?: string;
  eyebrow?: string;
  compact?: boolean;
}>(), { dimensions: () => [], reference: "", brand: "flavorwords", eyebrow: "", compact: false });

const DIM_COLORS: Record<string, string> = {
  acidity: "#F2C24E", sweetness: "#F5B0C6", body: "#9B7B5D", floral: "#7268C9", fruity: "#EE8F70", nutty_chocolate: "#B97C4E",
  fermented_winey: "#8C4A4C", bitter_roasted: "#1E1C1A", spice: "#DA8A80", herbal_green: "#6FA85A", woody_earthy: "#2F7A4C", defect: "#7F90B8",
};
const FALLBACK = ["#7268C9", "#EE8F70", "#C9DB6E", "#F2C24E", "#1F3B5C"];
const tiles = computed(() => props.words.map((_, i) => ({ color: DIM_COLORS[props.dimensions[i] ?? ""] ?? FALLBACK[i % FALLBACK.length]!, shape: i % 3 })));
</script>

<template>
  <article class="rounded-[22px] bg-cream text-ink" :class="compact ? 'px-4 pt-4 pb-3' : 'px-5 pt-5 pb-4'" data-component="FlavorCard">
    <div class="flex items-center justify-between">
      <p v-if="eyebrow" class="text-[10px] tracking-[0.2em] uppercase text-muted">{{ eyebrow }}</p>
      <!-- the motif: one shape per confirmed word, in the word's feature colour -->
      <svg :viewBox="`0 0 ${tiles.length * 30} 30`" :width="tiles.length * (compact ? 22 : 26)" :height="compact ? 22 : 26" aria-hidden="true" class="ml-auto">
        <g v-for="(t, i) in tiles" :key="i" :transform="`translate(${i * 30} 0)`">
          <path v-if="t.shape === 0" d="M2 28 C2 12 14 2 28 2 C28 18 16 28 2 28 Z" :fill="t.color" />
          <circle v-else-if="t.shape === 1" cx="15" cy="15" r="13" :fill="t.color" />
          <path v-else d="M2 2 H28 A26 26 0 0 1 2 28 Z" :fill="t.color" />
        </g>
      </svg>
    </div>
    <dl class="mt-3 space-y-1" data-layer="cup">
      <div v-for="row in cup" :key="row.label" class="leader">
        <dt class="text-muted">{{ row.label }}</dt><i /><dd class="font-medium normal-case tracking-normal text-[12px]">{{ row.value }}</dd>
      </div>
    </dl>
    <p class="flex flex-wrap gap-x-4 gap-y-1 font-semibold" :class="compact ? 'text-[22px] leading-[1.45] mt-3' : 'text-[27px] leading-[1.5] mt-4'" data-layer="words">
      <span v-for="w in words" :key="w">{{ w }}</span>
    </p>
    <div class="flex items-end justify-between mt-4 border-t border-ink/15 pt-2" data-layer="reference">
      <p class="text-[11px] text-muted">{{ reference }}</p>
      <p class="font-display text-[13px] tracking-tight">{{ brand }}</p>
    </div>
  </article>
</template>

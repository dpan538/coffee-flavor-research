<script setup lang="ts">
// The flavor card — the product object. Three layers: the cup's information (only what was entered), the confirmed
// words as one tight group, the reference entry and the signature. Cream card like a printed tasting card; the motif
// row at the top is the brand kit painted with the words' feature colours.
import { computed } from "vue";
import BrandGlyphs, { type Shape } from "./BrandGlyphs.vue";

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
const FALLBACK = ["#7268C9", "#E4724B", "#C9DB6E", "#F2C24E", "#1F3B5C"];
const SHAPES: Shape[] = ["leaf", "circle", "fan", "drop", "ring"];
const colors = computed(() => props.words.map((_, i) => DIM_COLORS[props.dimensions[i] ?? ""] ?? FALLBACK[i % FALLBACK.length]!));
const shapes = computed(() => props.words.map((_, i) => SHAPES[i % SHAPES.length]!));
</script>

<template>
  <article class="rounded-[22px] bg-cream text-ink" :class="compact ? 'px-4 pt-4 pb-3' : 'px-5 pt-5 pb-4'" data-component="FlavorCard">
    <div class="flex items-center justify-between">
      <p v-if="eyebrow" class="text-[10px] tracking-[0.2em] uppercase text-muted">{{ eyebrow }}</p>
      <BrandGlyphs class="ml-auto" :size="compact ? 20 : 24" :colors="colors" :shapes="shapes" />
    </div>
    <dl class="mt-3 space-y-1" data-layer="cup">
      <div v-for="row in cup" :key="row.label" class="leader">
        <dt class="text-muted">{{ row.label }}</dt><i /><dd class="font-medium normal-case tracking-normal text-[12px]">{{ row.value }}</dd>
      </div>
    </dl>
    <p class="flex flex-wrap gap-x-4 gap-y-0 font-semibold" :class="compact ? 'text-[22px] leading-[1.3] mt-3' : 'text-[27px] leading-[1.3] mt-4'" data-layer="words">
      <span v-for="w in words" :key="w">{{ w }}</span>
    </p>
    <div class="flex items-end justify-between mt-4 border-t border-ink/15 pt-2" data-layer="reference">
      <p class="text-[11px] text-muted">{{ reference }}</p>
      <p class="font-display text-[13px] tracking-tight">{{ brand }}</p>
    </div>
  </article>
</template>

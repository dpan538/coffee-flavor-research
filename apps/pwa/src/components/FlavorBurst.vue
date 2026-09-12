<script setup lang="ts">
// The 16 reference profiles as a radial spectrum: one ray per group, length on a log scale of its records, tick
// colours from the group's own centroid weights. Every number comes from the bundle. `progress` (0–1, scroll-driven
// in About) draws it: rings first, then the rays one after another from the centre outward, then the count.
import { computed } from "vue";
import { productVectorBundle } from "flavor-data/product-vector-v1";
import { locale } from "../store";

const props = withDefaults(defineProps<{ progress?: number }>(), { progress: 1 });
const DIM_COLORS: Record<string, string> = {
  acidity: "#F2C24E", sweetness: "#F5B0C6", body: "#9B7B5D", floral: "#7268C9", fruity: "#EE8F70", nutty_chocolate: "#B97C4E",
  fermented_winey: "#8C4A4C", bitter_roasted: "#1E1C1A", spice: "#DA8A80", herbal_green: "#6FA85A", woody_earthy: "#2F7A4C", defect: "#7F90B8",
};
const dims = productVectorBundle.dimensions as string[];
const profiles = computed(() => [...productVectorBundle.profiles].sort((a, b) => b.member_count - a.member_count));
const maxMembers = computed(() => Math.max(...profiles.value.map((p) => p.member_count)));
const size = 320;
const cx = size / 2;
const cy = size / 2;
const inner = 44;
const outer = size / 2 - 8;
const total = computed(() => profiles.value.reduce((a, p) => a + p.member_count, 0));

function polar(r: number, a: number) {
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)] as const;
}

type Tick = { r: number; color: string };
const spokes = computed(() =>
  profiles.value.map((p, i) => {
    const angle = -Math.PI / 2 + (i / profiles.value.length) * Math.PI * 2;
    const length = inner + (outer - inner) * (Math.log10(p.member_count + 1) / Math.log10(maxMembers.value + 1));
    const weights = dims.map((d, k) => ({ d, w: p.centroid[k] ?? 0 })).filter((x) => x.w > 0.12).sort((a, b) => b.w - a.w).slice(0, 4);
    const sum = weights.reduce((a, x) => a + x.w, 0) || 1;
    let from = inner;
    const ticks: Tick[] = [];
    for (const x of weights) {
      const len = (length - inner) * (x.w / sum);
      const count = Math.max(1, Math.round(len / 3.2));
      for (let t = 0; t < count; t += 1) ticks.push({ r: from + (t + 0.5) * (len / count), color: DIM_COLORS[x.d] ?? "#999" });
      from += len;
    }
    return { id: p.profile_id, angle, length, ticks, name: p.owner_name[locale.value] || p.owner_name.en, members: p.member_count };
  }),
);

// drawing schedule: 0–0.1 rings; 0.1–0.9 rays one after another, each drawn from the centre outward; 0.85–1 the count
const clamp = (x: number) => Math.max(0, Math.min(1, x));
const ringIn = computed(() => clamp(props.progress / 0.1));
const rayDraw = (i: number) => {
  const n = profiles.value.length;
  const span = 0.8 / n;
  return clamp((props.progress - 0.1 - i * span) / (span * 1.6));
};
const countShown = computed(() => Math.round(total.value * clamp((props.progress - 0.85) / 0.15)));
</script>

<template>
  <figure class="w-full" data-component="FlavorBurst">
    <svg :viewBox="`0 0 ${size} ${size}`" class="w-full h-auto" role="img" :aria-label="`${profiles.length} flavor profiles`">
      <circle v-for="k in 4" :key="'ring' + k" :cx="cx" :cy="cy" :r="inner + ((outer - inner) * k) / 4" fill="none" stroke="#1E1C1A" :stroke-opacity="0.08 * ringIn" stroke-width="0.6" />
      <g v-for="(s, i) in spokes" :key="s.id">
        <template v-for="(tick, t) in s.ticks" :key="t">
          <line v-if="tick.r <= inner + (s.length - inner) * rayDraw(i)"
            :x1="polar(tick.r, s.angle - 0.028)[0]" :y1="polar(tick.r, s.angle - 0.028)[1]"
            :x2="polar(tick.r, s.angle + 0.028)[0]" :y2="polar(tick.r, s.angle + 0.028)[1]"
            :stroke="tick.color" stroke-width="1.6" />
        </template>
        <circle v-if="rayDraw(i) >= 1" :cx="polar(s.length + 5, s.angle)[0]" :cy="polar(s.length + 5, s.angle)[1]" r="1.8" fill="#1E1C1A" />
      </g>
      <circle :cx="cx" :cy="cy" :r="inner - 8" fill="#FFFFFF" stroke="#1E1C1A" :stroke-opacity="ringIn" stroke-width="1" />
      <text :x="cx" :y="cy + 5" text-anchor="middle" font-size="13" fill="#1E1C1A" font-weight="600" :opacity="progress > 0.85 ? 1 : 0">{{ countShown.toLocaleString() }}</text>
    </svg>
    <figcaption class="mt-2 grid grid-cols-3 gap-x-3 gap-y-1 text-[11px] text-muted transition-opacity duration-500" :style="{ opacity: progress > 0.9 ? 1 : 0 }">
      <span v-for="d in dims" :key="d" class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-sm" :style="{ backgroundColor: DIM_COLORS[d] }" />{{ (productVectorBundle.presentation.dimension_labels as Record<string, Record<string, string>>)[d]?.[locale] }}</span>
    </figcaption>
  </figure>
</template>

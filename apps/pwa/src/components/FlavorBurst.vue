<script setup lang="ts">
// The data visual (owner: show what the engine was built from, not a copied chart). A radial spectrum:
// one ribbon per flavor profile, length on a log scale of its member coffees, colour segments from the
// profile's own centroid weights across the 12 dimensions. Every number comes from the bundle.
import { computed } from "vue";
import { productVectorBundle } from "flavor-data/product-vector-v1";
import { locale } from "../store";

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

/** ribbon segments: each profile spoke is cut by its top dimension weights (share of the spoke's length) */
const spokes = computed(() =>
  profiles.value.map((p, i) => {
    const angle = -Math.PI / 2 + (i / profiles.value.length) * Math.PI * 2;
    const length = inner + (outer - inner) * (Math.log10(p.member_count + 1) / Math.log10(maxMembers.value + 1));
    const weights = dims.map((d, k) => ({ d, w: p.centroid[k] ?? 0 })).filter((x) => x.w > 0.12).sort((a, b) => b.w - a.w).slice(0, 4);
    const sum = weights.reduce((a, x) => a + x.w, 0) || 1;
    let from = inner;
    const segments = weights.map((x) => {
      const len = (length - inner) * (x.w / sum);
      const seg = { color: DIM_COLORS[x.d] ?? "#999", r0: from, r1: from + len };
      from += len;
      return seg;
    });
    return { id: p.profile_id, angle, length, segments, name: p.owner_name["zh-CN"] || p.owner_name.en, members: p.member_count };
  }),
);
</script>

<template>
  <figure class="w-full" data-component="FlavorBurst">
    <svg :viewBox="`0 0 ${size} ${size}`" class="w-full h-auto" role="img" :aria-label="`${profiles.length} flavor profiles`">
      <circle v-for="k in 4" :key="'ring' + k" :cx="cx" :cy="cy" :r="inner + ((outer - inner) * k) / 4" fill="none" stroke="#1E1C1A" stroke-opacity="0.08" stroke-width="0.6" />
      <g v-for="s in spokes" :key="s.id">
        <template v-for="(seg, i) in s.segments" :key="i">
          <line v-for="t in Math.max(1, Math.round((seg.r1 - seg.r0) / 3.2))" :key="t"
            :x1="polar(seg.r0 + (t - 0.5) * ((seg.r1 - seg.r0) / Math.max(1, Math.round((seg.r1 - seg.r0) / 3.2))), s.angle - 0.028)[0]"
            :y1="polar(seg.r0 + (t - 0.5) * ((seg.r1 - seg.r0) / Math.max(1, Math.round((seg.r1 - seg.r0) / 3.2))), s.angle - 0.028)[1]"
            :x2="polar(seg.r0 + (t - 0.5) * ((seg.r1 - seg.r0) / Math.max(1, Math.round((seg.r1 - seg.r0) / 3.2))), s.angle + 0.028)[0]"
            :y2="polar(seg.r0 + (t - 0.5) * ((seg.r1 - seg.r0) / Math.max(1, Math.round((seg.r1 - seg.r0) / 3.2))), s.angle + 0.028)[1]"
            :stroke="seg.color" stroke-width="1.6" />
        </template>
        <circle :cx="polar(s.length + 5, s.angle)[0]" :cy="polar(s.length + 5, s.angle)[1]" r="1.8" fill="#1E1C1A" />
      </g>
      <circle :cx="cx" :cy="cy" :r="inner - 8" fill="#FFFFFF" stroke="#1E1C1A" stroke-width="1" />
      <text :x="cx" :y="cy + 5" text-anchor="middle" font-size="13" fill="#1E1C1A" font-weight="600">{{ total.toLocaleString() }}</text>
    </svg>
    <figcaption class="mt-2 grid grid-cols-3 gap-x-3 gap-y-1 text-[11px] text-muted">
      <span v-for="d in dims" :key="d" class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-sm" :style="{ backgroundColor: DIM_COLORS[d] }" />{{ (productVectorBundle.presentation.dimension_labels as Record<string, Record<string, string>>)[d]?.[locale] }}</span>
    </figcaption>
  </figure>
</template>

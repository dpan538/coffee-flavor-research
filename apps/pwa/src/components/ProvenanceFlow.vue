<script setup lang="ts">
// Where the data came from and what it became: source families on the left, the 12 dimensions on the right,
// ribbons whose width is the family's mass on that dimension (from corpus_facts.families). Pure SVG, our own numbers.
import { computed } from "vue";
import { productVectorBundle } from "flavor-data/product-vector-v1";
import { locale } from "../store";

const DIM_COLORS: Record<string, string> = {
  acidity: "#F2C24E", sweetness: "#F5B0C6", body: "#9B7B5D", floral: "#7268C9", fruity: "#EE8F70", nutty_chocolate: "#B97C4E",
  fermented_winey: "#8C4A4C", bitter_roasted: "#1E1C1A", spice: "#DA8A80", herbal_green: "#6FA85A", woody_earthy: "#2F7A4C", defect: "#7F90B8",
};
const FAMILY_LABEL: Record<string, Record<string, string>> = {
  coffeereview_kaggle_parsed: { "zh-CN": "CoffeeReview 编辑评审", en: "CoffeeReview editorial reviews" },
  ace_cup_of_excellence: { "zh-CN": "Cup of Excellence 评审", en: "Cup of Excellence juries" },
  mdpi_certified_q_grader_storage_panel: { "zh-CN": "Q-grader 储藏实验", en: "Q-grader storage panel" },
  zenodo_golovinsky_q_grader_dataset: { "zh-CN": "Q-grader 数据集", en: "Q-grader dataset" },
  frontiers_inera_robusta_q_grader_panel: { "zh-CN": "罗布斯塔 Q-grader 评审", en: "Robusta Q-grader panel" },
};
const dims = productVectorBundle.dimensions as string[];
const labels = productVectorBundle.presentation.dimension_labels as Record<string, Record<string, string>>;
type Family = { family: string; coffees: number; mass: number[] };
const families = computed<Family[]>(() => {
  const all = (productVectorBundle.corpus_facts as { families: Family[] }).families;
  const top = all.slice(0, 5);
  const rest = all.slice(5);
  if (rest.length) top.push({ family: "others", coffees: rest.reduce((a, f) => a + f.coffees, 0), mass: dims.map((_, i) => rest.reduce((a, f) => a + (f.mass[i] ?? 0), 0)) });
  return top;
});
const W = 340, H = 300, LX = 96, RX = 244, GAP = 4;
const familyTotals = computed(() => families.value.map((f) => f.mass.reduce((a, b) => a + b, 0)));
const dimTotals = computed(() => dims.map((_, i) => families.value.reduce((a, f) => a + (f.mass[i] ?? 0), 0)));
const scaleL = computed(() => (H - GAP * (families.value.length - 1)) / familyTotals.value.reduce((a, b) => a + b, 0));
const scaleR = computed(() => (H - GAP * (dims.length - 1)) / dimTotals.value.reduce((a, b) => a + b, 0));
const leftBars = computed(() => { let y = 0; return families.value.map((f, i) => { const h = familyTotals.value[i]! * scaleL.value; const bar = { y, h, f }; y += h + GAP; return bar; }); });
const rightBars = computed(() => { let y = 0; return dims.map((d, i) => { const h = dimTotals.value[i]! * scaleR.value; const bar = { y, h, d }; y += h + GAP; return bar; }); });
const ribbons = computed(() => {
  const outL = leftBars.value.map((b) => b.y);
  const outR = rightBars.value.map((b) => b.y);
  const out: Array<{ d: string; color: string; family: string }> = [];
  families.value.forEach((f, fi) => {
    dims.forEach((dim, di) => {
      const m = f.mass[di] ?? 0;
      if (m <= 0) return;
      const hL = m * scaleL.value, hR = m * scaleR.value;
      const y0 = outL[fi]!, y1 = outR[di]!;
      outL[fi] = y0 + hL; outR[di] = y1 + hR;
      const c = (LX + RX) / 2;
      out.push({ d: `M ${LX} ${y0} C ${c} ${y0} ${c} ${y1} ${RX} ${y1} L ${RX} ${y1 + hR} C ${c} ${y1 + hR} ${c} ${y0 + hL} ${LX} ${y0 + hL} Z`, color: DIM_COLORS[dim] ?? "#999", family: f.family });
    });
  });
  return out;
});
const fmt = (n: number) => n.toLocaleString(locale.value === "zh-CN" ? "zh-CN" : "en-US");
</script>

<template>
  <figure class="w-full" data-component="ProvenanceFlow">
    <svg :viewBox="`0 0 ${W} ${H}`" class="w-full h-auto" role="img">
      <path v-for="(r, i) in ribbons" :key="i" :d="r.d" :fill="r.color" fill-opacity="0.55" />
      <g v-for="b in leftBars" :key="b.f.family">
        <rect :x="LX - 6" :y="b.y" width="6" :height="b.h" fill="#1E1C1A" />
        <text :x="LX - 10" :y="b.y + Math.min(b.h, 14) / 2 + 3.5" text-anchor="end" font-size="8.5" fill="#1E1C1A">{{ FAMILY_LABEL[b.f.family]?.[locale] ?? (b.f.family === 'others' ? (locale === 'zh-CN' ? '其他评审' : 'other panels') : b.f.family) }}</text>
        <text :x="LX - 10" :y="b.y + Math.min(b.h, 14) / 2 + 13" text-anchor="end" font-size="7.5" fill="#6B6660">{{ fmt(b.f.coffees) }}</text>
      </g>
      <g v-for="b in rightBars" :key="b.d">
        <rect :x="RX" :y="b.y" width="6" :height="b.h" :fill="DIM_COLORS[b.d]" />
        <text :x="RX + 10" :y="b.y + b.h / 2 + 3.5" font-size="8.5" fill="#1E1C1A">{{ labels[b.d]?.[locale] }}</text>
      </g>
    </svg>
  </figure>
</template>

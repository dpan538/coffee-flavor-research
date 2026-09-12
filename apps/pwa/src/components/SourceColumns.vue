<script setup lang="ts">
// "From coffee reviews to flavor descriptions" as a poster (owner reference: the extinction chart). Black page,
// white type. Twelve columns A–L, one per flavor feature: the bar is that feature's cumulative weight across the
// review panels (log scale, tier lines at 10 / 100 / 1,000), stacked by panel (opacity = panel), a dot and the
// value at the top. Below the baseline every column bends into one trunk: the records that enter the grouping.
// `progress` (0–1, scroll-driven) draws it: axes → columns one by one → the tree → the trunk label.
import { computed } from "vue";
import { productVectorBundle } from "flavor-data/product-vector-v1";
import { locale } from "../store";

const props = withDefaults(defineProps<{ progress?: number }>(), { progress: 1 });
const DIM_COLORS: Record<string, string> = {
  acidity: "#F2C24E", sweetness: "#F5B0C6", body: "#B79B7C", floral: "#9C92E8", fruity: "#EE8F70", nutty_chocolate: "#C98A55",
  fermented_winey: "#B2626A", bitter_roasted: "#D8D2C8", spice: "#DA8A80", herbal_green: "#8CC46F", woody_earthy: "#4FA06C", defect: "#8FA0C8",
};
const FAMILY_LABEL: Record<string, Record<string, string>> = {
  coffeereview_kaggle_parsed: { "zh-CN": "CoffeeReview 编辑评审", en: "CoffeeReview editorial reviews" },
  ace_cup_of_excellence: { "zh-CN": "Cup of Excellence 评审", en: "Cup of Excellence juries" },
  zenodo_golovinsky_q_grader_dataset: { "zh-CN": "Q-grader 数据集", en: "Q-grader dataset" },
  frontiers_inera_robusta_q_grader_panel: { "zh-CN": "罗布斯塔 Q-grader 评审", en: "Robusta Q-grader panel" },
  project_origin: { "zh-CN": "Project Origin 评审", en: "Project Origin panel" },
  frontiers_cenicafe_lengupa_trained_cuppers: { "zh-CN": "Cenicafé 受训杯测师", en: "Cenicafé trained cuppers" },
  coffee_board_of_india_fine_cup: { "zh-CN": "印度咖啡局 Fine Cup", en: "Coffee Board of India Fine Cup" },
  sheba_coffee_yemen_auction: { "zh-CN": "也门 Sheba 拍卖评审", en: "Sheba Yemen auction panel" },
};
type Family = { family: string; coffees: number; mass: number[] };
const dims = productVectorBundle.dimensions as string[];
const labels = productVectorBundle.presentation.dimension_labels as Record<string, Record<string, string>>;
const facts = productVectorBundle.corpus_facts as unknown as { families: Family[]; usable_coffee_vectors: number; profiles: number };
const families = computed(() => [...facts.families].sort((a, b) => b.coffees - a.coffees));
const zh = computed(() => locale.value === "zh-CN");
const fmt = (v: number) => Math.round(v).toLocaleString(locale.value === "zh-CN" ? "zh-CN" : "en-US");
const LETTERS = "ABCDEFGHIJKL".split("");

const W = 375, TOP = 30, BASE = 336, TRUNK_Y = 478, CX = 187.5, SLOPE = 0.5;
const xs = dims.map((_, i) => 36 + i * 28.2);
const totals = computed(() => dims.map((_, i) => families.value.reduce((a, f) => a + (f.mass[i] ?? 0), 0)));
const maxTotal = computed(() => Math.max(...totals.value));
const yOf = (m: number) => BASE - (Math.log10(m + 1) / Math.log10(maxTotal.value + 1)) * (BASE - TOP - 14);
const tiers = computed(() => [10, 100, 1000].filter((t) => t < maxTotal.value).map((t) => ({ t, y: yOf(t) })));
const minorTiers = computed(() => [3, 30, 300, 3000].filter((t) => t < maxTotal.value).map((t) => ({ t, y: yOf(t) })));
const grand = computed(() => totals.value.reduce((a, b) => a + b, 0));
const share = (i: number) => `${Math.round((totals.value[i]! / grand.value) * 100)}%`;
const clamp = (x: number) => Math.max(0, Math.min(1, x));
const axesIn = computed(() => clamp(props.progress / 0.12));
const colIn = (i: number) => clamp((props.progress - 0.12 - i * 0.042) / 0.07);
const treeIn = (i: number) => clamp((props.progress - 0.66 - i * 0.018) / 0.14);
const trunkIn = computed(() => clamp((props.progress - 0.9) / 0.1));
const panelIn = (i: number) => clamp((props.progress - 0.02 - i * 0.03) / 0.08);
const columns = computed(() =>
  dims.map((d, i) => {
    const total = totals.value[i]!;
    const top = yOf(total);
    const h = (BASE - top) * colIn(i);
    let y = BASE;
    const segments = families.value.map((f, fi) => {
      const share = total > 0 ? (f.mass[i] ?? 0) / total : 0;
      const sh = h * share;
      const seg = { y: y - sh, h: sh, opacity: fi === 0 ? 1 : fi === 1 ? 0.7 : 0.42 };
      y -= sh;
      return seg;
    });
    return { d, i, x: xs[i]!, total, top: BASE - h, segments, color: DIM_COLORS[d] ?? "#ccc", done: colIn(i) >= 1 };
  }),
);
/** the tree: each column drops, bends at 45° toward the centre bundle, and runs down into the trunk */
const tree = computed(() =>
  dims.map((_, i) => {
    const x = xs[i]!;
    const k = i < 6 ? 5 - i : i - 6; // rank from the centre
    const sign = i < 6 ? -1 : 1;
    const xt = CX + sign * (k * 6.5 + 3.25);
    const y1 = BASE + 12 + (5 - k) * 8;
    const y2 = y1 + Math.abs(x - xt) * SLOPE;
    const d = `M ${x} ${BASE} V ${y1} L ${xt} ${y2} V ${TRUNK_Y}`;
    const len = (y1 - BASE) + Math.hypot(x - xt, y2 - y1) + (TRUNK_Y - y2);
    return { d, len, color: DIM_COLORS[dims[i]!] ?? "#ccc", draw: treeIn(i) };
  }),
);
</script>

<template>
  <figure class="w-full text-[#F4F1EA]" data-component="SourceColumns">
    <div class="flex items-start justify-between gap-3">
      <div class="text-[12px] leading-[1.4] text-[#B9B4AA] max-w-[196px]">
        {{ zh ? '十二类风味特征在全部评审记录里的累计权重（对数刻度）；深浅是来源评审族，字母下是各自占比。' : 'Twelve flavor features by cumulative weight across every review record (log scale); shades are the review panels, the share sits under each letter.' }}
      </div>
      <ul class="text-[11px] leading-[1.35] shrink-0" data-index="panels">
        <li v-for="(f, i) in families" :key="f.family" class="flex gap-2 transition-opacity duration-300" :style="{ opacity: panelIn(i) }">
          <span class="inline-block w-3 h-[8px] mt-[4px] rounded-[1px] bg-[#F4F1EA]" :style="{ opacity: i === 0 ? 1 : i === 1 ? 0.7 : 0.42 }" /><span class="text-[#B9B4AA]">{{ FAMILY_LABEL[f.family]?.[locale] ?? f.family }} <b class="text-[#F4F1EA] font-medium tabular-nums">{{ fmt(f.coffees) }}</b></span>
        </li>
      </ul>
    </div>
    <ul class="grid grid-cols-3 gap-x-2 gap-y-[3px] mt-2 text-[12px] leading-[1.3]" data-index="features" :style="{ opacity: axesIn }">
      <li v-for="(d, i) in dims" :key="d" class="flex items-center gap-1.5"><b class="w-3 font-semibold">{{ LETTERS[i] }}</b><span class="inline-block w-2 h-2 rounded-sm" :style="{ backgroundColor: DIM_COLORS[d] }" /><span class="text-[#D8D2C8]">{{ labels[d]?.[locale] }}</span></li>
    </ul>
    <svg :viewBox="`0 0 ${W} 526`" class="w-full h-auto max-h-[58dvh] mx-auto mt-1" role="img" font-family="inherit">
      <!-- tiers -->
      <g :opacity="axesIn">
        <line v-for="t in minorTiers" :key="'m' + t.t" x1="18" :x2="W - 6" :y1="t.y" :y2="t.y" stroke="#F4F1EA" stroke-opacity="0.1" stroke-width="0.5" stroke-dasharray="2 3" />
        <line v-for="t in tiers" :key="t.t" x1="18" :x2="W - 6" :y1="t.y" :y2="t.y" stroke="#F4F1EA" stroke-opacity="0.22" stroke-width="0.6" />
        <text v-for="t in tiers" :key="'l' + t.t" x="4" :y="t.y - 3" font-size="9.5" fill="#B9B4AA">{{ fmt(t.t) }}</text>
        <line x1="18" :x2="W - 6" :y1="BASE" :y2="BASE" stroke="#F4F1EA" stroke-opacity="0.6" stroke-width="1" />
        <text x="4" :y="BASE - 3" font-size="8.5" fill="#B9B4AA">0</text>
        <g v-for="(x, i) in xs" :key="'g' + i">
          <line :x1="x" :x2="x" :y1="TOP" :y2="BASE" stroke="#F4F1EA" stroke-opacity="0.18" stroke-width="0.6" />
          <text :x="x" :y="TOP - 14" text-anchor="middle" font-size="12" font-weight="700" fill="#F4F1EA">{{ LETTERS[i] }}</text>
          <text :x="x" :y="TOP - 3" text-anchor="middle" font-size="8.5" fill="#B9B4AA">{{ share(i) }}</text>
        </g>
      </g>
      <!-- the tree, drawn from each column into the trunk -->
      <path v-for="(t, i) in tree" :key="'t' + i" :d="t.d" fill="none" :stroke="t.color" stroke-width="5" stroke-linejoin="round" stroke-linecap="butt" :stroke-dasharray="t.len" :stroke-dashoffset="t.len * (1 - t.draw)" stroke-opacity="0.92" />
      <!-- the columns -->
      <g v-for="c in columns" :key="c.d">
        <rect v-for="(s, k) in c.segments" :key="k" :x="c.x - 7" :y="s.y" width="14" :height="Math.max(0, s.h)" :fill="c.color" :fill-opacity="s.opacity" />
        <line v-for="(s, k) in c.segments.slice(1)" :key="'k' + k" :x1="c.x - 9" :x2="c.x + 9" :y1="s.y + s.h" :y2="s.y + s.h" stroke="#0B0A09" stroke-width="1" />
        <circle v-if="c.done" :cx="c.x" :cy="c.top - 6" r="4" :fill="c.color" stroke="#0B0A09" stroke-width="1.2" />
        <text v-if="c.done" :x="c.x" :y="c.top - 13" text-anchor="middle" font-size="8.5" fill="#F4F1EA">{{ fmt(c.total) }}</text>
      </g>
      <!-- the trunk -->
      <g :opacity="trunkIn">
        <rect :x="CX - 100" :y="TRUNK_Y + 2" width="200" height="44" rx="8" fill="#F4F1EA" />
        <text :x="CX" :y="TRUNK_Y + 21" text-anchor="middle" font-size="13" font-weight="700" fill="#0B0A09">{{ fmt(facts.usable_coffee_vectors) }} {{ zh ? '条记录' : 'records' }}</text>
        <text :x="CX" :y="TRUNK_Y + 37" text-anchor="middle" font-size="10" fill="#4a4642">{{ zh ? `→ 整理为 ${facts.profiles} 组参考风味` : `→ organised into ${facts.profiles} reference profiles` }}</text>
      </g>
    </svg>
  </figure>
</template>

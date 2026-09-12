<script setup lang="ts">
// The sixteen reference profiles as a network (owner reference: the "connect the dots" spread). Black page, white
// type. Numbered circles, sized by records, coloured by the group's strongest feature, on two rings around the
// pool of records; white curves join each group to its two nearest groups (cosine of centroids); the strongest
// links carry a callout C1–C6 explained in the notes; a numbered index and a feature legend make every label
// readable. `progress` (0–1, scroll-driven) draws it: rings → circles one by one → links → callouts and notes.
import { computed } from "vue";
import { productVectorBundle } from "flavor-data/product-vector-v1";
import { locale } from "../store";

const props = withDefaults(defineProps<{ progress?: number }>(), { progress: 1 });
const DIM_COLORS: Record<string, string> = {
  acidity: "#F2C24E", sweetness: "#F5B0C6", body: "#B79B7C", floral: "#9C92E8", fruity: "#EE8F70", nutty_chocolate: "#C98A55",
  fermented_winey: "#B2626A", bitter_roasted: "#D8D2C8", spice: "#DA8A80", herbal_green: "#8CC46F", woody_earthy: "#4FA06C", defect: "#8FA0C8",
};
const dims = productVectorBundle.dimensions as string[];
const labels = productVectorBundle.presentation.dimension_labels as Record<string, Record<string, string>>;
const zh = computed(() => locale.value === "zh-CN");
const fmt = (v: number) => v.toLocaleString(locale.value === "zh-CN" ? "zh-CN" : "en-US");
const W = 375, H = 372, CX = 187.5, CY = 186, R1 = 76, R2 = 146;

type Node = { n: number; id: string; name: string; members: number; x: number; y: number; r: number; color: string; top: string[]; centroid: number[] };
const nodes = computed<Node[]>(() => {
  const sorted = [...productVectorBundle.profiles].sort((a, b) => b.member_count - a.member_count);
  const max = Math.log10(sorted[0]!.member_count + 1);
  return sorted.map((p, i) => {
    const inner = i < 6;
    const k = inner ? i : i - 6;
    const count = inner ? 6 : 10;
    const angle = -Math.PI / 2 + (inner ? Math.PI / 6 : Math.PI / count) + (k / count) * Math.PI * 2;
    const R = inner ? R1 : R2;
    const top = dims.map((d, j) => ({ d, w: p.centroid[j] ?? 0 })).sort((a, b) => b.w - a.w).slice(0, 2).map((x) => x.d);
    return { n: i + 1, id: p.profile_id, name: p.owner_name[locale.value] || p.owner_name.en, members: p.member_count, x: CX + R * Math.cos(angle), y: CY + R * Math.sin(angle), r: 11 + 11 * (Math.log10(p.member_count + 1) / max), color: DIM_COLORS[top[0]!] ?? "#ccc", top, centroid: p.centroid as number[] };
  });
});
function cosine(a: number[], b: number[]) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i += 1) { dot += (a[i] ?? 0) * (b[i] ?? 0); na += (a[i] ?? 0) ** 2; nb += (b[i] ?? 0) ** 2; }
  return na && nb ? dot / Math.sqrt(na * nb) : 0;
}
type Edge = { a: Node; b: Node; sim: number; shared: string[]; d: string; len: number; mx: number; my: number; callout: string };
const edges = computed<Edge[]>(() => {
  const ns = nodes.value;
  const seen = new Set<string>();
  const out: Edge[] = [];
  for (const a of ns) {
    const nearest = ns.filter((b) => b !== a).map((b) => ({ b, sim: cosine(a.centroid, b.centroid) })).sort((x, y) => y.sim - x.sim).slice(0, 2);
    for (const { b, sim } of nearest) {
      if (sim < 0.5) continue;
      const key = [a.n, b.n].sort((x, y) => x - y).join("-");
      if (seen.has(key)) continue;
      seen.add(key);
      const mean = a.centroid.map((v, i) => (v + (b.centroid[i] ?? 0)) / 2);
      const shared = dims.map((d, i) => ({ d, w: mean[i] ?? 0 })).sort((x, y) => y.w - x.w).slice(0, 2).map((x) => labels[x.d]?.[locale.value] ?? x.d);
      // a quadratic curve bowing away from the centre, like the reference's arcs
      const mx0 = (a.x + b.x) / 2, my0 = (a.y + b.y) / 2;
      const dx = mx0 - CX, dy = my0 - CY, dist = Math.hypot(dx, dy) || 1;
      const cx = mx0 + (dx / dist) * 26, cy = my0 + (dy / dist) * 26;
      const len = Math.hypot(a.x - cx, a.y - cy) + Math.hypot(b.x - cx, b.y - cy);
      out.push({ a, b, sim, shared, d: `M ${a.x} ${a.y} Q ${cx} ${cy} ${b.x} ${b.y}`, len, mx: (a.x + 2 * cx + b.x) / 4, my: (a.y + 2 * cy + b.y) / 4, callout: "" });
    }
  }
  out.sort((x, y) => y.sim - x.sim);
  out.forEach((e, i) => { if (i < 6) e.callout = `C${i + 1}`; });
  return out;
});
const callouts = computed(() => edges.value.filter((e) => e.callout));
const clamp = (x: number) => Math.max(0, Math.min(1, x));
const ringsIn = computed(() => clamp(props.progress / 0.1));
const nodeIn = (i: number) => clamp((props.progress - 0.1 - i * 0.03) / 0.06);
const edgeIn = (i: number) => clamp((props.progress - 0.6 - i * 0.012) / 0.1);
const notesIn = computed(() => clamp((props.progress - 0.85) / 0.12));
const ink = (hex: string) => { const n = parseInt(hex.slice(1), 16); const l = (0.2126 * ((n >> 16) & 255) + 0.7152 * ((n >> 8) & 255) + 0.0722 * (n & 255)) / 255; return l > 0.6 ? "#0B0A09" : "#F4F1EA"; };
</script>

<template>
  <figure class="w-full text-[#F4F1EA]" data-component="ProfileNetwork">
    <div class="flex items-start justify-between gap-3">
      <p class="text-[12px] leading-[1.4] text-[#B9B4AA] max-w-[150px]">{{ zh ? '大小按记录数，颜色是该组最强的风味特征；内圈是记录最多的 6 组。白线连到最接近的两组，C1–C6 是最接近的几对。' : 'Size by records, colour by the group\'s strongest feature; the inner ring holds the 6 largest. Curves join the two nearest groups, C1–C6 the closest pairs.' }}</p>
      <ol class="grid grid-cols-2 gap-x-2 gap-y-[2px] text-[11px] leading-[1.3] shrink-0" data-index="profiles">
        <li v-for="(nd, i) in nodes" :key="nd.id" class="flex gap-1 transition-opacity duration-300" :style="{ opacity: nodeIn(i) }"><b class="w-4 text-right font-semibold tabular-nums">{{ nd.n }}</b><span class="text-[#D8D2C8]">{{ nd.name }}</span></li>
      </ol>
    </div>
    <svg :viewBox="`0 0 ${W} ${H}`" class="w-full h-auto max-h-[44dvh] mx-auto mt-1" role="img">
      <g :opacity="ringsIn">
        <circle :cx="CX" :cy="CY" :r="R1" fill="none" stroke="#F4F1EA" stroke-opacity="0.35" stroke-width="0.8" stroke-dasharray="3 4" />
        <circle :cx="CX" :cy="CY" :r="R2" fill="none" stroke="#F4F1EA" stroke-opacity="0.35" stroke-width="0.8" stroke-dasharray="3 4" />
        <text :x="CX" :y="CY + R1 + 18" text-anchor="middle" font-size="10" fill="#B9B4AA">{{ zh ? '记录最多的 6 组' : 'the 6 largest' }}</text>
        <text :x="CX" :y="CY - R2 - 6" text-anchor="middle" font-size="10" fill="#B9B4AA">{{ zh ? '其余 10 组' : 'the other 10' }}</text>
        <circle :cx="CX" :cy="CY" r="27" fill="#F4F1EA" />
        <text :x="CX" :y="CY - 1" text-anchor="middle" font-size="11" font-weight="700" fill="#0B0A09">{{ fmt(nodes.reduce((a, n) => a + n.members, 0)) }}</text>
        <text :x="CX" :y="CY + 10" text-anchor="middle" font-size="8.5" fill="#4a4642">{{ zh ? '条记录' : 'records' }}</text>
      </g>
      <path v-for="(e, i) in edges" :key="'e' + i" :d="e.d" fill="none" stroke="#F4F1EA" stroke-width="1" stroke-opacity="0.75" :stroke-dasharray="e.len" :stroke-dashoffset="e.len * (1 - edgeIn(i))" />
      <g v-for="(nd, i) in nodes" :key="nd.id" :transform="`translate(${nd.x} ${nd.y}) scale(${nodeIn(i)})`">
        <circle :r="nd.r" :fill="nd.color" />
        <text y="4" text-anchor="middle" font-size="11" font-weight="700" :fill="ink(nd.color)">{{ nd.n }}</text>
      </g>
      <g v-for="e in callouts" :key="e.callout" :opacity="notesIn">
        <rect :x="e.mx - 12" :y="e.my - 8" width="24" height="16" rx="2" fill="#F4F1EA" />
        <text :x="e.mx" :y="e.my + 4" text-anchor="middle" font-size="9.5" font-weight="700" fill="#0B0A09">{{ e.callout }}</text>
      </g>
    </svg>
    <div class="mt-2 transition-opacity duration-500" :style="{ opacity: notesIn }">
      <ul class="grid grid-cols-2 gap-x-3 gap-y-[2px] text-[11px] leading-[1.35] text-[#D8D2C8]" data-index="callouts">
        <li v-for="e in callouts" :key="e.callout"><b class="text-[#F4F1EA]">{{ e.callout }}</b> {{ e.a.n }} ↔ {{ e.b.n }} · {{ e.shared.join("、") }} <span class="text-[#8f8a80] tabular-nums">{{ e.sim.toFixed(2) }}</span></li>
      </ul>
      <ul class="grid grid-cols-4 gap-x-2 gap-y-[2px] mt-2 text-[11px] leading-[1.3]" data-index="features">
        <li v-for="d in dims" :key="d" class="flex items-center gap-1"><span class="inline-block w-2 h-2 rounded-sm shrink-0" :style="{ backgroundColor: DIM_COLORS[d] }" /><span class="text-[#D8D2C8] truncate">{{ labels[d]?.[locale] }}</span></li>
      </ul>
    </div>
  </figure>
</template>

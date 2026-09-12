<script setup lang="ts">
// Final card: heading (small) → profile → three lead words (largest) → two more (muted) → colour bar of the picked
// words' dimensions → attribution (CSS-grid fold, closed by default) → icon bar: home, start over, share.
import { computed, ref } from "vue";
import { House, RotateCcw, Share2 } from "lucide-vue-next";
import type { ResultCardModel } from "flavor-data/product-vector-v1/view";
import { home, locale, restart } from "../store";

const props = defineProps<{ model: ResultCardModel }>();
const open = ref(false);
const labels = computed(() => (locale.value === "zh-CN" ? { home: "首页", again: "重新体验", share: "分享" } : { home: "Home", again: "Start over", share: "Share" }));
const main = computed(() => props.model.picked.slice(0, 3));
const rest = computed(() => props.model.picked.slice(3));
const DIM_COLORS: Record<string, string> = {
  acidity: "#F2C24E", sweetness: "#F5B0C6", body: "#9B7B5D", floral: "#7268C9", fruity: "#EE8F70", nutty_chocolate: "#B97C4E",
  fermented_winey: "#8C4A4C", bitter_roasted: "#1E1C1A", spice: "#DA8A80", herbal_green: "#6FA85A", woody_earthy: "#2F7A4C", defect: "#7F90B8",
};
const bar = computed(() => props.model.pickedDimensions.map((d) => DIM_COLORS[d] ?? "#999"));
async function share(text: string) {
  if (typeof navigator === "undefined") return;
  const nav = navigator as Navigator & { share?: (d: { text: string }) => Promise<void> };
  if (typeof nav.share === "function") await nav.share({ text }).catch(() => undefined);
  else if (nav.clipboard) await nav.clipboard.writeText(text).catch(() => undefined);
}
</script>

<template>
  <section class="h-full flex flex-col text-cream fold-card" data-component="FinalAttributionCard" :data-corrected="model.corrected">
    <div class="px-6 pt-7 flex flex-col gap-2">
      <p class="text-[11px] tracking-[0.2em] opacity-60">{{ model.heading }}<span v-if="model.corrected"> · {{ locale === 'zh-CN' ? '精修' : 'refined' }}</span></p>
      <h2 class="text-[22px] opacity-90 mt-1" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">［{{ model.title }}］</h2>
      <p class="text-[30px] leading-[1.15] font-semibold mt-2" data-words="main">{{ main.join("  │  ") }}</p>
      <p class="text-lg opacity-75 mt-1" data-words="secondary">{{ rest.join("  ·  ") }}</p>
      <div class="flex h-1.5 rounded-full overflow-hidden mt-4" aria-hidden="true">
        <span v-for="(c, i) in bar" :key="i" class="flex-1" :style="{ backgroundColor: c }" />
      </div>
    </div>
    <div class="mx-6 mt-5 flex-1 min-h-0 overflow-y-auto border-t border-cream/20 pt-3">
      <button type="button" class="w-full text-left text-[12px] tracking-[0.2em] opacity-70 py-1" :aria-expanded="open" @click="open = !open">
        {{ model.scienceHeading }}<span class="float-right">{{ open ? '–' : '+' }}</span>
      </button>
      <div class="fold" :data-open="open">
        <div>
          <ul class="mt-3 space-y-5 text-[15px] leading-relaxed">
            <li v-for="line in model.science" :key="line.citationRef + line.text" :data-evidence-state="line.evidenceState">
              <p class="text-[11px] tracking-[0.2em] opacity-60 mb-1">{{ line.label }}</p>
              <p class="opacity-95">{{ line.text }}</p>
              <p v-if="line.citation" class="text-xs opacity-60 mt-1 italic">{{ line.citation }}</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
    <nav class="px-6 pt-4 pb-5 flex items-center justify-between" :aria-label="locale === 'zh-CN' ? '操作' : 'Actions'">
      <button type="button" class="rounded-full border border-cream/35 p-3.5" :aria-label="labels.home" :title="labels.home" @click="home"><House :size="20" :stroke-width="1.75" /></button>
      <button type="button" class="rounded-full border border-cream/35 p-3.5" :aria-label="labels.again" :title="labels.again" @click="restart"><RotateCcw :size="20" :stroke-width="1.75" /></button>
      <button type="button" class="rounded-full bg-cream text-ink p-3.5" :aria-label="labels.share" :title="labels.share" @click="share(model.shareText)"><Share2 :size="20" :stroke-width="1.75" /></button>
    </nav>
  </section>
</template>

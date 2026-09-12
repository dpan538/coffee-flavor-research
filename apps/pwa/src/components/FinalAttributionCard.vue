<script setup lang="ts">
// Final screen: the flavor card (the product object) on the navy band, then "关于这段描述" folded, then the icon bar.
import { computed, ref } from "vue";
import { House, RotateCcw, Share2 } from "lucide-vue-next";
import type { ResultCardModel } from "flavor-data/product-vector-v1/view";
import FlavorCard from "./FlavorCard.vue";
import { shareCardPng } from "../exportCard";
import { home, locale, restart } from "../store";

const props = defineProps<{ model: ResultCardModel }>();
const open = ref(false);
const labels = computed(() => (locale.value === "zh-CN" ? { home: "首页", again: "重新体验", share: "分享", reference: "参考风味" } : { home: "Home", again: "Start over", share: "Share", reference: "Reference" }));
const eyebrow = computed(() => `${props.model.heading}${props.model.corrected ? ` · ${locale.value === "zh-CN" ? "已确认" : "confirmed"}` : ""}`);
const busy = ref(false);
/** the card as a 1200 × 1200 PNG through the share sheet, or saved; the text share is the fallback */
async function share(text: string) {
  if (typeof navigator === "undefined" || busy.value) return;
  busy.value = true;
  try {
    await shareCardPng(props.model, locale.value);
  } catch {
    const nav = navigator as Navigator & { share?: (d: { text: string }) => Promise<void> };
    if (typeof nav.share === "function") await nav.share({ text }).catch(() => undefined);
    else if (nav.clipboard) await nav.clipboard.writeText(text).catch(() => undefined);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section class="h-full flex flex-col text-cream fold-card" data-component="FinalAttributionCard" :data-corrected="model.corrected">
    <div class="flex-1 min-h-0 overflow-y-auto px-4 pt-4 pb-2">
      <FlavorCard :cup="model.cupInfo" :words="model.picked" :dimensions="model.pickedDimensions" :reference="`${labels.reference} · ${model.title}`" :eyebrow="eyebrow" />
      <div class="mx-2 mt-4 border-t border-cream/20 pt-1">
        <button type="button" class="fold-toggle min-h-[58px] text-[15px] tracking-[0.14em] opacity-90" :aria-expanded="open" @click="open = !open">
          <span>{{ model.scienceHeading }}</span><span class="text-3xl leading-none">{{ open ? '–' : '+' }}</span>
        </button>
        <div class="fold" :data-open="open">
          <div>
            <ul class="mt-2 space-y-5 text-[15px] leading-relaxed pb-3">
              <li v-for="line in model.science" :key="line.citationRef + line.text" :data-evidence-state="line.evidenceState">
                <p class="text-[11px] tracking-[0.2em] opacity-60 mb-1">{{ line.label }}</p>
                <p class="opacity-95">{{ line.text }}</p>
                <p v-if="line.citation" class="text-xs opacity-60 mt-1 italic">{{ line.citation }}</p>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <nav class="px-6 pt-2 pb-10 flex items-center justify-between" :aria-label="locale === 'zh-CN' ? '操作' : 'Actions'">
      <button type="button" class="rounded-2xl border border-cream/35 w-14 h-14 inline-flex items-center justify-center" :aria-label="labels.home" :title="labels.home" @click="home"><House :size="22" :stroke-width="1.75" /></button>
      <button type="button" class="rounded-2xl border border-cream/35 w-14 h-14 inline-flex items-center justify-center" :aria-label="labels.again" :title="labels.again" @click="restart"><RotateCcw :size="22" :stroke-width="1.75" /></button>
      <button type="button" class="rounded-2xl bg-cream text-ink w-14 h-14 inline-flex items-center justify-center disabled:opacity-60" :disabled="busy" :aria-label="labels.share" :title="labels.share" @click="share(model.shareText)"><Share2 :size="22" :stroke-width="1.75" /></button>
    </nav>
  </section>
</template>

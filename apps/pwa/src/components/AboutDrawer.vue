<script setup lang="ts">
// About — Sensory Physics & Methodology. Mobile sheet on paper: the data visual first, then three folded sections
// (methodology summary open, details folded; literature + licences folded; lexicon & local autonomy folded). Text only.
import { computed, ref } from "vue";
import { aboutFooter, aboutStats, aboutTitle } from "flavor-data/product-vector-v1/about";
import FlavorBurst from "./FlavorBurst.vue";
import { X } from "lucide-vue-next";
import { about, aboutOpen, locale } from "../store";

const title = computed(() => aboutTitle(locale.value));
const stats = computed(() => aboutStats(locale.value));
const maxStat = computed(() => Math.max(...stats.value.map((s) => s.value)));
const fmt = (n: number) => n.toLocaleString(locale.value === "zh-CN" ? "zh-CN" : "en-US");
const colors = ["#7268C9", "#2F7A4C", "#B97C4E", "#5FAEE8", "#EE8F70", "#86CBB4", "#DA8A80", "#F2C24E"];
const closeLabel = computed(() => (locale.value === "zh-CN" ? "收起" : "Collapse"));
const openSection = ref("");
const detailsLabel = computed(() => (locale.value === "zh-CN" ? "展开细节" : "Details"));
</script>

<template>
  <aside class="fixed inset-0 z-40 overflow-y-auto bg-paper text-ink fold-card" role="dialog" aria-modal="true" data-component="AboutDrawer">
    <div class="sticky top-0 bg-paper/95 backdrop-blur px-5 py-4 flex items-start justify-between">
      <div class="leading-[0.9]"><span class="display block text-[26px]">flavor</span><span class="display block text-[26px] text-violet">words</span></div>
      <button type="button" class="rounded-full border border-ink/20 p-2" :aria-label="locale === 'zh-CN' ? '关闭' : 'Close'" @click="aboutOpen = false"><X :size="18" :stroke-width="1.75" /></button>
    </div>

    <section class="px-5 pt-4">
      <h1 class="text-[30px]" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">{{ title.title }}</h1>
      <p class="text-sm text-muted mt-1">{{ title.subtitle }}</p>
    </section>

    <!-- the data visual: what this engine was built from — a radial spectrum of the profiles, then the counts -->
    <section class="px-5 pt-6" data-section="stats">
      <FlavorBurst />
      <p class="text-xs text-muted mt-2 mb-5">{{ locale === 'zh-CN' ? '每一道光谱是一个风味画像：长度按其咖啡数的对数刻度，色段是它在 12 个维度上的重心' : 'each ray is a flavor profile: length on a log scale of its coffees, colour segments its weight across the 12 dimensions' }}</p>
      <ul class="space-y-3">
        <li v-for="(s, i) in stats" :key="s.key" class="flex flex-col gap-1">
          <div class="flex items-baseline justify-between">
            <span class="display-zh text-2xl">{{ fmt(s.value) }}</span>
            <span class="text-sm text-muted">{{ s.label }}</span>
          </div>
          <div class="h-2 rounded-full bg-ink/10 overflow-hidden">
            <div class="h-full rounded-full" :style="{ width: `${Math.max(3, Math.round((Math.log10(s.value + 1) / Math.log10(maxStat + 1)) * 100))}%`, backgroundColor: colors[i % colors.length] }" />
          </div>
        </li>
      </ul>
      <p class="text-xs text-muted mt-2">{{ locale === 'zh-CN' ? '条形按对数刻度绘制' : 'bars on a log scale' }}</p>
    </section>

    <section v-for="(section, i) in about.sections" :key="section.id" class="px-5 pt-8" :data-section="section.id">
      <h2 class="text-[22px] mb-2" :class="locale === 'zh-CN' ? 'display-zh' : 'display'" :style="{ color: colors[i] }">{{ section.title }}</h2>
      <p class="leading-relaxed">{{ section.summary }}</p>
      <button type="button" class="chip mt-3 !py-1.5 !px-3 text-sm" :aria-expanded="openSection === section.id" @click="openSection = openSection === section.id ? '' : section.id">{{ openSection === section.id ? closeLabel : detailsLabel }}</button>
      <div class="fold" :data-open="openSection === section.id">
        <div>
          <div class="mt-4 space-y-4">
            <article v-for="block in section.blocks" :key="block.title" class="rounded-2xl bg-cream p-4">
              <h3 class="font-medium mb-1">{{ block.title }}</h3>
              <p class="text-sm leading-relaxed whitespace-pre-line">{{ block.body }}</p>
            </article>
          </div>
        </div>
      </div>
    </section>
    <p class="px-5 pt-8 pb-10 text-xs text-muted leading-relaxed">{{ aboutFooter(locale) }}</p>
  </aside>
</template>

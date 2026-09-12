<script setup lang="ts">
// About: our approach (why, who) → provenance flow (where the data came from, what it became) → sensory physics
// & geometric attribution (summary, details folded) → the evidence chain (folded). Mobile sheet on white.
import { computed, ref } from "vue";
import { X } from "lucide-vue-next";
import { aboutApproach, aboutEvidence, aboutStats, aboutTitle } from "flavor-data/product-vector-v1/about";
import FlavorBurst from "./FlavorBurst.vue";
import ProvenanceFlow from "./ProvenanceFlow.vue";
import { about, aboutOpen, locale } from "../store";

const approach = computed(() => aboutApproach(locale.value));
const title = computed(() => aboutTitle(locale.value));
const stats = computed(() => aboutStats(locale.value).filter((s) => ["assertions", "coffees", "edges", "consumers"].includes(s.key)));
const evidence = computed(() => aboutEvidence(locale.value));
const fmt = (n: number) => n.toLocaleString(locale.value === "zh-CN" ? "zh-CN" : "en-US");
const openSection = ref("");
const zh = computed(() => locale.value === "zh-CN");
const t = computed(() => (zh.value ? { details: "展开", collapse: "收起", flow: "数据从哪来，变成了什么", flowNote: "左：来源评审族与咖啡数；右：12 个维度；带宽是该来源在该维度上的质量", spectrum: "十六个风味画像", spectrumNote: "每一道射线是一个画像，长度按咖啡数的对数刻度，刻度色是它在各维度上的重心", evidence: "证据链", gives: "给引擎的是" } : { details: "Details", collapse: "Collapse", flow: "Where the data came from, what it became", flowNote: "left: source panels and their coffees; right: the 12 dimensions; ribbon width is that source's mass on that dimension", spectrum: "Sixteen flavor profiles", spectrumNote: "each ray is a profile, length on a log scale of its coffees, tick colours its weight across the dimensions", evidence: "Evidence chain", gives: "gives the engine" }));
</script>

<template>
  <aside class="fixed inset-0 z-40 overflow-y-auto bg-paper text-ink fold-card safe-top safe-bottom" role="dialog" aria-modal="true" data-component="AboutDrawer">
    <div class="sticky top-0 z-10 bg-paper/95 backdrop-blur px-5 py-4 flex items-start justify-between">
      <div class="leading-[0.9]"><span class="display block text-[26px]">flavor</span><span class="display block text-[26px] text-violet">words</span></div>
      <button type="button" class="rounded-full border border-ink/20 p-2" :aria-label="zh ? '关闭' : 'Close'" @click="aboutOpen = false"><X :size="18" :stroke-width="1.75" /></button>
    </div>

    <!-- our approach -->
    <section class="px-5 pt-4" data-section="approach">
      <p class="text-[11px] tracking-[0.22em] text-muted uppercase">{{ approach.eyebrow }}</p>
      <h1 class="text-[30px] mt-2" :class="zh ? 'display-zh' : 'display'">{{ approach.title }}</h1>
      <p class="text-sm text-muted mt-2">{{ approach.author }}</p>
      <div class="mt-5 border-l-2 border-violet pl-4 space-y-2">
        <p v-for="(p, i) in approach.problem" :key="i" class="leading-relaxed text-[15px]">{{ p }}</p>
      </div>
      <p v-for="(p, i) in approach.paragraphs" :key="'a' + i" class="leading-relaxed mt-4">{{ p }}</p>
    </section>

    <!-- the numbers, then where they came from -->
    <section class="px-5 pt-8" data-section="data">
      <ul class="grid grid-cols-2 gap-x-4 gap-y-3">
        <li v-for="s in stats" :key="s.key">
          <p class="display-zh text-[26px] leading-none">{{ fmt(s.value) }}</p>
          <p class="text-xs text-muted mt-1">{{ s.label }}</p>
        </li>
      </ul>
      <h2 class="text-[15px] font-medium mt-8">{{ t.flow }}</h2>
      <ProvenanceFlow class="mt-3" />
      <p class="text-xs text-muted mt-1">{{ t.flowNote }}</p>
      <h2 class="text-[15px] font-medium mt-8">{{ t.spectrum }}</h2>
      <FlavorBurst class="mt-3" />
      <p class="text-xs text-muted mt-1">{{ t.spectrumNote }}</p>
    </section>

    <!-- sensory physics & geometric attribution -->
    <section v-for="section in about.sections.filter((s) => s.id === 'methodology')" :key="section.id" class="px-5 pt-10" :data-section="section.id">
      <p class="text-[11px] tracking-[0.22em] text-muted uppercase">{{ title.subtitle }}</p>
      <h2 class="text-[24px] mt-2" :class="zh ? 'display-zh' : 'display'">{{ section.title }}</h2>
      <p class="leading-relaxed mt-3">{{ section.summary }}</p>
      <button type="button" class="chip mt-3 !py-1.5 !px-3 text-sm" :aria-expanded="openSection === section.id" @click="openSection = openSection === section.id ? '' : section.id">{{ openSection === section.id ? t.collapse : t.details }}</button>
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

    <!-- evidence chain -->
    <section class="px-5 pt-10 pb-12" data-section="evidence">
      <h2 class="text-[24px]" :class="zh ? 'display-zh' : 'display'">{{ t.evidence }}</h2>
      <ol class="mt-4 relative">
        <li v-for="(e, i) in evidence" :key="e.id" class="relative pl-6 pb-5">
          <span class="absolute left-0 top-1.5 w-3 h-3 rounded-full" :style="{ backgroundColor: e.color }" />
          <span v-if="i < evidence.length - 1" class="absolute left-[5px] top-5 bottom-0 w-px bg-ink/15" />
          <p class="font-medium leading-snug">{{ e.title }}</p>
          <p class="text-sm text-muted mt-0.5">{{ t.gives }}：{{ e.gives }}</p>
          <button type="button" class="text-xs text-muted underline underline-offset-4 mt-1" :aria-expanded="openSection === e.id" @click="openSection = openSection === e.id ? '' : e.id">{{ openSection === e.id ? t.collapse : t.details }}</button>
          <div class="fold" :data-open="openSection === e.id">
            <div>
              <p class="text-xs text-muted mt-2 break-all">{{ e.locator }}</p>
              <p class="text-xs text-muted mt-1">{{ e.licence }}</p>
            </div>
          </div>
        </li>
      </ol>
    </section>
  </aside>
</template>

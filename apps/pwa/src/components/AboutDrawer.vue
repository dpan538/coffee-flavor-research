<script setup lang="ts">
// About, in the owner's reading order (copy review 2026-09-12): what it is for → a sample card → the author and
// the work → the scope of the material (with units) → the two data visuals → how a card is made (folded) →
// technical notes (folded) → sources ("how this project uses it"). Mobile sheet on white.
import { computed, ref } from "vue";
import { X } from "lucide-vue-next";
import { aboutApproach, aboutAuthor, aboutEvidence, aboutExample, aboutScope, aboutSections } from "flavor-data/product-vector-v1/about";
import FlavorBurst from "./FlavorBurst.vue";
import ProvenanceFlow from "./ProvenanceFlow.vue";
import { aboutOpen, locale } from "../store";

const approach = computed(() => aboutApproach(locale.value));
const example = computed(() => aboutExample(locale.value));
const author = computed(() => aboutAuthor(locale.value));
const scope = computed(() => aboutScope(locale.value));
const sections = computed(() => aboutSections(locale.value));
const evidence = computed(() => aboutEvidence(locale.value));
const fmt = (n: number) => n.toLocaleString(locale.value === "zh-CN" ? "zh-CN" : "en-US");
const openSection = ref("");
const zh = computed(() => locale.value === "zh-CN");
const t = computed(() =>
  zh.value
    ? { details: "展开", collapse: "收起", flow: "评审资料如何用于风味描述", flowNote: "左：来源评审族与记录数；右：12 类风味特征；带宽是该来源在该特征上的累计权重（每条记录的风味词投影到该特征后求和）", spectrum: "16 组参考风味", spectrumNote: "本项目从所用资料中整理的分组，不是咖啡的全部分类；每条射线一组，长度按记录数的对数刻度，刻度色是它主要的风味特征", sources: "资料来源", uses: "本项目如何使用这份资料", pending: "条待复核，未上线" }
    : { details: "Details", collapse: "Collapse", flow: "How the review material feeds the descriptions", flowNote: "left: source panels and their record counts; right: the 12 flavor features; ribbon width is that source's cumulative weight on that feature (each record's flavor words projected onto the feature, summed)", spectrum: "16 reference profiles", spectrumNote: "groups organised from the material used here, not a taxonomy of all coffee; one ray per group, length on a log scale of its records, tick colours its main flavor features", sources: "Sources", uses: "How this project uses it", pending: "held back until re-verified" },
);
const mainWords = computed(() => example.value.words.slice(0, 3));
const restWords = computed(() => example.value.words.slice(3));
</script>

<template>
  <aside class="fixed inset-0 z-40 overflow-y-auto bg-paper text-ink fold-card safe-top safe-bottom" role="dialog" aria-modal="true" data-component="AboutDrawer">
    <div class="sticky top-0 z-10 bg-paper/95 backdrop-blur px-5 py-4 flex items-start justify-between">
      <div class="leading-[0.9]"><span class="display block text-[26px]">flavor</span><span class="display block text-[26px] text-violet">words</span></div>
      <button type="button" class="rounded-full border border-ink/20 p-2" :aria-label="zh ? '关闭' : 'Close'" @click="aboutOpen = false"><X :size="18" :stroke-width="1.75" /></button>
    </div>

    <!-- what it is for -->
    <section class="px-5 pt-4" data-section="approach">
      <p class="text-[11px] tracking-[0.22em] text-muted uppercase">{{ approach.eyebrow }}</p>
      <h1 class="text-[30px] mt-2" :class="zh ? 'display-zh' : 'display'">{{ approach.title }}</h1>
      <p v-for="(p, i) in approach.intro" :key="'i' + i" class="leading-relaxed mt-4">{{ p }}</p>
    </section>

    <!-- a sample card, marked as a sample -->
    <section class="px-5 pt-8" data-section="example">
      <div class="rounded-2xl bg-leaf text-cream px-5 pt-5 pb-6">
        <p class="text-[11px] tracking-[0.2em] opacity-60">{{ example.eyebrow }}</p>
        <h2 class="text-[20px] opacity-90 mt-1" :class="zh ? 'display-zh' : 'display'">［{{ example.title }}］</h2>
        <p class="text-[24px] leading-[1.2] font-semibold mt-2">{{ mainWords.join("  │  ") }}</p>
        <p class="text-base opacity-75 mt-1">{{ restWords.join("  ·  ") }}</p>
      </div>
      <p class="text-xs text-muted mt-2">{{ example.note }}</p>
      <h2 class="text-[17px] font-medium mt-8">{{ approach.referenceTitle }}</h2>
      <p v-for="(p, i) in approach.reference" :key="'r' + i" class="leading-relaxed mt-3">{{ p }}</p>
    </section>

    <!-- the author and the work -->
    <section class="px-5 pt-10" data-section="author">
      <p class="text-[11px] tracking-[0.22em] text-muted uppercase">{{ author.eyebrow }}</p>
      <h2 class="text-[24px] mt-2" :class="zh ? 'display-zh' : 'display'">{{ author.name }}</h2>
      <p v-for="(p, i) in author.paragraphs" :key="'a' + i" class="leading-relaxed mt-4">{{ p }}</p>
      <ul class="mt-6 space-y-4">
        <li v-for="c in author.contributions" :key="c.label" class="flex gap-4">
          <p class="display-zh text-[28px] leading-none w-16 shrink-0">{{ c.value }}<span class="text-sm ml-0.5">{{ c.unit }}</span></p>
          <div>
            <p class="font-medium leading-snug">{{ c.label }}</p>
            <p class="text-sm text-muted mt-0.5 leading-relaxed">{{ c.use }}</p>
          </div>
        </li>
      </ul>
    </section>

    <!-- the scope of the material, with units -->
    <section class="px-5 pt-10" data-section="scope">
      <h2 class="text-[24px]" :class="zh ? 'display-zh' : 'display'">{{ scope.title }}</h2>
      <ul class="mt-4 divide-y divide-ink/10">
        <li v-for="s in scope.items" :key="s.key" class="py-3 flex gap-4 items-baseline">
          <p class="display-zh text-[22px] leading-none w-24 shrink-0 tabular-nums">{{ fmt(s.value) }}<span class="text-xs ml-0.5">{{ s.unit }}</span></p>
          <div>
            <p class="font-medium leading-snug">{{ s.label }}</p>
            <p class="text-xs text-muted mt-0.5 leading-relaxed">{{ s.note }}</p>
          </div>
        </li>
      </ul>
      <p class="text-xs text-muted mt-2">{{ scope.footnote }}</p>
      <h3 class="text-[15px] font-medium mt-8">{{ t.flow }}</h3>
      <ProvenanceFlow class="mt-3" />
      <p class="text-xs text-muted mt-1">{{ t.flowNote }}</p>
      <h3 class="text-[15px] font-medium mt-8">{{ t.spectrum }}</h3>
      <FlavorBurst class="mt-3" />
      <p class="text-xs text-muted mt-1">{{ t.spectrumNote }}</p>
    </section>

    <!-- how a card is made, then the technical notes; both folded -->
    <section v-for="section in sections.filter((s) => s.id !== 'literature')" :key="section.id" class="px-5 pt-10" :data-section="section.id">
      <h2 class="text-[24px]" :class="zh ? 'display-zh' : 'display'">{{ section.title }}</h2>
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

    <!-- sources: what this project takes from each -->
    <section class="px-5 pt-10 pb-12" data-section="evidence">
      <h2 class="text-[24px]" :class="zh ? 'display-zh' : 'display'">{{ t.sources }}</h2>
      <ol class="mt-4 relative">
        <li v-for="(e, i) in evidence" :key="e.id" class="relative pl-6 pb-5">
          <span class="absolute left-0 top-1.5 w-3 h-3 rounded-full" :style="{ backgroundColor: e.color }" />
          <span v-if="i < evidence.length - 1" class="absolute left-[5px] top-5 bottom-0 w-px bg-ink/15" />
          <p class="font-medium leading-snug">{{ e.title }}</p>
          <p class="text-sm text-muted mt-0.5">{{ t.uses }}：{{ e.gives }}</p>
          <p v-if="e.claimsPendingReview" class="text-xs text-muted mt-0.5">{{ e.claimsPendingReview }} {{ t.pending }}</p>
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

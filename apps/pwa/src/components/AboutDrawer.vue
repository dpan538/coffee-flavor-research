<script setup lang="ts">
// About as four pages (owner, 2026-09-12): 1 what it is for + a sample card · 2 the author, the work, three folded
// entries · 3 the provenance flow, drawn by scrolling · 4 the sixteen reference profiles, drawn by scrolling · then
// the sources. The two visuals sit in tall tracks with a sticky panel; GSAP ScrollTrigger (scroller = this sheet)
// turns the scroll position into a 0–1 progress the SVGs draw from, and reveals the text pages as they arrive.
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { X } from "lucide-vue-next";
import { aboutApproach, aboutAuthor, aboutEvidence, aboutExample, aboutSections } from "flavor-data/product-vector-v1/about";
import { productVectorBundle } from "flavor-data/product-vector-v1";
import FlavorBurst from "./FlavorBurst.vue";
import ProvenanceFlow from "./ProvenanceFlow.vue";
import { aboutOpen, locale } from "../store";

gsap.registerPlugin(ScrollTrigger);

const approach = computed(() => aboutApproach(locale.value));
const example = computed(() => aboutExample(locale.value));
const author = computed(() => aboutAuthor(locale.value));
const sections = computed(() => aboutSections(locale.value));
const evidence = computed(() => aboutEvidence(locale.value));
const zh = computed(() => locale.value === "zh-CN");
const openSection = ref("");
const fmt = (n: number) => n.toLocaleString(locale.value === "zh-CN" ? "zh-CN" : "en-US");
const grouped = (productVectorBundle.corpus_facts as { usable_coffee_vectors: number }).usable_coffee_vectors;
const t = computed(() =>
  zh.value
    ? { details: "展开", collapse: "收起", close: "关闭", scroll: "向下滑动", flowTitle: "评审资料如何用于风味描述", flowNote: "左：来源评审族与记录数；右：12 类风味特征；带宽是该来源在该特征上的累计权重。", flowCount: "条记录进入参考风味分组", burstTitle: "本项目整理的 16 组参考风味", burstNote: "每条射线一组，长度按记录数的对数刻度，刻度色是它主要的风味特征。", sources: "资料来源", uses: "本项目的使用", terms: "来源条款" }
    : { details: "Details", collapse: "Collapse", close: "Close", scroll: "Scroll", flowTitle: "From coffee reviews to flavor descriptions", flowNote: "left: source panels and their record counts; right: the 12 flavor features; ribbon width is that source's cumulative weight on that feature.", flowCount: "records enter the reference-profile grouping", burstTitle: "16 reference profiles organised by this project", burstNote: "one ray per group, length on a log scale of its records, tick colours its main flavor features.", sources: "Sources", uses: "Use in this project", terms: "Source terms" },
);
const mainWords = computed(() => example.value.words.slice(0, 3));
const restWords = computed(() => example.value.words.slice(3));

// scroll-driven drawing
const scroller = ref<HTMLElement | null>(null);
const flowTrack = ref<HTMLElement | null>(null);
const burstTrack = ref<HTMLElement | null>(null);
const flowProgress = ref(0);
const burstProgress = ref(0);
const reduced = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const flowCount = computed(() => Math.round(grouped * Math.max(0, Math.min(1, flowProgress.value / 0.8))));

function toggle(id: string) {
  openSection.value = openSection.value === id ? "" : id;
  setTimeout(() => ScrollTrigger.refresh(), 420);
}

onMounted(async () => {
  await nextTick();
  if (reduced || !scroller.value) {
    flowProgress.value = 1;
    burstProgress.value = 1;
    return;
  }
  const scrollerEl = scroller.value;
  ScrollTrigger.create({ trigger: flowTrack.value!, scroller: scrollerEl, start: "top top", end: "bottom bottom", scrub: 0.6, onUpdate: (self) => (flowProgress.value = self.progress) });
  ScrollTrigger.create({ trigger: burstTrack.value!, scroller: scrollerEl, start: "top top", end: "bottom bottom", scrub: 0.6, onUpdate: (self) => (burstProgress.value = self.progress) });
  scrollerEl.querySelectorAll<HTMLElement>("[data-reveal]").forEach((el) => {
    gsap.from(Array.from(el.children), { y: 28, opacity: 0, duration: 0.75, ease: "power3.out", stagger: 0.07, scrollTrigger: { trigger: el, scroller: scrollerEl, start: "top 78%", once: true } });
  });
  gsap.from(scrollerEl.querySelectorAll("[data-page='1'] > *"), { y: 24, opacity: 0, duration: 0.7, ease: "power3.out", stagger: 0.08, delay: 0.1 });
});
onBeforeUnmount(() => {
  ScrollTrigger.getAll().forEach((s) => s.kill());
});
</script>

<template>
  <aside ref="scroller" class="fixed inset-0 z-40 overflow-y-auto bg-paper text-ink fold-card safe-top safe-bottom" role="dialog" aria-modal="true" data-component="AboutDrawer">
    <div class="sticky top-0 z-10 bg-paper/95 backdrop-blur px-5 py-3 flex items-center justify-between">
      <div class="leading-[0.9]"><span class="display block text-[22px]">flavor</span><span class="display block text-[22px] text-violet">words</span></div>
      <button type="button" class="icon-btn" :aria-label="t.close" @click="aboutOpen = false"><X :size="22" :stroke-width="1.75" /></button>
    </div>

    <!-- page 1: what it is for, a sample card -->
    <section class="min-h-[calc(100dvh-72px)] px-5 pt-4 pb-10 flex flex-col" data-page="1" data-section="approach">
      <p class="text-[11px] tracking-[0.22em] text-muted uppercase">{{ approach.eyebrow }}</p>
      <h1 class="text-[36px] mt-2" :class="zh ? 'display-zh' : 'display'">{{ approach.title }}</h1>
      <p v-for="(p, i) in approach.intro" :key="'i' + i" class="leading-relaxed text-[17px] mt-4">{{ p }}</p>
      <div class="rounded-3xl bg-navy text-cream px-5 pt-5 pb-6 mt-8" data-section="example">
        <p class="text-[11px] tracking-[0.2em] opacity-60">{{ example.eyebrow }}</p>
        <h2 class="text-[20px] opacity-90 mt-1" :class="zh ? 'display-zh' : 'display'">［{{ example.title }}］</h2>
        <p class="text-[24px] leading-[1.2] font-semibold mt-2">{{ mainWords.join("  │  ") }}</p>
        <p class="text-base opacity-75 mt-1">{{ restWords.join("  ·  ") }}</p>
      </div>
      <p class="text-xs text-muted mt-auto pt-8 tracking-widest">↓ {{ t.scroll }}</p>
    </section>

    <!-- page 2: the author and the work; three folded entries -->
    <section class="min-h-[100dvh] px-5 pt-10 pb-10" data-page="2" data-section="author" data-reveal>
      <p class="text-[11px] tracking-[0.22em] text-muted uppercase">{{ author.eyebrow }}</p>
      <h2 class="text-[30px] mt-2" :class="zh ? 'display-zh' : 'display'">{{ author.name }}</h2>
      <p v-for="(p, i) in author.paragraphs" :key="'a' + i" class="leading-relaxed text-[17px] mt-4">{{ p }}</p>
      <ul class="mt-6 space-y-4">
        <li v-for="c in author.contributions" :key="c.label" class="flex gap-4 items-baseline">
          <p class="display-zh text-[30px] leading-none w-[72px] shrink-0 tabular-nums">{{ c.value }}<span class="text-sm ml-0.5">{{ c.unit }}</span></p>
          <div>
            <p class="font-medium leading-snug">{{ c.label }}</p>
            <p class="text-sm text-muted mt-0.5 leading-relaxed">{{ c.use }}</p>
          </div>
        </li>
      </ul>
      <div class="mt-8 divide-y divide-ink/10 border-y border-ink/10">
        <div v-for="section in sections" :key="section.id" :data-section="section.id">
          <button type="button" class="fold-toggle py-4" :aria-expanded="openSection === section.id" @click="toggle(section.id)">
            <span>
              <span class="block text-[18px] font-medium">{{ section.title }}</span>
              <span class="block text-sm text-muted mt-0.5 leading-relaxed">{{ section.summary }}</span>
            </span>
            <span class="text-2xl leading-none ml-4 shrink-0">{{ openSection === section.id ? '–' : '+' }}</span>
          </button>
          <div class="fold" :data-open="openSection === section.id">
            <div>
              <div class="pb-5 space-y-3">
                <article v-for="block in section.blocks" :key="block.title" class="rounded-2xl bg-cream p-4">
                  <h3 class="font-medium mb-1">{{ block.title }}</h3>
                  <p class="text-sm leading-relaxed whitespace-pre-line">{{ block.body }}</p>
                </article>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- page 3: the provenance flow, drawn while scrolling -->
    <section ref="flowTrack" class="relative h-[320dvh]" data-page="3" data-section="flow">
      <div class="sticky top-0 h-[100dvh] px-5 pt-[84px] pb-10 flex flex-col justify-center">
        <h2 class="text-[24px]" :class="zh ? 'display-zh' : 'display'">{{ t.flowTitle }}</h2>
        <p class="display-zh text-[34px] leading-none mt-3 tabular-nums">{{ fmt(flowCount) }}<span class="text-sm font-normal ml-2 text-muted">{{ t.flowCount }}</span></p>
        <ProvenanceFlow class="mt-4" :progress="flowProgress" />
        <p class="text-xs text-muted mt-2 transition-opacity duration-500" :style="{ opacity: flowProgress > 0.85 ? 1 : 0 }">{{ t.flowNote }}</p>
      </div>
    </section>

    <!-- page 4: the sixteen reference profiles, drawn while scrolling -->
    <section ref="burstTrack" class="relative h-[320dvh]" data-page="4" data-section="spectrum">
      <div class="sticky top-0 h-[100dvh] px-5 pt-[84px] pb-10 flex flex-col justify-center">
        <h2 class="text-[24px]" :class="zh ? 'display-zh' : 'display'">{{ t.burstTitle }}</h2>
        <FlavorBurst class="mt-4" :progress="burstProgress" />
        <p class="text-xs text-muted mt-2 transition-opacity duration-500" :style="{ opacity: burstProgress > 0.9 ? 1 : 0 }">{{ t.burstNote }}</p>
      </div>
    </section>

    <!-- sources in use -->
    <section class="px-5 pt-8 pb-16" data-page="5" data-section="evidence" data-reveal>
      <h2 class="text-[24px]" :class="zh ? 'display-zh' : 'display'">{{ t.sources }}</h2>
      <ol class="mt-4 relative">
        <li v-for="(e, i) in evidence" :key="e.id" class="relative pl-6 pb-5">
          <span class="absolute left-0 top-2 w-3 h-3 rounded-full" :style="{ backgroundColor: e.color }" />
          <span v-if="i < evidence.length - 1" class="absolute left-[5px] top-6 bottom-0 w-px bg-ink/15" />
          <p class="font-medium leading-snug text-[17px]">{{ e.title }}</p>
          <p class="text-sm text-muted mt-1">{{ e.gives }}</p>
          <button type="button" class="chip mt-2 !min-h-[44px] !py-2 text-sm" :aria-expanded="openSection === e.id" @click="toggle(e.id)">{{ openSection === e.id ? t.collapse : t.details }}</button>
          <div class="fold" :data-open="openSection === e.id">
            <div>
              <p class="text-xs text-muted mt-3 break-all">{{ e.locator }}</p>
              <p class="text-xs text-muted mt-1"><span class="text-ink">{{ t.terms }}：</span>{{ e.terms }}</p>
              <p class="text-xs text-muted mt-1"><span class="text-ink">{{ t.uses }}：</span>{{ e.use }}</p>
            </div>
          </div>
        </li>
      </ol>
    </section>
  </aside>
</template>

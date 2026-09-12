<script setup lang="ts">
// About as pages (owner, 2026-09-12): 1 从品味，到表达 — what it is for, the mission, the sample card · 2 the
// column-and-trunk poster (black page, drawn by scrolling) · 3 the profile network (black page, drawn by
// scrolling) · 4 the author and three folded entries (owner: after the two visuals) · 5 sources. The two visuals sit in tall tracks with a sticky panel;
// GSAP ScrollTrigger (scroller = this sheet) turns scroll into a 0–1 progress the SVGs draw from.
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { X } from "lucide-vue-next";
import { aboutApproach, aboutAuthor, aboutCitations, aboutEvidence, aboutSections } from "flavor-data/product-vector-v1/about";
import BrandGlyphs from "./BrandGlyphs.vue";
import ProfileNetwork from "./ProfileNetwork.vue";
import SourceColumns from "./SourceColumns.vue";
import { aboutOpen, locale } from "../store";

gsap.registerPlugin(ScrollTrigger);

const approach = computed(() => aboutApproach(locale.value));
const author = computed(() => aboutAuthor(locale.value));
const sections = computed(() => aboutSections(locale.value));
const evidence = computed(() => aboutEvidence(locale.value));
const citations = computed(() => aboutCitations(locale.value));
const roleOf = (id: string) => citations.value.find((c) => c.id === id)?.role ?? "";
function toTop() {
  scroller.value?.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
}
const zh = computed(() => locale.value === "zh-CN");
const openSection = ref("");
const PLUS_COLORS = ["#7268C9", "#E4724B", "#6F8B5A"];
const t = computed(() =>
  zh.value
    ? { details: "链接与条款", collapse: "收起", close: "关闭", scroll: "向下滑动", burstTitle: "本项目整理的 16 组参考风味", sources: "引用与来源", uses: "本项目的使用", terms: "来源条款", top: "回到顶端" }
    : { details: "Link and terms", collapse: "Collapse", close: "Close", scroll: "Scroll", burstTitle: "16 reference profiles organised by this project", sources: "Citations and sources", uses: "Use in this project", terms: "Source terms", top: "Back to top" },
);

const scroller = ref<HTMLElement | null>(null);
const flowTrack = ref<HTMLElement | null>(null);
const burstTrack = ref<HTMLElement | null>(null);
const flowProgress = ref(0);
const burstProgress = ref(0);
const reduced = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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
      <div class="leading-[0.9]"><span class="display block font-bold text-[22px]">flavor</span><span class="wordmark-serif block uppercase text-[22px] text-violet">words</span></div>
      <button type="button" class="icon-btn" :aria-label="t.close" @click="aboutOpen = false"><X :size="22" :stroke-width="1.75" /></button>
    </div>

    <!-- page 1: what it is for — blank above, the glyphs, the owner's three paragraphs (less is more) -->
    <section class="min-h-[calc(100dvh-72px)] px-5 pt-20 pb-8 flex flex-col" data-page="1" data-section="approach">
      <BrandGlyphs :size="20" />
      <p class="text-[11px] tracking-[0.22em] text-muted mt-8">{{ approach.eyebrow }}</p>
      <h1 class="text-[36px] mt-2 font-bold" :class="zh ? 'display-zh' : 'display'">{{ approach.title }}</h1>
      <p v-for="(p, i) in approach.intro" :key="'i' + i" class="leading-relaxed text-[16px] mt-4">{{ p }}</p>
      <p class="text-xs text-muted mt-auto pt-8 tracking-widest">↓ {{ t.scroll }}</p>
    </section>

    <!-- page 3: the column-and-trunk poster, drawn while scrolling -->
    <section ref="flowTrack" class="relative h-[560dvh] bg-[#0B0A09]" data-page="3" data-section="flow">
      <div class="sticky top-0 h-[100dvh] px-4 pt-[84px] pb-6 flex flex-col justify-center overflow-hidden text-[#F4F1EA]">
        <SourceColumns :progress="flowProgress" />
      </div>
    </section>

    <!-- page 4: the profile network, drawn while scrolling -->
    <section ref="burstTrack" class="relative h-[560dvh] bg-[#0B0A09]" data-page="4" data-section="spectrum">
      <div class="sticky top-0 h-[100dvh] px-4 pt-[84px] pb-6 flex flex-col justify-start overflow-hidden text-[#F4F1EA]">
        <h2 class="text-[22px] font-bold leading-tight" :class="zh ? 'display-zh' : 'display'">{{ t.burstTitle }}</h2>
        <ProfileNetwork class="mt-2" :progress="burstProgress" />
      </div>
    </section>

    <!-- page 4: design notes — pinned for a beat, three folded entries with coloured marks, the credit line (owner's copy) -->
    <section class="relative min-h-[170dvh]" data-page="2" data-section="author">
    <div class="sticky top-0 min-h-[100dvh] max-h-[100dvh] overflow-y-auto px-5 pt-[100px] pb-10 flex flex-col bg-paper" data-reveal>
      <p class="text-[11px] tracking-[0.22em] text-muted">{{ author.eyebrow }}</p>
      <h2 class="text-[32px] mt-2 font-bold" :class="zh ? 'display-zh' : 'display'">{{ author.title }}</h2>
      <p v-for="(p, i) in author.paragraphs" :key="'a' + i" class="leading-relaxed mt-4 text-[16px]">{{ p }}</p>
      <div class="mt-8 divide-y divide-ink/10 border-y border-ink/10">
        <div v-for="(section, si) in sections" :key="section.id" :data-section="section.id">
          <button type="button" class="fold-toggle py-4" :aria-expanded="openSection === section.id" @click="toggle(section.id)">
            <span>
              <span class="block text-[18px] font-medium">{{ section.title }}</span>
              <span class="block text-sm text-muted mt-0.5 leading-relaxed">{{ section.summary }}</span>
            </span>
            <span class="text-2xl leading-none ml-4 shrink-0 font-semibold" :style="{ color: PLUS_COLORS[si % PLUS_COLORS.length] }">{{ openSection === section.id ? '–' : '+' }}</span>
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
      <p class="text-[14px] mt-8">{{ author.credit }}</p>
    </div>
    </section>

    <!-- page 5: sources in use, pinned for a beat, TOP at the bottom right -->
    <section class="relative min-h-[170dvh]" data-page="5" data-section="evidence">
    <div class="sticky top-0 min-h-[100dvh] max-h-[100dvh] overflow-y-auto px-5 pt-[100px] pb-28 flex flex-col bg-paper" data-reveal>
      <h2 class="text-[28px] font-bold" :class="zh ? 'display-zh' : 'display'">{{ t.sources }}</h2>
      <ol class="mt-5 relative">
        <li v-for="(e, i) in evidence" :key="e.id" class="relative pl-6 pb-6">
          <span class="absolute left-0 top-2 w-3 h-3 rounded-full" :style="{ backgroundColor: e.color }" />
          <span v-if="i < evidence.length - 1" class="absolute left-[5px] top-6 bottom-0 w-px bg-ink/15" />
          <p class="font-medium leading-snug text-[18px]">{{ e.title }}</p>
          <p class="text-[14px] leading-relaxed mt-1">{{ roleOf(e.id) }}</p>
          <p class="text-[13px] text-muted leading-relaxed mt-1"><span class="text-ink">{{ t.uses }}：</span>{{ e.use }}</p>
          <button type="button" class="chip mt-3 !min-h-[44px] !py-2 text-sm" :aria-expanded="openSection === e.id" @click="toggle(e.id)">{{ openSection === e.id ? t.collapse : t.details }}</button>
          <div class="fold" :data-open="openSection === e.id">
            <div>
              <p class="text-xs text-muted mt-3 break-all">{{ e.locator }}</p>
              <p class="text-xs text-muted mt-1"><span class="text-ink">{{ t.terms }}：</span>{{ e.terms }}</p>
            </div>
          </div>
        </li>
      </ol>
      <button type="button" class="absolute right-5 bottom-8 rounded-xl bg-ink text-paper min-h-[54px] px-5 font-semibold inline-flex items-center gap-2" data-action="top" @click="toTop">↑ TOP</button>
    </div>
    </section>
  </aside>
</template>

<script setup lang="ts">
// The page is two bands with no background of its own (owner). Home: the hero band (paper) is 2.25 × the lower
// band and shows the wordmark, the bold tagline and the flavor card — the product object — with the selection
// trace; the lower band holds two tall, bright rectangular buttons (1 : 1.25), Start and About. In the flow the
// split is 1 : 3 and the top band collects the answered cards. Card transitions are GSAP springs.
import { computed } from "vue";
import gsap from "gsap";
import { ArrowRight } from "lucide-vue-next";
import { aboutExample } from "flavor-data/product-vector-v1/about";
import AppHeader from "./components/AppHeader.vue";
import CollectedStack from "./components/CollectedStack.vue";
import AboutDrawer from "./components/AboutDrawer.vue";
import ContextSetupCard from "./components/ContextSetupCard.vue";
import FlavorCard from "./components/FlavorCard.vue";
import QuizCard from "./components/QuizCard.vue";
import FirstDescriptionCard from "./components/FirstDescriptionCard.vue";
import EscalationModal from "./components/EscalationModal.vue";
import FinalAttributionCard from "./components/FinalAttributionCard.vue";
import { aboutOpen, collecting, currentContextCard, locale, screen, shell, stage, stageColor, stageInk, start } from "./store";

const sample = computed(() => aboutExample(locale.value));
const SAMPLE_DIMS = ["floral", "floral", "fruity", "fruity", "acidity"];
const stageKey = () => {
  if (stage.value === "hero") return "hero";
  if (stage.value === "context") return `context:${currentContextCard.value?.key ?? ""}`;
  const s = screen.value;
  if (!s) return "empty";
  return s.kind === "question" ? `q:${s.slot}` : s.kind;
};
const reduced = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function onEnter(el: Element, done: () => void) {
  if (reduced()) return done();
  gsap.fromTo(el, { y: 44, scale: 0.965, opacity: 0, transformOrigin: "50% 100%" }, { y: 0, scale: 1, opacity: 1, duration: 0.62, ease: "back.out(1.15)", onComplete: done, clearProps: "transform,opacity" });
}
function onLeave(el: Element, done: () => void) {
  if (reduced()) return done();
  gsap.to(el, { y: "-58%", scale: 0.84, rotateX: 14, opacity: 0, transformOrigin: "50% 0%", duration: 0.4, ease: "power3.in", onComplete: done });
}
</script>

<template>
  <div class="h-[100dvh] flex flex-col transition-colors duration-500" :style="{ backgroundColor: stageColor, color: stageInk }">
    <!-- paper above, colour below: 2.25 : 1 on the home page, 1 : 3 in the flow (owner) -->
    <section class="relative shrink-0 bg-paper text-ink px-5 pt-4 pb-3 flex flex-col min-h-0 safe-top transition-[flex-basis] duration-500" :class="stage === 'hero' ? 'basis-[69%]' : 'basis-[25%]'" data-zone="top">
      <AppHeader :big="stage === 'hero'" />
      <template v-if="stage === 'hero'">
        <h1 class="font-display font-bold text-[34px] leading-[1.02] tracking-tight mt-5 rise">{{ shell.title }}</h1>
        <p class="text-[15px] leading-relaxed text-muted mt-2 rise">{{ shell.subtitle }}</p>
        <div class="mt-auto pt-4 rise" data-sample>
          <FlavorCard :cup="sample.cup" :words="sample.words" :dimensions="SAMPLE_DIMS" :reference="sample.reference" :eyebrow="sample.eyebrow" compact />
        </div>
      </template>
      <CollectedStack v-else />
      <div v-if="collecting" class="absolute right-5 bottom-3 flex gap-1" aria-live="polite" :aria-label="locale === 'zh-CN' ? '收集中' : 'collecting'">
        <span class="dot w-2 h-2 rounded-full bg-ink" /><span class="dot w-2 h-2 rounded-full bg-ink" /><span class="dot w-2 h-2 rounded-full bg-ink" />
      </div>
    </section>

    <section class="relative flex-1 min-h-0 safe-bottom" data-zone="stage">
      <Transition :css="false" mode="out-in" @enter="onEnter" @leave="onLeave">
        <div :key="stageKey()" class="h-full">
          <section v-if="stage === 'hero'" class="h-full flex items-stretch gap-3 px-5 py-4" data-screen="hero">
            <button type="button" class="tile flex-1 bg-clay text-paper rise" data-action="start" @click="start">
              <span class="font-bold text-[30px] leading-none" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">{{ shell.start }}</span>
              <ArrowRight :size="36" :stroke-width="2" class="self-end" />
            </button>
            <button type="button" class="tile flex-1 bg-lime text-ink rise" data-action="about" @click="aboutOpen = true">
              <span class="font-bold text-[30px] leading-none" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">{{ shell.about }}</span>
              <span class="self-end font-display font-bold text-[26px] leading-none">?</span>
            </button>
          </section>

          <ContextSetupCard v-else-if="stage === 'context'" />

          <template v-else-if="stage === 'session' && screen">
            <QuizCard v-if="screen.kind === 'question'" :model="screen" />
            <FirstDescriptionCard v-else-if="screen.kind === 'first_description'" :model="screen" />
            <FinalAttributionCard v-else-if="screen.kind === 'result'" :model="screen" />
            <div v-else class="h-full" data-screen="describe_ready" />
          </template>
        </div>
      </Transition>
      <EscalationModal v-if="stage === 'session' && screen && screen.kind === 'escalation'" :model="screen" />
    </section>

    <AboutDrawer v-if="aboutOpen" />
  </div>
</template>

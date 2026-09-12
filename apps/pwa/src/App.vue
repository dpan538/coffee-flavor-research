<script setup lang="ts">
// The page has no background of its own (owner): a paper band on top and a colour band below. On the home page
// the split is 1 : 2 — the wordmark and the tagline are the hero, the lower band holds two tiles, Start and About
// (owner's reference: a big title, then two bold cards). In the flow the split is 1 : 3 and the top band collects
// the answered cards. One card at a time; the card transition is a GSAP spring, off under prefers-reduced-motion.
import gsap from "gsap";
import { ArrowRight, Info } from "lucide-vue-next";
import AppHeader from "./components/AppHeader.vue";
import CollectedStack from "./components/CollectedStack.vue";
import AboutDrawer from "./components/AboutDrawer.vue";
import ContextSetupCard from "./components/ContextSetupCard.vue";
import QuizCard from "./components/QuizCard.vue";
import FirstDescriptionCard from "./components/FirstDescriptionCard.vue";
import EscalationModal from "./components/EscalationModal.vue";
import FinalAttributionCard from "./components/FinalAttributionCard.vue";
import { aboutOpen, collecting, currentContextCard, locale, screen, shell, stage, stageColor, stageInk, start } from "./store";

const stageKey = () => {
  if (stage.value === "hero") return "hero";
  if (stage.value === "context") return `context:${currentContextCard.value?.key ?? ""}`;
  const s = screen.value;
  if (!s) return "empty";
  return s.kind === "question" ? `q:${s.slot}` : s.kind;
};
const reduced = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** the next card rises in with a small overshoot */
function onEnter(el: Element, done: () => void) {
  if (reduced()) return done();
  gsap.fromTo(el, { y: 44, scale: 0.965, opacity: 0, transformOrigin: "50% 100%" }, { y: 0, scale: 1, opacity: 1, duration: 0.62, ease: "back.out(1.15)", onComplete: done, clearProps: "transform,opacity" });
}
/** the answered card lifts, tilts back and shrinks toward the stack above */
function onLeave(el: Element, done: () => void) {
  if (reduced()) return done();
  gsap.to(el, { y: "-58%", scale: 0.84, rotateX: 14, opacity: 0, transformOrigin: "50% 0%", duration: 0.4, ease: "power3.in", onComplete: done });
}
</script>

<template>
  <div class="h-[100dvh] flex flex-col transition-colors duration-500" :style="{ backgroundColor: stageColor, color: stageInk }">
    <!-- paper above, the card colour below; 1 : 2 on the home page, 1 : 3 in the flow (owner) -->
    <section class="relative shrink-0 bg-paper text-ink px-5 pt-4 pb-3 flex flex-col min-h-0 safe-top transition-[flex-basis] duration-500" :class="stage === 'hero' ? 'basis-[33.3%]' : 'basis-[25%]'" data-zone="top">
      <AppHeader :big="stage === 'hero'" />
      <p v-if="stage === 'hero'" class="font-display text-[27px] tracking-tight leading-tight text-muted mt-auto pb-1 rise">{{ shell.title }}</p>
      <CollectedStack v-else />
      <div v-if="collecting" class="absolute right-5 bottom-3 flex gap-1" aria-live="polite" :aria-label="locale === 'zh-CN' ? '收集中' : 'collecting'">
        <span class="dot w-2 h-2 rounded-full bg-ink" /><span class="dot w-2 h-2 rounded-full bg-ink" /><span class="dot w-2 h-2 rounded-full bg-ink" />
      </div>
    </section>

    <section class="relative flex-1 min-h-0 safe-bottom" data-zone="stage">
      <Transition :css="false" mode="out-in" @enter="onEnter" @leave="onLeave">
        <div :key="stageKey()" class="h-full">
          <section v-if="stage === 'hero'" class="h-full flex flex-col px-5 pt-6 pb-5 gap-5" data-screen="hero">
            <p class="text-[17px] leading-relaxed opacity-95 rise">{{ shell.subtitle }}</p>
            <div class="grid grid-cols-2 gap-3">
              <button type="button" class="tile aspect-[1/1.02] bg-paper text-ink rise" data-action="start" @click="start">
                <span class="text-[30px] font-semibold leading-tight" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">{{ shell.start }}</span>
                <ArrowRight :size="40" :stroke-width="1.5" class="self-end" />
              </button>
              <button type="button" class="tile aspect-[1/1.02] bg-ochre text-ink rise" data-action="about" @click="aboutOpen = true">
                <span class="text-[30px] font-semibold leading-tight" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">{{ shell.about }}</span>
                <Info :size="40" :stroke-width="1.5" class="self-end" />
              </button>
            </div>
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

<script setup lang="ts">
// Two bands, no background of their own (owner). Home: the hero band holds the small wordmark and, centred, the
// headline "Every taste has its own vocabulary." with the letters of "taste" each in a colour, the language title,
// the body paragraph, the motif row and the two-line slogan (tapping it starts, no underline — a redundant path to
// the Start button below). The lower band holds the two bright 1 : 1.2 buttons. In the flow the split is 1 : 3.
import { computed } from "vue";
import gsap from "gsap";
import { ArrowRight } from "lucide-vue-next";
import AppHeader from "./components/AppHeader.vue";
import BrandGlyphs from "./components/BrandGlyphs.vue";
import CollectedStack from "./components/CollectedStack.vue";
import AboutDrawer from "./components/AboutDrawer.vue";
import ContextSetupCard from "./components/ContextSetupCard.vue";
import QuizCard from "./components/QuizCard.vue";
import FirstDescriptionCard from "./components/FirstDescriptionCard.vue";
import EscalationModal from "./components/EscalationModal.vue";
import FinalAttributionCard from "./components/FinalAttributionCard.vue";
import { aboutOpen, collecting, currentContextCard, locale, screen, shell, stage, stageColor, stageInk, start } from "./store";

// "Every taste has its own vocabulary." — only the five letters of "taste" take a colour each (owner)
const LETTER_COLORS = ["#7C6CFF", "#FF6B4A", "#2EC27E", "#FFB300", "#2F9BFF"];
const headline = computed(() => {
  const text = shell.value.slogan;
  const at = text.toLowerCase().indexOf("taste");
  if (at < 0) return { before: text, letters: [] as Array<{ ch: string; color: string }>, after: "" };
  return { before: text.slice(0, at), letters: text.slice(at, at + 5).split("").map((ch, i) => ({ ch, color: LETTER_COLORS[i]! })), after: text.slice(at + 5) };
});
// the slogan line breaks before 从: the claim on one line, the start line on the next
const sloganLines = computed(() => [shell.value.claim, shell.value.startLink + " →"].filter((l) => l.trim() !== "→"));
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
    <!-- paper above, colour below: 58 : 42 on the home page, 1 : 3 in the flow (owner) -->
    <section class="relative shrink-0 bg-paper text-ink px-5 pt-4 pb-3 flex flex-col min-h-0 safe-top transition-[flex-basis] duration-500" :class="stage === 'hero' ? 'basis-[60.5%]' : 'basis-[25%]'" data-zone="top">
      <AppHeader :big="stage === 'hero'" />
      <div v-if="stage === 'hero'" class="flex-1 min-h-0 flex flex-col justify-center gap-3 pt-10 pb-2" data-hero>
        <h1 class="font-display font-bold text-[34px] leading-[1.05] tracking-tight rise" data-headline>{{ headline.before }}<span v-for="(l, i) in headline.letters" :key="i" :style="{ color: l.color }">{{ l.ch }}</span>{{ headline.after }}</h1>
        <h2 class="font-semibold text-[22px] leading-tight rise" :class="locale === 'zh-CN' ? 'display-zh' : 'font-display'">{{ shell.title }}</h2>
        <p class="text-[15px] leading-relaxed text-ink rise">{{ shell.subtitle }}</p>
        <BrandGlyphs class="rise" :size="18" />
        <button type="button" class="text-left font-display font-bold text-[16px] leading-snug tracking-tight min-h-[44px] mt-3 rise" data-action="start-link" @click="start">
          <span v-for="(line, i) in sloganLines" :key="i" class="block">{{ line }}</span>
        </button>
      </div>
      <CollectedStack v-else />
      <div v-if="collecting" class="absolute right-5 bottom-3 flex gap-1" aria-live="polite" :aria-label="locale === 'zh-CN' ? '收集中' : 'collecting'">
        <span class="dot w-2 h-2 rounded-full bg-ink" /><span class="dot w-2 h-2 rounded-full bg-ink" /><span class="dot w-2 h-2 rounded-full bg-ink" />
      </div>
    </section>

    <section class="relative flex-1 min-h-0 safe-bottom" data-zone="stage">
      <Transition :css="false" mode="out-in" @enter="onEnter" @leave="onLeave">
        <div :key="stageKey()" class="h-full">
          <section v-if="stage === 'hero'" class="h-full flex items-center gap-3 px-5 py-6" data-screen="hero">
            <button type="button" class="tile flex-1 aspect-[1/1.2] bg-sun text-ink rise" data-action="start" @click="start">
              <span class="font-bold text-[28px] leading-none" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">{{ shell.start }}</span>
              <ArrowRight :size="32" :stroke-width="2" class="self-end" />
            </button>
            <button type="button" class="tile flex-1 aspect-[1/1.2] bg-mint2 text-ink rise" data-action="about" @click="aboutOpen = true">
              <span class="font-bold text-[28px] leading-none" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">{{ shell.about }}</span>
              <span class="self-end font-display font-bold text-[24px] leading-none">?</span>
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

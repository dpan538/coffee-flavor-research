<script setup lang="ts">
// The page has no background of its own (owner): it is split 1 : 4 — a paper band on top (logo, About, language,
// the collected cards) and a colour band below that changes with the current card. One card at a time.
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
</script>

<template>
  <div class="h-[100dvh] flex flex-col transition-colors duration-500" :style="{ backgroundColor: stageColor, color: stageInk }">
    <!-- no page background: the screen is split 1 : 4, paper above, the card colour below (owner) -->
    <section class="relative basis-1/5 shrink-0 bg-paper text-ink px-5 pt-4 pb-3 flex flex-col min-h-0 safe-top" data-zone="top">
      <AppHeader />
      <CollectedStack />
      <div v-if="collecting" class="absolute right-5 bottom-3 flex gap-1" aria-live="polite" :aria-label="locale === 'zh-CN' ? '收集中' : 'collecting'">
        <span class="dot w-2 h-2 rounded-full bg-ink" /><span class="dot w-2 h-2 rounded-full bg-ink" /><span class="dot w-2 h-2 rounded-full bg-ink" />
      </div>
    </section>

    <section class="relative flex-1 min-h-0 safe-bottom" data-zone="stage">
      <Transition name="fold" mode="out-in">
        <div :key="stageKey()" class="h-full">
          <section v-if="stage === 'hero'" class="h-full flex flex-col" data-screen="hero">
            <div class="flex-1 px-6 pt-8 flex flex-col justify-end gap-3">
              <h1 class="text-[44px]" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">{{ shell.title }}</h1>
              <p class="text-lg opacity-90">{{ shell.subtitle }}</p>
            </div>
            <div class="flex-1 px-6 pb-8 flex flex-col justify-end gap-6">
              <p class="text-base opacity-90 leading-relaxed">{{ shell.lead }}</p>
              <button type="button" class="cta bg-paper !text-ink" @click="start">{{ shell.start }}</button>
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

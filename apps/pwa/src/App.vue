<script setup lang="ts">
// Structural shell only (owner: stop before visual design). Screens follow screenModel's five kinds.
import AppHeader from "./components/AppHeader.vue";
import AboutDrawer from "./components/AboutDrawer.vue";
import ContextSetupCard from "./components/ContextSetupCard.vue";
import QuizCard from "./components/QuizCard.vue";
import FirstDescriptionCard from "./components/FirstDescriptionCard.vue";
import EscalationModal from "./components/EscalationModal.vue";
import FinalAttributionCard from "./components/FinalAttributionCard.vue";
import { aboutOpen, screen, shell, stage, start } from "./store";
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <AppHeader />
    <main class="flex-1 flex flex-col items-center justify-center p-6">
      <section v-if="stage === 'hero'" class="max-w-md w-full text-center space-y-4" data-screen="hero">
        <h1 class="text-2xl">{{ shell.title }}</h1>
        <p>{{ shell.subtitle }}</p>
        <p>{{ shell.lead }}</p>
        <button type="button" class="border px-6 py-3" @click="start">{{ shell.start }}</button>
      </section>

      <ContextSetupCard v-else-if="stage === 'context'" />

      <template v-else-if="stage === 'session' && screen">
        <QuizCard v-if="screen.kind === 'question'" :model="screen" />
        <FirstDescriptionCard v-else-if="screen.kind === 'first_description'" :model="screen" />
        <FinalAttributionCard v-else-if="screen.kind === 'result'" :model="screen" />
        <p v-else data-screen="describe_ready">…</p>
        <EscalationModal v-if="screen.kind === 'escalation'" :model="screen" />
      </template>
    </main>
    <AboutDrawer v-if="aboutOpen" />
  </div>
</template>

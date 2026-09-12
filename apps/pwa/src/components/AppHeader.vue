<script setup lang="ts">
// Wordmark on two lines; About as an icon; language as text (it is the content).
import { Info } from "lucide-vue-next";
import { aboutOpen, online, shell, toggleLocale } from "../store";
</script>

<template>
  <header class="flex items-start justify-between" data-component="AppHeader">
    <div class="leading-[0.9] select-none" aria-label="flavorwords">
      <span class="display block text-[26px]">flavor</span>
      <span class="display block text-[26px] text-violet">words</span>
    </div>
    <div class="flex items-center gap-2 pt-1">
      <span class="w-1.5 h-1.5 rounded-full" :class="online ? 'bg-leaf' : 'bg-salmon'" :title="shell.offlineReady" />
      <button type="button" class="rounded-full border border-ink/20 p-2" :aria-label="shell.about" @click="aboutOpen = true"><Info :size="18" :stroke-width="1.75" /></button>
      <button type="button" class="chip !py-1.5 !px-3 text-sm" @click="toggleLocale">{{ shell.localeSwitch }}</button>
    </div>
  </header>
</template>

<script setup lang="ts">
// Wordmark (large on the home page, small in the flow); language as text — the only control up here (owner:
// no About icon; About is a tile on the home page). The toggle is a 54 dp target.
import { online, shell, toggleLocale } from "../store";

defineProps<{ big?: boolean }>();
</script>

<template>
  <header class="flex items-start justify-between" data-component="AppHeader">
    <div class="select-none transition-all duration-500" :class="big ? 'leading-[0.86]' : 'leading-[0.9]'" aria-label="flavorwords">
      <span class="display block transition-all duration-500" :class="big ? 'text-[64px]' : 'text-[26px]'">flavor</span>
      <span class="display block text-violet transition-all duration-500" :class="big ? 'text-[64px]' : 'text-[26px]'">words</span>
    </div>
    <div class="flex items-center gap-2">
      <span class="w-1.5 h-1.5 rounded-full mr-1" :class="online ? 'bg-leaf' : 'bg-salmon'" :title="shell.offlineReady" />
      <button type="button" class="rounded-xl bg-ink text-paper min-h-[54px] min-w-[64px] px-4 text-base font-medium inline-flex items-center justify-center" @click="toggleLocale">{{ shell.localeSwitch }}</button>
    </div>
  </header>
</template>

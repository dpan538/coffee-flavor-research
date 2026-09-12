<script setup lang="ts">
// Wordmark (a little larger on the home page) and the language badge — the only control up here (owner: no About
// icon, no status dot). The badge is a black rounded rectangle, 54 dp.
import { shell, toggleLocale } from "../store";

defineProps<{ big?: boolean }>();
</script>

<template>
  <header class="flex items-start justify-between" data-component="AppHeader">
    <div class="select-none leading-[0.9]" aria-label="flavorwords">
      <span class="display block font-bold transition-all duration-500" :class="big ? 'text-[40px]' : 'text-[24px]'">flavor</span>
      <span class="display block font-bold text-violet transition-all duration-500" :class="big ? 'text-[40px]' : 'text-[24px]'">words</span>
    </div>
    <button type="button" class="rounded-xl bg-ink text-paper min-h-[54px] min-w-[64px] px-4 text-base font-semibold inline-flex items-center justify-center" @click="toggleLocale">{{ shell.localeSwitch }}</button>
  </header>
</template>

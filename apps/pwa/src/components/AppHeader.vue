<script setup lang="ts">
// Wordmark ("FLAVOR" in the display sans, "WORDS" in Fraunces, both upper case) and the language badge.
import { shell, toggleLocale } from "../store";

defineProps<{ big?: boolean }>();
</script>

<template>
  <header class="flex items-start justify-between" data-component="AppHeader">
    <div class="select-none leading-[0.9]" aria-label="flavorwords">
      <span class="display block font-bold transition-all duration-500" :class="big ? 'text-[30px]' : 'text-[24px]'">flavor</span>
      <span class="wordmark-serif block uppercase text-violet transition-all duration-500" :class="big ? 'text-[30px]' : 'text-[24px]'">words</span>
    </div>
    <button type="button" class="rounded-xl bg-ink text-paper min-h-[48px] min-w-[58px] px-3.5 text-[15px] font-semibold inline-flex items-center justify-center" @click="toggleLocale">{{ shell.localeSwitch }}</button>
  </header>
</template>

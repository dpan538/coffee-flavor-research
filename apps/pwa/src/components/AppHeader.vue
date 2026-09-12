<script setup lang="ts">
// The wordmark (a little larger on the home page) and the language badge — the only control up here.
import Wordmark from "./Wordmark.vue";
import { shell, toggleLocale } from "../store";

defineProps<{ big?: boolean }>();
</script>

<template>
  <header class="flex items-start justify-between" data-component="AppHeader">
    <Wordmark
      :width="big ? 104 : 84"
      class="select-none transition-all duration-500"
    />
    <button
      type="button"
      class="rounded-xl bg-ink text-paper min-h-[48px] min-w-[58px] px-3.5 text-[15px] font-semibold inline-flex items-center justify-center"
      @click="toggleLocale"
    >
      {{ shell.localeSwitch }}
    </button>
  </header>
</template>

<script setup lang="ts">
import { Info, Languages, Wifi, WifiOff } from "lucide-vue-next";
import { aboutOpen, online, shell, toggleLocale } from "../store";
</script>

<template>
  <header class="flex items-center justify-between p-4" data-component="AppHeader">
    <button type="button" class="flex items-center gap-1" :aria-label="shell.about" @click="aboutOpen = true">
      <Info :size="18" /><span>{{ shell.about }}</span>
    </button>
    <div class="flex items-center gap-3">
      <span class="flex items-center gap-1" :title="shell.offlineReady">
        <Wifi v-if="online" :size="16" /><WifiOff v-else :size="16" /><span>{{ shell.offlineReady }}</span>
      </span>
      <button type="button" class="flex items-center gap-1" @click="toggleLocale"><Languages :size="16" /><span>{{ shell.localeSwitch }}</span></button>
    </div>
  </header>
</template>

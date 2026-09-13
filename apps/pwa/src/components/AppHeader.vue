<script setup lang="ts">
// The wordmark (a little larger on the home page), the add-to-home-screen icon and the language badge.
import { Download } from "lucide-vue-next";
import { ref } from "vue";
import InstallSheet from "./InstallSheet.vue";
import Wordmark from "./Wordmark.vue";
import { installed, promptInstall } from "../install";
import { shell, toggleLocale } from "../store";

defineProps<{ big?: boolean }>();
const sheetOpen = ref(false);

async function install() {
  const outcome = await promptInstall();
  if (outcome === "unavailable") sheetOpen.value = true;
}
</script>

<template>
  <header class="flex items-start justify-between" data-component="AppHeader">
    <Wordmark
      :width="big ? 104 : 84"
      class="select-none transition-all duration-500"
    />
    <div class="flex items-center gap-2">
      <button
        v-if="!installed"
        type="button"
        class="rounded-xl border border-ink/20 text-ink min-h-[48px] min-w-[48px] inline-flex items-center justify-center"
        :aria-label="shell.install"
        :title="shell.install"
        data-action="install"
        @click="install"
      >
        <Download :size="22" :stroke-width="1.75" />
      </button>
      <button
        type="button"
        class="rounded-xl bg-ink text-paper min-h-[48px] min-w-[58px] px-3.5 text-[15px] font-semibold inline-flex items-center justify-center"
        @click="toggleLocale"
      >
        {{ shell.localeSwitch }}
      </button>
    </div>
    <InstallSheet v-if="sheetOpen" @close="sheetOpen = false" />
  </header>
</template>

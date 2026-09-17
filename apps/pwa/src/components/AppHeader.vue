<script setup lang="ts">
// The wordmark (a little larger on the home page; in the flow it is the way back to the home page), the
// add-to-home-screen icon on the home page — replaced by an exit icon in the flow (owner, 2026-09-17) — and the language
// badge in the same white bordered style as the icons (owner, 2026-09-17).
import { Download, LogOut } from "lucide-vue-next";
import { ref } from "vue";
import InstallSheet from "./InstallSheet.vue";
import Wordmark from "./Wordmark.vue";
import { installed, promptInstall } from "../install";
import { exitToHome, shell, stage, toggleLocale } from "../store";

defineProps<{ big?: boolean }>();
const sheetOpen = ref(false);

async function install() {
  const outcome = await promptInstall();
  if (outcome === "unavailable") sheetOpen.value = true;
}
</script>

<template>
  <header class="flex items-start justify-between" data-component="AppHeader">
    <button
      type="button"
      class="select-none text-left"
      :aria-label="shell.home"
      :title="stage === 'hero' ? undefined : shell.home"
      data-action="home"
      @click="exitToHome"
    >
      <Wordmark :width="big ? 104 : 84" class="transition-all duration-500" />
    </button>
    <div class="flex items-center gap-2">
      <button
        v-if="stage !== 'hero'"
        type="button"
        class="rounded-xl border border-ink/20 text-ink min-h-[48px] min-w-[48px] inline-flex items-center justify-center"
        :aria-label="shell.exit"
        :title="shell.exit"
        data-action="exit"
        @click="exitToHome"
      >
        <LogOut :size="22" :stroke-width="1.75" />
      </button>
      <button
        v-else-if="!installed"
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
        class="rounded-xl border border-ink/20 text-ink min-h-[48px] min-w-[48px] px-3 text-[15px] font-semibold inline-flex items-center justify-center"
        @click="toggleLocale"
      >
        {{ shell.localeSwitch }}
      </button>
    </div>
    <InstallSheet v-if="sheetOpen" @close="sheetOpen = false" />
  </header>
</template>

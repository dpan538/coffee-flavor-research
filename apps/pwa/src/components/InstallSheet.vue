<script setup lang="ts">
// The add-to-home-screen sheet: one line for the platform at hand, one button.
import { Share, X } from "lucide-vue-next";
import { computed } from "vue";
import { platform } from "../install";
import { shell } from "../store";

const emit = defineEmits<{ close: [] }>();
const line = computed(() => {
  const s = shell.value;
  if (platform.wechat) return s.installWechat;
  if (platform.ios) return platform.safari ? s.installIos : s.installIosOther;
  if (platform.harmony) return s.installHarmony;
  return s.installOther;
});
// the quoted menu name stays on one line (owner: no break before the last character)
const parts = computed(() =>
  line.value
    .split(/(「[^」]*」|“[^”]*”)/)
    .filter(Boolean)
    .map((text) => ({ text, quote: /^[「“]/.test(text) })),
);
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-[60] bg-ink/40 flex items-end sm:items-center justify-center p-4 pb-[calc(1rem_+_env(safe-area-inset-bottom))]"
      role="dialog"
      aria-modal="true"
      data-component="InstallSheet"
      @click.self="emit('close')"
    >
      <section
        class="app-col max-w-[420px] rounded-[20px] bg-paper text-ink p-5 flex flex-col gap-4"
      >
        <div class="flex items-start justify-between gap-3">
          <h2
            class="text-[22px] leading-tight"
            :class="shell.localeSwitch === 'EN' ? 'display-zh' : 'display'"
          >
            {{ shell.installTitle }}
          </h2>
          <button
            type="button"
            class="icon-btn shrink-0"
            :aria-label="shell.installClose"
            @click="emit('close')"
          >
            <X :size="22" :stroke-width="1.75" />
          </button>
        </div>
        <p class="flex items-start gap-3 text-[15px] leading-relaxed">
          <Share
            v-if="platform.ios"
            :size="22"
            :stroke-width="1.75"
            class="shrink-0 mt-0.5"
          />
          <span
            ><template v-for="(part, i) in parts" :key="i"
              ><span :class="part.quote ? 'whitespace-nowrap' : ''">{{
                part.text
              }}</span></template
            ></span
          >
        </p>
        <button type="button" class="cta" @click="emit('close')">
          {{ shell.installClose }}
        </button>
      </section>
    </div>
  </Teleport>
</template>

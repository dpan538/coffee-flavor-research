<script setup lang="ts">
// Q6: rendered only when the escalation gate opened it (severe conflict + picks confirming the bias). Text only, no icons.
import { ref } from "vue";
import type { EscalationModalModel } from "flavor-data/product-vector-v1/view";
import { locale, submitQ6 } from "../store";

defineProps<{ model: EscalationModalModel }>();
const selected = ref<string[]>([]);
function toggle(dimension: string) {
  selected.value = selected.value.includes(dimension)
    ? selected.value.filter((d) => d !== dimension)
    : [...selected.value, dimension];
}
</script>

<template>
  <div
    class="absolute inset-0 bg-maroon"
    role="dialog"
    aria-modal="true"
    data-component="EscalationModal"
  >
    <section
      class="app-col h-full bg-maroon text-paper px-5 pt-7 pb-4 flex flex-col gap-4"
    >
      <p class="text-xs uppercase tracking-widest opacity-70">
        {{ locale === "zh-CN" ? "再看一眼" : "One more look" }}
      </p>
      <h2
        class="text-[30px]"
        :class="locale === 'zh-CN' ? 'display-zh' : 'display'"
      >
        {{ model.title }}
      </h2>
      <div
        class="grid grid-cols-2 auto-rows-fr gap-2 flex-1 min-h-0"
        role="group"
      >
        <button
          v-for="option in model.options"
          :key="option.dimension"
          type="button"
          class="option flex items-center justify-center text-center"
          :aria-pressed="selected.includes(option.dimension)"
          :data-dimension="option.dimension"
          @click="toggle(option.dimension)"
        >
          {{ option.text }}
        </button>
      </div>
      <button
        type="button"
        class="cta bg-paper !text-ink"
        :disabled="selected.length === 0"
        @click="submitQ6(selected)"
      >
        {{ model.submitLabel }}
      </button>
    </section>
  </div>
</template>

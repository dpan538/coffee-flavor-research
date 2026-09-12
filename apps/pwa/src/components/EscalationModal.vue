<script setup lang="ts">
// Q6: rendered only when the escalation gate opened it (severe conflict + picks confirming the bias).
import { ref } from "vue";
import type { EscalationModalModel } from "flavor-data/product-vector-v1/view";
import { submitQ6 } from "../store";

defineProps<{ model: EscalationModalModel }>();
const selected = ref<string[]>([]);
function toggle(dimension: string) {
  selected.value = selected.value.includes(dimension) ? selected.value.filter((d) => d !== dimension) : [...selected.value, dimension];
}
</script>

<template>
  <div class="fixed inset-0 flex items-end justify-center" role="dialog" aria-modal="true" data-component="EscalationModal">
    <section class="max-w-md w-full space-y-4 p-6 border bg-white">
      <h2>{{ model.title }}</h2>
      <div class="grid grid-cols-2 gap-2" role="group">
        <button v-for="option in model.options" :key="option.dimension" type="button" class="border px-3 py-2" :aria-pressed="selected.includes(option.dimension)" :data-dimension="option.dimension" @click="toggle(option.dimension)">
          {{ option.text }}
        </button>
      </div>
      <button type="button" class="border px-6 py-3" :disabled="selected.length === 0" @click="submitQ6(selected)">{{ model.submitLabel }}</button>
    </section>
  </div>
</template>

<script setup lang="ts">
// C0–C2 cards from contextCatalog: single chips, the SOE / blend toggle (max 3 varieties), optional origin chips.
import { computed, ref } from "vue";
import { catalog, confirmContext, draftContext, locale } from "../store";

const blendMode = ref(false);
const varietyCard = computed(() => catalog.value.find((c) => c.key === "c2_variety"));
const maxVarieties = computed(() => (varietyCard.value && varietyCard.value.key === "c2_variety" ? varietyCard.value.max : 1));

function selected(key: string): string[] {
  const value = (draftContext.value as Record<string, string | string[] | undefined>)[key];
  return Array.isArray(value) ? value : value ? [value] : [];
}

function choose(key: string, value: string, multi: boolean) {
  const draft = { ...draftContext.value } as Record<string, string | string[] | undefined>;
  if (multi && blendMode.value) {
    const current = selected(key);
    draft[key] = current.includes(value) ? current.filter((v) => v !== value) : current.length < maxVarieties.value ? [...current, value] : current;
  } else {
    draft[key] = draft[key] === value ? undefined : value;
  }
  draftContext.value = draft as typeof draftContext.value;
}

function setSingle() {
  blendMode.value = false;
  const first = selected("c2_variety")[0];
  const draft = { ...draftContext.value } as Record<string, string | string[] | undefined>;
  if (first) draft.c2_variety = first;
  else delete draft.c2_variety;
  draftContext.value = draft as typeof draftContext.value;
}

const ready = computed(() => Boolean(draftContext.value.c0_preparation && draftContext.value.c1_roast && draftContext.value.c2_process && selected("c2_variety").length));
const labels = computed(() => (locale.value === "zh-CN" ? { next: "开始问答", skip: "跳过" } : { next: "Start the questions", skip: "Skip" }));
</script>

<template>
  <section class="max-w-md w-full space-y-6" data-component="ContextSetupCard">
    <div v-for="card in catalog" :key="card.key" class="space-y-2" :data-context-key="card.key">
      <h2>{{ card.title }}<span v-if="card.optional"> ·</span></h2>
      <div v-if="card.key === 'c2_variety'" class="flex gap-2" role="radiogroup">
        <button type="button" :aria-pressed="!blendMode" class="border px-2 py-1" @click="setSingle">{{ card.toggle.single }}</button>
        <button type="button" :aria-pressed="blendMode" class="border px-2 py-1" @click="blendMode = true">{{ card.toggle.blend }}</button>
      </div>
      <p v-if="card.key === 'c2_origin'">{{ card.hint }}</p>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="chip in card.chips"
          :key="chip.value"
          type="button"
          class="border px-3 py-1"
          :aria-pressed="selected(card.key).includes(chip.value)"
          :title="chip.basis"
          @click="choose(card.key, chip.value, card.multi)"
        >
          {{ chip.label }}
        </button>
      </div>
    </div>
    <button type="button" class="border px-6 py-3" :disabled="!ready" @click="confirmContext">{{ labels.next }}</button>
  </section>
</template>

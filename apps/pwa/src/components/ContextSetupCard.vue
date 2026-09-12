<script setup lang="ts">
// One context card at a time (C0, C1, C2 variety with SOE / blend, process, optional origin) — split like the quiz card.
import { computed, ref, watch } from "vue";
import { advanceContext, chooseContext, contextSelection, currentContextCard, locale } from "../store";

const blendMode = ref(false);
const card = computed(() => currentContextCard.value);
watch(card, () => (blendMode.value = false));
const max = computed(() => (card.value && card.value.key === "c2_variety" ? card.value.max : 1));
const chosen = computed(() => (card.value ? contextSelection(card.value.key) : []));
const ready = computed(() => Boolean(card.value) && (card.value!.optional || chosen.value.length > 0));
const labels = computed(() => (locale.value === "zh-CN" ? { next: "下一步", skip: "跳过", chosen: "已选" } : { next: "Next", skip: "Skip", chosen: "chosen" }));

function choose(value: string) {
  if (!card.value) return;
  const multi = card.value.multi && blendMode.value;
  if (!card.value.multi || !blendMode.value) {
    // single choice: replace
    const draftKey = card.value.key;
    if (contextSelection(draftKey).includes(value)) chooseContext(draftKey, value, false);
    else {
      for (const v of contextSelection(draftKey)) chooseContext(draftKey, v, multi, max.value);
      chooseContext(draftKey, value, false);
    }
    return;
  }
  chooseContext(card.value.key, value, true, max.value);
}

function labelOf(values: string[]): string {
  if (!card.value) return "";
  return values.map((v) => card.value!.chips.find((c) => c.value === v)?.label ?? v).join(" + ") || labels.value.skip;
}
</script>

<template>
  <section v-if="card" class="h-full flex flex-col" data-component="ContextSetupCard" :data-context-key="card.key">
    <div class="basis-[42%] min-h-0 px-6 pt-7 flex flex-col justify-end gap-2">
      <p class="text-xs uppercase tracking-widest opacity-70">{{ locale === 'zh-CN' ? '这杯咖啡' : 'This cup' }}</p>
      <h2 class="text-[34px]" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">{{ card.title }}</h2>
      <p v-if="card.key === 'c2_origin'" class="text-sm opacity-80">{{ card.hint }}</p>
      <div v-if="card.key === 'c2_variety'" class="flex gap-2 pt-1" role="radiogroup">
        <button type="button" class="chip !py-1" :aria-pressed="!blendMode" @click="blendMode = false">{{ card.toggle.single }}</button>
        <button type="button" class="chip !py-1" :aria-pressed="blendMode" @click="blendMode = true">{{ card.toggle.blend }} ≤ {{ card.max }}</button>
      </div>
    </div>
    <div class="flex-1 px-4 pt-5 pb-4 flex flex-col gap-3 min-h-0">
      <!-- options fill the lower half as a grid of equal cells (owner: use the space), scrolling only when a card has many -->
      <div class="grid grid-cols-2 auto-rows-fr gap-2 overflow-y-auto min-h-0 flex-1" :class="card.chips.length > 8 ? 'auto-rows-[minmax(56px,1fr)]' : ''">
        <button v-for="chip in card.chips" :key="chip.value" type="button" class="option flex items-center justify-center text-center !rounded-2xl" :aria-pressed="chosen.includes(chip.value)" :title="chip.basis" @click="choose(chip.value)">
          {{ chip.label }}
        </button>
      </div>
      <div class="shrink-0 pt-1">
        <button type="button" class="cta" :disabled="!ready" @click="advanceContext(labelOf(chosen))">
          {{ card.optional && !chosen.length ? labels.skip : labels.next }}<span v-if="chosen.length" class="opacity-70 font-normal"> · {{ labelOf(chosen) }}</span>
        </button>
      </div>
    </div>
  </section>
</template>

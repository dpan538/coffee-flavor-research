<script setup lang="ts">
// One context card at a time (C0, C1, C2 variety with SOE / blend, process, optional origin). The title sits at the
// top (owner: no blank above the question); the options fill the rest as a two-column grid of 60 px+ cells whose
// labels break into name / latin name (owner: text spilling out of the chips); Next is a full-width bar.
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

/** "波本 Bourbon" → ["波本", "Bourbon"]; "手冲 (V60)" → ["手冲", "(V60)"]; "SL28 / SL34" stays one line */
function lines(label: string): [string, string] {
  const m = label.match(/^([^\sA-Za-z(]+)\s+([A-Za-z(].*)$/);
  return m ? [m[1]!, m[2]!] : [label, ""];
}

function labelOf(values: string[]): string {
  if (!card.value) return "";
  return values.map((v) => lines(card.value!.chips.find((c) => c.value === v)?.label ?? v)[0]).join(" + ") || labels.value.skip;
}
</script>

<template>
  <section v-if="card" class="h-full flex flex-col" data-component="ContextSetupCard" :data-context-key="card.key">
    <div class="shrink-0 px-6 pt-6 flex flex-col gap-2">
      <p class="text-xs uppercase tracking-widest opacity-70">{{ locale === 'zh-CN' ? '这杯咖啡' : 'This cup' }}</p>
      <h2 class="text-[32px] rise" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">{{ card.title }}</h2>
      <p v-if="card.key === 'c2_origin'" class="text-sm opacity-80">{{ card.hint }}</p>
      <div v-if="card.key === 'c2_variety'" class="flex gap-2 pt-1" role="radiogroup">
        <button type="button" class="chip" :aria-pressed="!blendMode" @click="blendMode = false">{{ card.toggle.single }}</button>
        <button type="button" class="chip" :aria-pressed="blendMode" @click="blendMode = true">{{ card.toggle.blend }} ≤ {{ card.max }}</button>
      </div>
    </div>
    <div class="flex-1 px-4 pt-4 pb-4 flex flex-col gap-3 min-h-0">
      <div class="grid grid-cols-2 auto-rows-[minmax(60px,auto)] gap-2.5 overflow-y-auto min-h-0 content-start">
        <button v-for="chip in card.chips" :key="chip.value" type="button" class="option !px-3 !py-2.5 flex flex-col items-center justify-center text-center rise" :aria-pressed="chosen.includes(chip.value)" :title="chip.basis" @click="choose(chip.value)">
          <span class="l1">{{ lines(chip.label)[0] }}</span>
          <span v-if="lines(chip.label)[1]" class="l2">{{ lines(chip.label)[1] }}</span>
        </button>
      </div>
      <div class="shrink-0 mt-auto pt-1">
        <button type="button" class="cta" :disabled="!ready" @click="advanceContext(labelOf(chosen))">
          {{ card.optional && !chosen.length ? labels.skip : labels.next }}<span v-if="chosen.length" class="opacity-70 font-normal"> · {{ labelOf(chosen) }}</span>
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
// 3 + 5 words on a cream card, then the 8-choose-5 matrix (implicit strong feedback).
import { computed, ref } from "vue";
import type { FirstDescriptionCardModel } from "flavor-data/product-vector-v1/view";
import type { Word } from "flavor-data/product-vector-v1/flow";
import { collecting, locale, submitPickedWords } from "../store";

const props = defineProps<{ model: FirstDescriptionCardModel }>();
const chosen = ref<Word[]>([]);
const all = computed(() => [...props.model.main, ...props.model.secondary]);
const full = computed(() => chosen.value.length >= props.model.pickCount);
const submitLabel = computed(() => (locale.value === "zh-CN" ? "生成我的风味卡" : "Make my card"));

function toggle(word: Word) {
  const has = chosen.value.some((w) => w.text === word.text);
  if (has) chosen.value = chosen.value.filter((w) => w.text !== word.text);
  else if (!full.value) chosen.value = [...chosen.value, word];
}
</script>

<template>
  <section class="h-full flex flex-col" data-component="FirstDescriptionCard">
    <div class="basis-[45%] min-h-0 px-6 pt-7 flex flex-col justify-end gap-2">
      <p class="text-xs tracking-widest opacity-70">{{ model.heading }}</p>
      <h2 v-if="model.profileTitle" class="text-2xl" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">［{{ model.profileTitle }}］</h2>
      <template v-if="collecting">
        <div class="skeleton h-7 w-4/5" /><div class="skeleton h-5 w-3/5" />
      </template>
      <template v-else>
        <p class="text-xl leading-snug" data-words="main">{{ model.main.map((w) => w.text).join("  │  ") }}</p>
        <p class="text-base opacity-80" data-words="secondary">{{ model.secondary.map((w) => w.text).join("  ·  ") }}</p>
      </template>
    </div>
    <div class="flex-1 min-h-0 px-4 pt-5 pb-4 flex flex-col gap-3">
      <p class="text-sm opacity-80">{{ model.pickPrompt }}</p>
      <div class="flex flex-wrap gap-2" role="group">
        <button v-for="word in all" :key="word.text" type="button" class="chip rise" :aria-pressed="chosen.some((w) => w.text === word.text)" :data-dimension="word.dimension" @click="toggle(word)">{{ word.text }}</button>
      </div>
      <div class="mt-auto shrink-0">
        <button type="button" class="cta" :disabled="!full" @click="submitPickedWords(chosen)">{{ submitLabel }} <span class="opacity-70 font-normal">{{ chosen.length }} / {{ model.pickCount }}</span></button>
      </div>
    </div>
  </section>
</template>

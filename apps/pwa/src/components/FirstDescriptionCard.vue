<script setup lang="ts">
// 3 + 5 words side by side, then the 8-choose-5 pick matrix (implicit strong feedback).
import { computed, ref } from "vue";
import type { FirstDescriptionCardModel } from "flavor-data/product-vector-v1/view";
import type { Word } from "flavor-data/product-vector-v1/flow";
import { locale, submitPickedWords } from "../store";

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
  <section class="max-w-md w-full space-y-4" data-component="FirstDescriptionCard">
    <h2 v-if="model.profileTitle">{{ model.profileTitle }}</h2>
    <p data-words="main">{{ model.main.map((w) => w.text).join(" | ") }}</p>
    <p data-words="secondary">{{ model.secondary.map((w) => w.text).join(" | ") }}</p>
    <p>{{ model.pickPrompt }}</p>
    <div class="grid grid-cols-2 gap-2" role="group">
      <button
        v-for="word in all"
        :key="word.text"
        type="button"
        class="border px-3 py-2"
        :aria-pressed="chosen.some((w) => w.text === word.text)"
        :data-dimension="word.dimension"
        @click="toggle(word)"
      >
        {{ word.text }}
      </button>
    </div>
    <button type="button" class="border px-6 py-3" :disabled="!full" @click="submitPickedWords(chosen)">{{ submitLabel }} ({{ chosen.length }}/{{ model.pickCount }})</button>
  </section>
</template>

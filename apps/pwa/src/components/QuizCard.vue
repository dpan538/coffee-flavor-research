<script setup lang="ts">
// Upper half: the question. Lower half: the options as equal bands that fill the space. Tap → highlight → fold.
import { ref } from "vue";
import type { QuizCardModel } from "flavor-data/product-vector-v1/view";
import type { Slot } from "flavor-data/product-vector-v1/flow";
import { locale, pick } from "../store";

const props = defineProps<{ model: QuizCardModel }>();
const selected = ref<string | null>(null);

async function choose(option: string, label: string) {
  if (selected.value) return;
  selected.value = option;
  await pick(props.model.slot as Slot, option, label, props.model.prompt);
}
</script>

<template>
  <section class="h-full flex flex-col" data-component="QuizCard" :data-slot="model.slot">
    <div class="basis-1/2 min-h-0 px-6 pt-7 flex flex-col justify-end gap-3">
      <div class="flex items-center justify-between text-xs tracking-widest opacity-70">
        <span>{{ locale === 'zh-CN' ? '这一口' : 'This sip' }}</span>
        <span class="flex gap-1" aria-hidden="true"><span v-for="i in model.progress.expected" :key="i" class="h-1 w-5 rounded-full" :class="i <= model.progress.answered + 1 ? 'bg-current' : 'bg-current opacity-25'" /></span>
      </div>
      <h2 class="text-[34px] rise" :class="locale === 'zh-CN' ? 'display-zh' : 'display'">{{ model.prompt }}</h2>
    </div>
    <ul class="basis-1/2 min-h-0 px-4 pt-5 pb-4 flex flex-col gap-2">
      <li v-for="option in model.options" :key="option.option" class="flex-1 min-h-0 flex rise">
        <button type="button" class="option flex-1 flex items-center" :aria-pressed="selected === option.option" @click="choose(option.option, option.label)">{{ option.label }}</button>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
// One question per card; choosing an option calls the store, which advances the session and refreshes the screen model.
import type { QuizCardModel } from "flavor-data/product-vector-v1/view";
import type { Slot } from "flavor-data/product-vector-v1/flow";
import { pick } from "../store";

defineProps<{ model: QuizCardModel }>();
</script>

<template>
  <section class="max-w-md w-full space-y-4" data-component="QuizCard" :data-slot="model.slot">
    <progress :value="model.progress.answered" :max="model.progress.expected" class="w-full" />
    <h2>{{ model.prompt }}</h2>
    <ul class="space-y-2">
      <li v-for="option in model.options" :key="option.option">
        <button type="button" class="border w-full text-left px-4 py-3" @click="pick(model.slot as Slot, option.option)">{{ option.label }}</button>
      </li>
    </ul>
  </section>
</template>

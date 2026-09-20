<script setup lang="ts">
// Answered cards stack up here (owner: cards "collected" into the top zone), like the recent-files stack reference.
// A question's card is also the way back to it (owner, 2026-09-18) — from the questions, the description or the final
// card: the question reopens with the other answers kept, and whatever changes is recomputed by the engine.
// Each card shows a strip of up to 30 px above the next one (18 px before 2026-09-20: too narrow for a finger).
import { isQuestionKey } from "flavor-data/product-vector-v1/dynamicBank";
import { computed } from "vue";
import { collected, editSlot, locale, stage } from "../store";
import type { CollectedCard } from "../store";

const isQuestion = (card: CollectedCard) => isQuestionKey(card.key);
// While the cup's context is being set, its cards collect here. From the first question on only the question cards
// stay — six at most (owner, 2026-09-20): the stack is how a reader goes back to a question, a finger is not a mouse
// pointer, and eleven strips of ten pixels cannot be tapped. The context stays on the final card; nothing restarts
// from the stack, so its cards have no use here once the questions begin.
const visible = computed(() =>
  stage.value === "context"
    ? collected.value
    : collected.value.filter(isQuestion),
);
function open(card: CollectedCard) {
  if (isQuestion(card)) editSlot(card.key);
}
const label = (card: CollectedCard) =>
  locale.value === "zh-CN" ? `修改：${card.title}` : `Change: ${card.title}`;
</script>

<template>
  <TransitionGroup
    name="stack"
    tag="ul"
    class="relative flex-1 min-h-0 mt-2 overflow-hidden"
    data-component="CollectedStack"
    aria-live="polite"
  >
    <li
      v-for="(card, i) in visible"
      :key="card.key + i"
      class="absolute left-0 right-0 rounded-2xl shadow-stack px-4 py-2 text-ink"
      :class="isQuestion(card) ? 'cursor-pointer' : ''"
      :role="isQuestion(card) ? 'button' : undefined"
      :tabindex="isQuestion(card) ? 0 : undefined"
      :aria-label="isQuestion(card) ? label(card) : undefined"
      :data-slot="isQuestion(card) ? card.key : undefined"
      @click="open(card)"
      @keydown.enter.prevent="open(card)"
      :style="{
        backgroundColor: card.color,
        top: `calc(${i} * min(30px, (100% - 52px) / ${Math.max(visible.length - 1, 1)}))`,
        zIndex: i + 1,
      }"
    >
      <!-- a question keeps its sentence case (owner, 2026-09-19: no English questions in capitals) and one line -->
      <span
        class="block text-[11px] tracking-wide opacity-70 truncate"
        :class="isQuestion(card) ? '' : 'uppercase'"
        >{{ card.title }}</span
      >
      <span class="block text-sm font-medium truncate">{{ card.label }}</span>
    </li>
  </TransitionGroup>
</template>

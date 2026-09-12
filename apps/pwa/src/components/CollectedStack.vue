<script setup lang="ts">
// Answered cards stack up here (owner: cards "collected" into the top zone), like the recent-files stack reference.
import { collected } from "../store";
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
      v-for="(card, i) in collected"
      :key="card.key + i"
      class="absolute left-0 right-0 rounded-2xl shadow-stack px-4 py-2 text-ink"
      :style="{
        backgroundColor: card.color,
        top: `calc(${i} * min(18px, (100% - 52px) / ${Math.max(collected.length - 1, 1)}))`,
        zIndex: i + 1,
      }"
    >
      <span class="text-[11px] uppercase tracking-wide opacity-70">{{
        card.title
      }}</span>
      <span class="block text-sm font-medium truncate">{{ card.label }}</span>
    </li>
  </TransitionGroup>
</template>
